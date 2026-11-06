import logging
from playwright.sync_api import Page
import os

logger = logging.getLogger("jobpilot.screenshots")

class ScreenshotManager:
    def __init__(self, page: Page, application_id: str):
        self.page = page
        self.application_id = application_id
        # In production this would upload to S3 directly or via backend
        self.storage_dir = f"/app/storage/screenshots/{application_id}"
        os.makedirs(self.storage_dir, exist_ok=True)

    def capture(self, event_name: str) -> str:
        """
        Takes a screenshot and returns the file path.
        """
        file_path = os.path.join(self.storage_dir, f"{event_name}.png")
        logger.info(f"Taking screenshot: {file_path}")
        try:
            self.page.screenshot(path=file_path, full_page=True)
            return file_path
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
