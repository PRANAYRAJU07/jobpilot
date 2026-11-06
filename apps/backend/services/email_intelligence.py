import logging
import re
from sqlalchemy.orm import Session
import models

logger = logging.getLogger("jobpilot.email_intelligence")

class EmailIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    def classify_and_match(self, email_data: dict, connection: models.GmailConnection):
        """
        Takes raw email dict from GmailService and returns a structured classification.
        Finds matching application based on domain and subject.
        """
        sender = email_data.get('sender', '').lower()
        subject = email_data.get('subject', '').lower()
        snippet = email_data.get('snippet', '').lower()
        sender_domain = email_data.get('sender_domain', '').lower()
        
        # 1. Application Matching (Deterministic first)
        # Search for applications where job company domain matches sender_domain
        # This is a naive heuristic; in production, use TruthEngine or embedding search
        matching_app = None
        if sender_domain and sender_domain not in ['gmail.com', 'yahoo.com', 'outlook.com']:
            # Try to match domain
            jobs = self.db.query(models.Job).all()
            for j in jobs:
                if j.company and j.company.lower().replace(" ", "") in sender_domain:
                    # found a matching job, find the application
                    matching_app = self.db.query(models.Application).filter_by(job_id=j.id).first()
                    break
                    
        # 2. Classification Pipeline (Deterministic heuristics -> LLM fallback)
        classification = "UNKNOWN"
        confidence = 0.0
        
        # Heuristics
        if re.search(r'thank you for applying|application received|we have received your application', subject + snippet):
            classification = "APPLICATION_CONFIRMATION"
            confidence = 0.95
        elif re.search(r'interview|schedule|meeting|time to speak', subject) and 'invitation' in subject + snippet:
            # We don't want false positives like "Interview tips" newsletter
            if 'unsubscribe' not in snippet:
                classification = "INTERVIEW"
                confidence = 0.90
        elif re.search(r'assessment|hackerrank|codility|online test', subject + snippet):
            classification = "ASSESSMENT"
            confidence = 0.85
        elif re.search(r'not selected|mov\w* forward with other|filled the position', subject + snippet):
            classification = "REJECTION"
            confidence = 0.92
        elif re.search(r'offer|congratulations', subject) and 'offer' in snippet:
            classification = "OFFER"
            confidence = 0.80
        elif re.search(r'action required|please complete|next steps', subject):
            classification = "ACTION_REQUIRED"
            confidence = 0.75
            
        # 3. Create records based on classification
        email = models.Email(
            gmail_connection_id=connection.id,
            provider_message_id=email_data['id'],
            thread_id=email_data['thread_id'],
            sender=email_data['sender'],
            sender_domain=email_data['sender_domain'],
            subject=email_data['subject'],
            received_at=email_data['received_at'],
            snippet=email_data['snippet'],
            classification=classification,
            classification_confidence=confidence,
            application_id=matching_app.id if matching_app else None,
            job_id=matching_app.job_id if matching_app else None
        )
        self.db.add(email)
        self.db.flush()
        
        # 4. Status Precedence Updates
        if matching_app:
            if classification == "APPLICATION_CONFIRMATION":
                # Only update to CONFIRMED if it's currently lower precedence
                if matching_app.status in ['READY_TO_SUBMIT', 'APPLICATION_STARTED', 'SUBMITTING', 'SUBMISSION_VERIFY']:
                    matching_app.status = "CONFIRMED"
                    self.db.add(models.ApplicationEvent(
                        application_id=matching_app.id,
                        new_state="CONFIRMED",
                        reason="Source: gmail"
                    ))
            elif classification == "REJECTION":
                matching_app.status = "REJECTED"
                self.db.add(models.ApplicationEvent(
                    application_id=matching_app.id,
                    new_state="REJECTED",
                    reason="Source: gmail"
                ))
                
        # 5. Extract specific entities
        if classification == "INTERVIEW" and matching_app:
            interview = models.Interview(
                application_id=matching_app.id,
                email_id=email.id,
                title="Interview with " + email_data['sender_domain'],
                status="DETECTED"
            )
            self.db.add(interview)
            
        if classification == "ASSESSMENT" and matching_app:
            assessment = models.Assessment(
                application_id=matching_app.id,
                email_id=email.id,
                platform="Unknown",
                status="DETECTED"
            )
            self.db.add(assessment)
            
        self.db.commit()
        return email
