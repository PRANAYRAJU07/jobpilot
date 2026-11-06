import logging
from playwright.sync_api import Page
from urllib.parse import urlparse

logger = logging.getLogger("jobpilot.navigation")

class NavigationManager:
    def __init__(self, page: Page):
        self.page = page

    def goto_safe(self, url: str, allowed_domains: list = None) -> bool:
        """
        Navigates to URL and ensures it doesn't redirect maliciously.
        Returns True if successful, False if blocked.
        """
        parsed_target = urlparse(url)
        if allowed_domains and parsed_target.netloc not in allowed_domains:
            logger.error(f"UNEXPECTED_DOMAIN: {parsed_target.netloc} not in allowed domains {allowed_domains}")
            return False

        logger.info(f"Navigating to {url}")
        try:
            response = self.page.goto(url)
            if not response:
                logger.warning("No response received during navigation.")
                return False
                
            final_url = self.page.url
            parsed_final = urlparse(final_url)
            
            if allowed_domains and parsed_final.netloc not in allowed_domains:
                logger.error(f"UNEXPECTED_DOMAIN_REDIRECT: Ended up on {parsed_final.netloc}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
