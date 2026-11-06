from datetime import datetime
import pytz

class NotificationPolicy:
    PRIORITY_MAP = {
        "OTP_REQUIRED": "CRITICAL",
        "CAPTCHA_REQUIRED": "CRITICAL",
        "LOGIN_REQUIRED": "CRITICAL",
        "UNKNOWN_QUESTION": "CRITICAL",
        "GMAIL_REAUTH_REQUIRED": "CRITICAL",
        "APPLICATION_BLOCKED": "CRITICAL",
        
        "INTERVIEW_DETECTED": "HIGH",
        "ASSESSMENT_DETECTED": "HIGH",
        "ACTION_REQUIRED": "HIGH",
        "OFFER_DETECTED": "HIGH",
        "APPLICATION_REVIEW_REQUIRED": "HIGH",
        
        "APPLICATION_CONFIRMED": "NORMAL",
        "APPLICATION_STARTED": "NORMAL",
        "JOB_MATCH": "NORMAL",
        "REJECTION_DETECTED": "NORMAL",
        
        "DAILY_SUMMARY": "LOW"
    }

    @staticmethod
    def get_priority(event_type: str) -> str:
        return NotificationPolicy.PRIORITY_MAP.get(event_type, "NORMAL")
        
    @staticmethod
    def should_deliver(notification_type: str, preference) -> bool:
        if not preference:
            return True # Default to delivering
            
        mapping = {
            "JOB_MATCH": preference.job_match_enabled,
            "APPLICATION_STARTED": preference.application_updates_enabled,
            "APPLICATION_REVIEW_REQUIRED": preference.application_updates_enabled,
            "APPLICATION_BLOCKED": preference.application_updates_enabled,
            "APPLICATION_CONFIRMED": preference.application_updates_enabled,
            "INTERVIEW_DETECTED": preference.interview_enabled,
            "ASSESSMENT_DETECTED": preference.assessment_enabled,
            "ACTION_REQUIRED": preference.action_required_enabled,
            "REJECTION_DETECTED": preference.rejection_enabled,
            "OFFER_DETECTED": preference.offer_enabled,
            "OTP_REQUIRED": preference.system_enabled,
            "CAPTCHA_REQUIRED": preference.system_enabled,
            "LOGIN_REQUIRED": preference.system_enabled,
            "UNKNOWN_QUESTION": preference.system_enabled,
            "GMAIL_REAUTH_REQUIRED": preference.system_enabled,
            "SYSTEM_ERROR": preference.system_enabled,
            "DAILY_SUMMARY": preference.daily_summary_enabled
        }
        
        return mapping.get(notification_type, True)
        
    @staticmethod
    def is_in_quiet_hours(preference, current_time=None) -> bool:
        if not preference or not preference.quiet_hours_enabled:
            return False
            
        if current_time is None:
            current_time = datetime.utcnow()
            
        try:
            tz = pytz.timezone(preference.timezone)
            local_time = current_time.replace(tzinfo=pytz.utc).astimezone(tz)
            
            start_h, start_m = map(int, preference.quiet_hours_start.split(':'))
            end_h, end_m = map(int, preference.quiet_hours_end.split(':'))
            
            # Create datetime objects for today's start and end times
            start_time = local_time.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            end_time = local_time.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
            
            if start_time > end_time:
                # Spans midnight (e.g. 22:00 to 07:00)
                return local_time >= start_time or local_time <= end_time
            else:
                # Same day (e.g. 01:00 to 05:00)
                return start_time <= local_time <= end_time
                
        except Exception:
            return False
            
    @staticmethod
    def get_delivery_status(notification_type: str, preference) -> str:
        """Determines if a notification should be SENT or QUEUED based on quiet hours."""
        priority = NotificationPolicy.get_priority(notification_type)
        
        if priority == "CRITICAL":
            return "PENDING"
            
        if NotificationPolicy.is_in_quiet_hours(preference):
            if priority == "NORMAL" or priority == "LOW":
                return "QUEUED"
            # For HIGH priority, user could have a specific setting, but default is to allow
            # We'll allow HIGH by default, only delay NORMAL/LOW
            return "PENDING"
            
        return "PENDING"

