import logging
from playwright.sync_api import sync_playwright, Browser, Playwright

logger = logging.getLogger("jobpilot.browser")

class BrowserManager:
    def __init__(self):
        self.playwright: Playwright = None
        self.browser: Browser = None

    def start(self):
        logger.info("Starting Playwright Chromium...")
        self.playwright = sync_playwright().start()
        # Secure minimal launch
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-gpu"
            ]
        )
        return self.browser

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Browser stopped.")
