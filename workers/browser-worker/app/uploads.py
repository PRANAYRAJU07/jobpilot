import logging
from playwright.sync_api import Page

logger = logging.getLogger("jobpilot.uploads")

class UploadManager:
    def __init__(self, page: Page):
        self.page = page

    def upload_resume(self, file_path: str):
        """
        Uploads resume to the file input on the page.
        """
        logger.info(f"Uploading resume from {file_path}")
        try:
            # Look for common file input patterns
            file_input = self.page.locator("input[type='file']").first
            if file_input:
                file_input.set_input_files(file_path)
                logger.info("RESUME_UPLOADED")
                return True
            else:
                logger.warning("No file input found for resume upload.")
                return False
        except Exception as e:
            logger.error(f"Failed to upload resume: {e}")
            return False
            
    def upload_cover_letter(self, file_path: str):
        logger.info(f"Uploading cover letter from {file_path}")
        try:
            # Example heuristic: if there are multiple file inputs, assume the second one is cover letter
            # A real implementation would parse labels
            file_inputs = self.page.locator("input[type='file']").all()
            if len(file_inputs) > 1:
                file_inputs[1].set_input_files(file_path)
                logger.info("COVER_LETTER_UPLOADED")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to upload cover letter: {e}")
            return False
