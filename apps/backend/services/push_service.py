import json
from pywebpush import webpush, WebPushException
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("jobpilot.push_service")

class NotificationChannel:
    def send(self, notification, subscription) -> bool:
        raise NotImplementedError

class WebPushChannel(NotificationChannel):
    def __init__(self):
        # Allow missing for tests, but warn
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")
        
        # If missing, we might use a mock mode
        self.claims = {
            "sub": "mailto:admin@jobpilot.ai"
        }

    def send(self, notification_data: Dict[str, Any], subscription_info: Dict[str, Any]) -> str:
        """
        Returns "SUCCESS", "INVALID_SUBSCRIPTION", "TRANSIENT_FAILURE"
        """
        if not self.vapid_private_key:
            logger.warning("VAPID keys not configured, cannot send real web push")
            return "TRANSIENT_FAILURE"
            
        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.claims
            )
            return "SUCCESS"
        except WebPushException as ex:
            if ex.response and ex.response.status_code in [404, 410]:
                logger.info(f"Subscription invalid or expired (status {ex.response.status_code})")
                return "INVALID_SUBSCRIPTION"
            else:
                logger.error(f"WebPush error: {repr(ex)}")
                return "TRANSIENT_FAILURE"
        except Exception as e:
            logger.error(f"Unexpected WebPush error: {str(e)}")
            return "TRANSIENT_FAILURE"

class MockPushProvider(NotificationChannel):
    """Deterministic mock provider for tests."""
    def __init__(self):
        self.records = []
        # Allows tests to control the simulated result
        self.next_result = "SUCCESS"
        
    def send(self, notification_data: Dict[str, Any], subscription_info: Dict[str, Any]) -> str:
        self.records.append({
            "notification_data": notification_data,
            "subscription_info": subscription_info
        })
        return self.next_result

# Global instance
push_channel = WebPushChannel()
if os.getenv("TESTING") == "true":
    push_channel = MockPushProvider()
