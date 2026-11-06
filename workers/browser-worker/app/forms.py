import logging
from playwright.sync_api import Page

logger = logging.getLogger("jobpilot.forms")

class FormFieldDetector:
    def __init__(self, page: Page):
        self.page = page
        
    def detect_and_fill(self, candidate_data: dict):
        """
        Detects fields on the page based on semantic labels/attributes,
        and fills them if a deterministic mapping exists.
        Returns a list of unknown questions.
        """
        logger.info("Detecting and filling form fields...")
        unknown_questions = []
        
        # In a full implementation, we'd iterate over all inputs, selects, and textareas.
        # This is a stub showing the semantic detection approach required by the user.
        
        inputs = self.page.locator("input:visible, select:visible, textarea:visible").all()
        for i, el in enumerate(inputs):
            # Attempt to gather semantic context
            name_attr = el.get_attribute("name") or ""
            id_attr = el.get_attribute("id") or ""
            type_attr = el.get_attribute("type") or ""
            
            # Simple heuristic matching
            if "email" in name_attr.lower() or "email" in id_attr.lower():
                el.fill(candidate_data.get("email", ""))
                logger.info("FIELD_FILLED field=email")
            elif "phone" in name_attr.lower() or "phone" in id_attr.lower():
                el.fill(candidate_data.get("phone", ""))
                logger.info("FIELD_FILLED field=phone")
            elif "first" in name_attr.lower() and "name" in name_attr.lower():
                el.fill(candidate_data.get("first_name", ""))
                logger.info("FIELD_FILLED field=first_name")
            elif "last" in name_attr.lower() and "name" in name_attr.lower():
                el.fill(candidate_data.get("last_name", ""))
                logger.info("FIELD_FILLED field=last_name")
            elif type_attr not in ["submit", "button", "hidden", "file"]:
                # Unknown field
                unknown_questions.append({
                    "id": id_attr,
                    "name": name_attr,
                    "type": type_attr
                })
                
        return unknown_questions
