from sqlalchemy.orm import Session
import models
import logging

logger = logging.getLogger("jobpilot.truth_engine")

VALID_VERIFIED_STATUSES = ("SUPPORTED", "ALLOW", "VERIFIED")

class TruthEngine:
    """
    Validates claims and required skills against the Candidate Knowledge Base (Evidence Graph).
    """
    def __init__(self, db: Session, profile_id: str):
        self.db = db
        self.profile_id = profile_id

    def verify_claim(self, claim_text: str, skill_name: str = None) -> bool:
        """
        Verify if a claim or skill is backed by verified evidence (SUPPORTED or ALLOW).
        """
        if skill_name:
            skill = self.db.query(models.CandidateSkill).filter(
                models.CandidateSkill.profile_id == self.profile_id,
                models.CandidateSkill.name.ilike(skill_name)
            ).first()

            if not skill:
                logger.warning(f"Skill '{skill_name}' not found in profile.")
                return False

            evidence = self.db.query(models.CandidateClaim).filter(
                models.CandidateClaim.profile_id == self.profile_id,
                models.CandidateClaim.skill_id == skill.id,
                models.CandidateClaim.verification_status.in_(VALID_VERIFIED_STATUSES)
            ).first()

            if evidence:
                return True
            else:
                logger.warning(f"No verified evidence found for skill '{skill_name}'.")
                return False

        return False
