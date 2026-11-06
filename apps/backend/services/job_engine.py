import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from sqlalchemy.orm import Session
import models
from services import india_classifier as _india_classifier
from services.document_intelligence import SKILL_TAXONOMY, CATEGORY_TO_DOMAIN
from services.alert_dispatcher import AlertDispatcherService

logger = logging.getLogger("jobpilot.job_engine")

# Flatten all curated skills from SKILL_TAXONOMY for comprehensive JD extraction
ALL_KNOWN_SKILLS: List[str] = []
SKILL_TO_CATEGORY: Dict[str, str] = {}
for _cat, _skills in SKILL_TAXONOMY.items():
    for _sk in _skills:
        if _sk not in ALL_KNOWN_SKILLS:
            ALL_KNOWN_SKILLS.append(_sk)
        SKILL_TO_CATEGORY[_sk.lower()] = _cat

# Trusted ATS & Career Platform domains for genuineness verification
TRUSTED_JOB_DOMAINS = [
    "greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com",
    "smartrecruiters.com", "linkedin.com", "internshala.com", "naukri.com",
    "workable.com", "bamboohr.com", "icims.com", "jobvite.com", "rippling.com",
    "wellfound.com", "unstop.com", "google.com", "microsoft.com", "amazon.jobs"
]

# Scam / Fee / Fraudulent Job Indicators
SCAM_INDICATORS = [
    r"registration\s+fee", r"security\s+deposit", r"training\s+fee",
    r"pay\s+(?:rs|inr|\$)\s*\d+\s*to\s+apply", r"100%\s+placement\s+fee",
    r"earn\s+\$?\d+\s+per\s+day\s+from\s+home\s+no\s+skills",
    r"whatsapp\s+only\s+no\s+interview", r"copy\s+paste\s+typing\s+job",
    r"telegram\s+task\s+investment", r"pay\s+for\s+offer\s+letter"
]

# Non-technical / Out-of-domain role title patterns to prevent false matches (e.g. Account Executive)
NON_TECH_TITLE_PATTERNS = [
    r"\baccount\s+executive\b", r"\bsales\s+(?:representative|manager|director|development|associate)\b",
    r"\b(?:hr|human\s+resources|talent\s+acquisition|recruiter|recruiting)\b",
    r"\blegal\s+counsel\b", r"\bparalegal\b", r"\bcorporate\s+counsel\b",
    r"\bmarketing\s+(?:manager|specialist|director|coordinator)\b",
    r"\bcustomer\s+(?:success|support|service)\s+(?:representative|associate|manager)\b",
    r"\b(?:payroll|accounting|bookkeeper|tax\s+analyst|audit)\b",
    r"\boffice\s+manager\b", r"\bexecutive\s+assistant\b", r"\breceptionist\b",
    r"\bpublic\s+relations\b", r"\bcopywriter\b", r"\bsocial\s+media\s+manager\b"
]

# Domain classification keywords in Job Title
TITLE_DOMAIN_KEYWORDS = {
    "AI_ML": [
        "ai", "ml", "machine learning", "deep learning", "artificial intelligence",
        "llm", "nlp", "computer vision", "gen ai", "generative ai", "applied scientist",
        "research intern", "research scientist", "neural", "agentic"
    ],
    "DATA_SCIENCE": [
        "data scientist", "data science", "data analyst", "analytics", "business intelligence",
        "data engineer", "big data", "decision scientist", "quantitative"
    ],
    "BACKEND_ENGINEERING": [
        "backend", "back-end", "api engineer", "distributed systems", "platform engineer",
        "python developer", "java developer", "golang", "microservices"
    ],
    "FULL_STACK": [
        "full stack", "fullstack", "full-stack", "frontend", "front-end", "web developer",
        "react", "next.js", "ui engineer"
    ],
    "DEVOPS_CLOUD": [
        "devops", "sre", "site reliability", "cloud engineer", "mlops", "infrastructure",
        "kubernetes", "platform ops", "security engineer"
    ],
    "SOFTWARE_ENGINEERING": [
        "software engineer", "software developer", "sde", "swe", "graduate engineer",
        "programmer", "member of technical staff", "mts", "engineering intern",
        "technical intern", "developer intern"
    ],
}


