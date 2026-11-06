import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import models
from encryption import decrypt_token
import logging
from sqlalchemy.orm import Session
import dateutil.parser

logger = logging.getLogger("jobpilot.gmail_service")

class GmailService:
    def __init__(self, db: Session, connection: models.GmailConnection):
        self.db = db
        self.connection = connection
        self.service = self._build_service()

    def _build_service(self):
        access_token = decrypt_token(self.connection.encrypted_access_token)
        refresh_token = decrypt_token(self.connection.encrypted_refresh_token)
        client_id = os.getenv("GMAIL_CLIENT_ID", "mock_client_id")
        client_secret = os.getenv("GMAIL_CLIENT_SECRET", "mock_client_secret")

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.readonly"]
        )
        return build('gmail', 'v1', credentials=credentials, cache_discovery=False)

    def fetch_new_messages(self, limit=50):
        """Fetch message metadata incrementally, using historyId."""
        try:
            detailed_messages = []
            new_history_id = None

            if self.connection.last_history_id:
                try:
                    results = self.service.users().history().list(
                        userId='me',
                        startHistoryId=self.connection.last_history_id,
                        historyTypes=['messageAdded']
                    ).execute()

                    histories = results.get('history', [])
                    new_history_id = results.get('historyId')

                    messages = []
                    for hist in histories:
                        if 'messagesAdded' in hist:
                            for msg_added in hist['messagesAdded']:
                                messages.append(msg_added['message'])

                except Exception as e:
                    if "404" in str(e) or "historyId" in str(e):
                        logger.warning("History ID expired, falling back to full list sync")
                        self.connection.last_history_id = None
                        return self.fetch_new_messages(limit)
                    raise e
            else:
                results = self.service.users().messages().list(userId='me', maxResults=limit).execute()
                messages = results.get('messages', [])

                profile = self.service.users().getProfile(userId='me').execute()
                new_history_id = str(profile.get('historyId'))

            for msg in messages:
                msg_id = msg['id']
                existing = self.db.query(models.Email).filter_by(provider_message_id=msg_id).first()
                if existing:
                    continue

                msg_detail = self.service.users().messages().get(
                    userId='me', id=msg_id, format='metadata',
                    metadataHeaders=['From', 'To', 'Subject', 'Date']
                ).execute()

                headers = msg_detail.get('payload', {}).get('headers', [])
                header_dict = {h['name']: h['value'] for h in headers}

                received_at_str = header_dict.get('Date')
                if received_at_str:
                    try:
                        received_at = dateutil.parser.parse(received_at_str).replace(tzinfo=None)
                    except Exception:
                        from datetime import datetime
                        received_at = datetime.utcnow()
                else:
                    from datetime import datetime
                    received_at = datetime.utcnow()

                sender = header_dict.get('From', '')
                sender_domain = sender.split('@')[-1].strip('>') if '@' in sender else ''

                detailed_messages.append({
                    "id": msg_id,
                    "thread_id": msg_detail.get('threadId'),
                    "snippet": msg_detail.get('snippet', ''),
                    "sender": sender,
                    "sender_domain": sender_domain,
                    "subject": header_dict.get('Subject', ''),
                    "received_at": received_at
                })

            return detailed_messages, new_history_id

        except Exception as e:
            logger.error(f"Error fetching Gmail: {e}")
            if "invalid_grant" in str(e).lower() or "reauth" in str(e).lower():
                self.connection.status = "REAUTH_REQUIRED"
                self.db.commit()
            return [], None
