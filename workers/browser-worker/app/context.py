import logging
from playwright.sync_api import Browser, BrowserContext

logger = logging.getLogger("jobpilot.context")

class ContextManager:
    def __init__(self, browser: Browser):
        self.browser = browser

    def create_isolated_context(self, application_id: str) -> BrowserContext:
        logger.info(f"Creating isolated context for application {application_id}")
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.set_default_timeout(10000) # 10 seconds action timeout
        context.set_default_navigation_timeout(30000) # 30 seconds navigation
        return context