class JobEngineService:
    def __init__(self, db: Session):
        self.db = db
        self.known_skills = ALL_KNOWN_SKILLS

    def extract_skills_from_text(self, text: str) -> List[str]:
        if not text:
            return []
        extracted = []
        text_lower = text.lower()
        for skill in self.known_skills:
            s_low = skill.lower()
            if s_low in ("c", "r"):
                pattern = r"(?:^|[\s,;:/|()])" + re.escape(s_low) + r"(?:$|[\s,;:/|()])"
                if re.search(pattern, text_lower):
                    extracted.append(skill)
            elif s_low in ("c++", "c#", "node.js", "next.js", "vue.js", "express.js"):
                if s_low in text_lower:
                    extracted.append(skill)
            else:
                pattern = r"\b" + re.escape(s_low) + r"\b"
                if re.search(pattern, text_lower):
                    extracted.append(skill)
        return list(dict.fromkeys(extracted))

    def verify_genuineness(self, job: models.Job) -> Dict[str, Any]:
        """
        Verifies whether a discovered job is genuine and safe to apply to.
        Checks URL validity, trusted ATS/career hostnames, company/title completeness,
        and scans for scam/registration-fee patterns.
        """
        score = 100
        reasons = []
        title = (job.title or "").strip()
        company = (job.company or "").strip()
        desc = (job.description or "").strip()
        url = (job.apply_url or job.url or "").strip()

        if not title or len(title) < 3 or title == "***":
            score -= 60
            reasons.append("Missing or obfuscated job title")

        if not company or len(company) < 2 or company.lower() in ("unknown", "confidential", "n/a"):
            score -= 35
            reasons.append("Unverified or anonymous employer name")

        if not url or not url.startswith(("http://", "https://")):
            score -= 50
            reasons.append("Missing valid application URL")
        else:
            host = (urlparse(url).netloc or "").lower()
            if any(short in host for short in ["bit.ly", "tinyurl.com", "t.co", "rb.gy", "cutt.ly"]):
                score -= 50
                reasons.append("Suspicious shortened redirect link")
            elif any(td in host for td in TRUSTED_JOB_DOMAINS):
                reasons.append(f"Verified ATS/platform host ({host})")
            else:
                reasons.append(f"Direct company career domain ({host})")

        combined_text = f"{title} {company} {desc}".lower()
        for pattern in SCAM_INDICATORS:
            if re.search(pattern, combined_text):
                score -= 80
                reasons.append(f"Flagged scam/fee pattern: {pattern}")

        score = max(0, min(100, score))
        return {
            "is_genuine": score >= 60,
            "genuineness_score": score,
            "reasons": reasons,
        }

    def classify_job_domain(self, job: models.Job, extracted_skills: List[str]) -> Dict[str, Any]:
        """
        Determines the primary domain of the job and whether it is a technical role
        suitable for an engineering/AI/data candidate.
        """
        title_lower = (job.title or "").lower()

        # Check explicit non-technical roles first (unless title explicitly says Engineer/Developer/Scientist)
        is_explicit_tech_title = any(
            t in title_lower for t in [
                "engineer", "developer", "scientist", "architect", "programmer",
                "sde", "swe", "ml ", "ai ", "data ", "devops", "security", "technical staff"
            ]
        )
        if not is_explicit_tech_title:
            for pat in NON_TECH_TITLE_PATTERNS:
                if re.search(pat, title_lower):
                    return {
                        "domain_category": "NON_TECH_OTHER",
                        "is_technical": False,
                        "reason": f"Non-technical role title ({job.title})"
                    }

        # Match title keywords first
        for domain, keywords in TITLE_DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw in title_lower:
                    return {
                        "domain_category": domain,
                        "is_technical": True,
                        "reason": f"Title matched {domain} keyword '{kw}'"
                    }

        # Fallback: infer from extracted skills
        domain_votes: Dict[str, int] = {}
        for sk in extracted_skills:
            cat = SKILL_TO_CATEGORY.get(sk.lower())
            if cat:
                dom = CATEGORY_TO_DOMAIN.get(cat, "SOFTWARE_ENGINEERING")
                domain_votes[dom] = domain_votes.get(dom, 0) + 1

        if domain_votes:
            best_domain = max(domain_votes.items(), key=lambda x: x[1])[0]
            return {
                "domain_category": best_domain,
                "is_technical": True,
                "reason": f"Inferred {best_domain} from {len(extracted_skills)} technical skills"
            }

        return {
            "domain_category": "NON_TECH_OTHER",
            "is_technical": False,
            "reason": "No technical keywords or engineering skills detected"
        }

    def is_domain_suitable_for_profile(self, job_domain: str, is_technical: bool, profile: models.CandidateProfile) -> bool:
        if not is_technical or job_domain == "NON_TECH_OTHER":
            return False

        candidate_domains = profile.domain_focus or ["AI_ML", "DATA_SCIENCE", "BACKEND_ENGINEERING", "SOFTWARE_ENGINEERING", "FULL_STACK"]
        if isinstance(candidate_domains, list) and candidate_domains:
            # SOFTWARE_ENGINEERING is compatible with all technical CS/AI profiles
            allowed = set(candidate_domains) | {"SOFTWARE_ENGINEERING"}
            if "AI_ML" in allowed:
                allowed.add("DATA_SCIENCE")
            if "BACKEND_ENGINEERING" in allowed:
                allowed.add("FULL_STACK")
            return job_domain in allowed

        return True

    def compute_freshness(self, job: models.Job, max_age_hours: int = 72) -> bool:
        ref_time = job.posted_at or job.created_at
        if not ref_time:
            return True
        naive_ref = ref_time.replace(tzinfo=None) if ref_time.tzinfo else ref_time
        age_hours = (datetime.utcnow() - naive_ref).total_seconds() / 3600.0
        return age_hours <= max_age_hours

    def analyze_jd(self, job: models.Job) -> dict:
        """
        Parses raw job description to extract structured requirements, domain, and genuineness.
        """
        full_text = (job.title or "") + "\n" + (job.description or "")
        extracted_skills = self.extract_skills_from_text(full_text)
        is_intern = _india_classifier.is_internship(job.title) or ("intern" in (job.employment_type or "").lower())
        domain_info = self.classify_job_domain(job, extracted_skills)
        genuineness_info = self.verify_genuineness(job)

        return {
            "required_skills": extracted_skills,
            "education": "B.Tech" if "b.tech" in full_text.lower() or "bachelor" in full_text.lower() else None,
            "is_internship": is_intern,
            "domain_category": domain_info["domain_category"],
            "is_technical": domain_info["is_technical"],
            "domain_reason": domain_info["reason"],
            "is_genuine": genuineness_info["is_genuine"],
            "genuineness_score": genuineness_info["genuineness_score"],
            "genuineness_reasons": genuineness_info["reasons"],
        }

    def check_eligibility(self, job_requirements: dict, profile: models.CandidateProfile, job: models.Job = None) -> str:
        """
        Determines eligibility based on genuineness, domain suitability, and graduation year/experience.
        """
        if not job_requirements.get("is_genuine", True):
            return "REJECTED_UNVERIFIED_SOURCE"

        if not self.is_domain_suitable_for_profile(
            job_requirements.get("domain_category", "SOFTWARE_ENGINEERING"),
            job_requirements.get("is_technical", True),
            profile,
        ):
            return "NOT_SUITABLE_DOMAIN"

        if job and job.role_level in ("STAFF", "MANAGER"):
            # If candidate is a student/fresher (grad year >= current year - 1), skip Staff/Manager roles
            if profile.graduation_year and profile.graduation_year >= 2025:
                return "NOT_ELIGIBLE_SENIORITY"

        return "ELIGIBLE"

    def calculate_match(self, job_requirements: dict, profile: models.CandidateProfile, job: models.Job = None) -> dict:
        """
        Cross-validates extracted job requirements against the candidate's learned skills
        and verified Evidence Graph (CandidateClaim + CandidateSkill).
        """
        required_skills = job_requirements.get("required_skills", [])

        # 1. Build verified evidence map from CandidateClaim (accepting SUPPORTED, ALLOW, VERIFIED)
        claims = self.db.query(models.CandidateClaim).filter_by(profile_id=profile.id).all()
        verified_skills_map: Dict[str, List[str]] = {}
        for c in claims:
            if c.verification_status in ("SUPPORTED", "ALLOW", "VERIFIED") and c.skill:
                evidence_list = []
                if c.project_evidence:
                    evidence_list.append(f"Project: {c.project_evidence.title}")
                if c.document_evidence:
                    evidence_list.append(f"Resume: {c.document_evidence.filename}")
                if not evidence_list:
                    evidence_list.append("Verified Profile Claim")
                verified_skills_map[c.skill.name.lower()] = evidence_list

        # 2. Also include any CandidateSkill directly registered on the profile
        all_profile_skills = self.db.query(models.CandidateSkill).filter_by(profile_id=profile.id).all()
        for sk in all_profile_skills:
            if sk.name.lower() not in verified_skills_map:
                verified_skills_map[sk.name.lower()] = ["Profile Skill"]

        matched = []
        missing = []
        matched_reqs_structured = []

        for req in required_skills:
            if req.lower() in verified_skills_map:
                matched.append(req)
                matched_reqs_structured.append({
                    "skill": req,
                    "evidence": verified_skills_map[req.lower()]
                })
            else:
                missing.append(req)

        # Compute cross-validation score
        if required_skills:
            skill_ratio = len(matched) / len(required_skills)
            relevance_score = int(round(skill_ratio * 100))
        else:
            # If the JD had no explicit skill keywords from our list, score conservatively based on domain title fit
            relevance_score = 65 if job_requirements.get("is_technical") else 0

        min_threshold = profile.min_match_score if profile.min_match_score is not None else 60
        is_genuine = job_requirements.get("is_genuine", True)
        domain_cat = job_requirements.get("domain_category", "SOFTWARE_ENGINEERING")
        domain_suitable = self.is_domain_suitable_for_profile(
            domain_cat,
            job_requirements.get("is_technical", True),
            profile
        )

        cross_validation_passed = bool(
            is_genuine
            and domain_suitable
            and relevance_score >= min_threshold
            and (len(matched) >= 1 or not required_skills)
        )

        return {
            "relevance_score": relevance_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "matched_requirements": matched_reqs_structured,
            "missing_requirements": missing,
            "domain_category": domain_cat,
            "domain_suitable": domain_suitable,
            "is_genuine": is_genuine,
            "genuineness_score": job_requirements.get("genuineness_score", 100),
            "genuineness_reasons": job_requirements.get("genuineness_reasons", []),
            "cross_validation_passed": cross_validation_passed,
        }

    def process_new_job(
        self,
        job_id: str,
        send_alerts: bool = True,
        candidate_profile: Optional[models.CandidateProfile] = None,
        auto_commit: bool = True
    ) -> Optional[Dict[str, Any]]:
        job = self.db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            return None

        # 0. Location, role level, internship, graduation eligibility, and freshness
        loc_info = _india_classifier.classify_location(job.location)
        job.country = loc_info["country"]
        job.region = loc_info["region"]
        job.role_level = _india_classifier.classify_role_level(job.title, job.description)
        job.is_internship = _india_classifier.is_internship(job.title) or ("intern" in (job.employment_type or "").lower())
        job.eligibility_status = _india_classifier.check_graduation_eligibility(job.description)
        job.apply_url = job.apply_url or job.url

        # 1. Analyze JD (skills, domain, genuineness)
        requirements = self.analyze_jd(job)
        job.domain_category = requirements["domain_category"]
        job.is_genuine = requirements["is_genuine"]
        job.genuineness_score = requirements["genuineness_score"]

        # 2. Match against candidate profile
        profile = candidate_profile or self.db.query(models.CandidateProfile).first()
        if not profile:
            logger.warning("No candidate profile found for matching.")
            job.status = "ANALYZED_NO_PROFILE"
            if auto_commit:
                self.db.commit()
            return {"status": "ANALYZED_NO_PROFILE", "alert_dispatched": False}

        max_age = profile.max_job_age_hours or 72
        job.is_fresh = self.compute_freshness(job, max_age_hours=max_age)

        # 3. Check Eligibility (Genuineness + Domain Suitability + Seniority)
        eligibility = self.check_eligibility(requirements, profile, job=job)
        match_data = self.calculate_match(requirements, profile, job=job)

        new_raw_jd = dict(job.raw_jd) if isinstance(job.raw_jd, dict) else {}
        new_raw_jd["match_analysis"] = match_data
        new_raw_jd["eligibility_status"] = eligibility
        job.raw_jd = new_raw_jd

        alert_dispatched = False
        alert_result = None

        if eligibility == "ELIGIBLE":
            job.status = "MATCHED"
            # Check if cross-validation passed and job is fresh enough for alert
            fresh_ok = job.is_fresh if (profile.fresh_jobs_only if profile.fresh_jobs_only is not None else True) else True
            if send_alerts and match_data.get("cross_validation_passed") and fresh_ok:
                dispatcher = AlertDispatcherService(self.db)
                alert_result = dispatcher.dispatch_job_match_alert(job, profile, match_data)
                alert_dispatched = bool(alert_result and alert_result.get("sent"))
        else:
            job.status = eligibility

        if auto_commit:
            self.db.commit()
        return {
            "status": job.status,
            "relevance_score": match_data.get("relevance_score"),
            "cross_validation_passed": match_data.get("cross_validation_passed"),
            "alert_dispatched": alert_dispatched,
            "alert_result": alert_result,
        }

    def re_evaluate_all_jobs_for_profile(
        self,
        profile: models.CandidateProfile,
        send_alerts_for_top: int = 10,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Re-runs cross-validation across discovered jobs in the database after a resume upload
        or skill update, and dispatches alerts for the top freshly matched jobs.
        """
        query = self.db.query(models.Job).order_by(models.Job.posted_at.desc().nullslast(), models.Job.created_at.desc())
        if limit:
            jobs = query.limit(limit).all()
        else:
            jobs = query.all()

        matched_count = 0
        passed_cross_validation = 0
        rejected_domain_or_scam = 0
        alerts_sent = 0

        for idx, job in enumerate(jobs):
            allow_alert = alerts_sent < send_alerts_for_top
            res = self.process_new_job(
                str(job.id),
                send_alerts=allow_alert,
                candidate_profile=profile,
                auto_commit=False
            )
            if not res:
                continue
            if res.get("status") == "MATCHED":
                matched_count += 1
                if res.get("cross_validation_passed"):
                    passed_cross_validation += 1
            else:
                rejected_domain_or_scam += 1

            if res.get("alert_dispatched"):
                alerts_sent += 1

            if idx > 0 and idx % 50 == 0:
                self.db.commit()

        self.db.commit()
        return {
            "total_jobs_evaluated": len(jobs),
            "domain_eligible_jobs": matched_count,
            "cross_validation_passed_jobs": passed_cross_validation,
            "filtered_out_jobs": rejected_domain_or_scam,
            "alerts_dispatched": alerts_sent,
        }
