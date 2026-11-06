import logging
from playwright.sync_api import Page
import re

logger = logging.getLogger("jobpilot.detection")

class BlockerDetector:
    def __init__(self, page: Page):
        self.page = page

    def detect_blockers(self) -> str:
        """
        Detects if the page is blocked by CAPTCHA, OTP, or Login requirements.
        Returns the blocker type or None.
        """
        content = self.page.content().lower()
        
        # 1. CAPTCHA
        if self._detect_captcha(content):
            return "CAPTCHA_REQUIRED"
            
        # 2. OTP
        if self._detect_otp(content):
            return "OTP_REQUIRED"
            
        # 3. LOGIN
        if self._detect_login(content):
            return "LOGIN_REQUIRED"
            
        if self._detect_sensitive(content):
            return "REVIEW_REQUIRED_SENSITIVE"
            
        if self._detect_legal(content):
            return "REVIEW_REQUIRED_LEGAL"
            
        return None

    def _detect_captcha(self, content: str) -> bool:
        indicators = [
            "g-recaptcha", "h-captcha", "cloudflare challenge", 
            "verify you are human", "robot verification", 
            "px-captcha"
        ]
        return any(ind in content for ind in indicators)
        
    def _detect_otp(self, content: str) -> bool:
        indicators = [
            "verification code", "one-time password", "sms code", 
            "email verification code", "enter the code sent to"
        ]
        return any(ind in content for ind in indicators)
        
    def _detect_login(self, content: str) -> bool:
        if "sign in to continue" in content or "log in to apply" in content:
            return True
        return False
        
    def _detect_sensitive(self, content: str) -> bool:
        # Avoid naive keyword matching. Look for explicit question labels/headers
        patterns = [
            r"(?i)<label[^>]*>.*?race.*?<\/label>",
            r"(?i)<label[^>]*>.*?ethnicity.*?<\/label>",
            r"(?i)<label[^>]*>.*?veteran status.*?<\/label>",
            r"(?i)<label[^>]*>.*?disability.*?<\/label>",
            r"(?i)<legend[^>]*>.*?voluntary self-identification.*?<\/legend>",
            r"(?i)<h[1-6][^>]*>.*?equal employment opportunity.*?<\/h[1-6]>"
        ]
        return any(re.search(p, content) for p in patterns)
        
    def _detect_legal(self, content: str) -> bool:
        # Look for explicit legal/sponsorship question labels
        patterns = [
            r"(?i)<label[^>]*>.*?legally authorized to work.*?<\/label>",
            r"(?i)<label[^>]*>.*?require.*visa sponsorship.*?<\/label>",
            r"(?i)<label[^>]*>.*?criminal history.*?<\/label>"
        ]
        return any(re.search(p, content) for p in patterns)
