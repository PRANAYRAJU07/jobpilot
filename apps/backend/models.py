import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    google_tokens = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("CandidateProfile", back_populates="user", uselist=False)

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    github = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    education = Column(String, nullable=True)
    cgpa = Column(Float, nullable=True)
    graduation_year = Column(Integer, nullable=True)
    # Location, domain, and alert preference columns
    location = Column(String, nullable=True)
    preferred_locations = Column(JSONB, nullable=True)
    preferred_roles = Column(JSONB, nullable=True)
    preferred_job_types = Column(JSONB, nullable=True)
    domain_focus = Column(JSONB, nullable=True)  # e.g., ["AI_ML", "DATA_SCIENCE", "BACKEND_ENGINEERING"]
    min_match_score = Column(Integer, nullable=True, default=60)
    daily_application_limit = Column(Integer, nullable=True, default=10)
    auto_apply_enabled = Column(Boolean, nullable=True, default=False)
    # Direct alert channels (Email & WhatsApp)
    alert_email = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    email_alerts_enabled = Column(Boolean, nullable=True, default=True)
    whatsapp_alerts_enabled = Column(Boolean, nullable=True, default=True)
    fresh_jobs_only = Column(Boolean, nullable=True, default=True)
    max_job_age_hours = Column(Integer, nullable=True, default=72)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
    documents = relationship("Document", back_populates="profile")
    skills = relationship("CandidateSkill", back_populates="profile")
    projects = relationship("CandidateProject", back_populates="profile")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False)
    filename = Column(String, nullable=False)
    hash = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String)
    document_type = Column(String)
    verification_status = Column(String, default="VERIFIED")
    file_path = Column(String, nullable=True)
    extracted_text = Column(Text, nullable=True)
    parsed_metadata = Column(JSONB, nullable=True)

    profile = relationship("CandidateProfile", back_populates="documents")
    claims = relationship("CandidateClaim", back_populates="document_evidence")

class CandidateProject(Base):
    __tablename__ = "candidate_projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
    profile = relationship("CandidateProfile", back_populates="projects")
    claims = relationship("CandidateClaim", back_populates="project_evidence")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    
    profile = relationship("CandidateProfile", back_populates="skills")
    claims = relationship("CandidateClaim", back_populates="skill")

class CandidateClaim(Base):
    __tablename__ = "candidate_claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("candidate_skills.id"), nullable=True)
    claim_text = Column(String, nullable=False)
    verification_status = Column(String, default="SUPPORTED")  # SUPPORTED / ALLOW / UNVERIFIED / REJECT
    
    project_evidence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_projects.id"), nullable=True)
    document_evidence_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    skill = relationship("CandidateSkill", back_populates="claims")
    project_evidence = relationship("CandidateProject", back_populates="claims")
    document_evidence = relationship("Document", back_populates="claims")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_job_id = Column(String, index=True)
    source = Column(String, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    url = Column(String, nullable=True)
    apply_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)
    status = Column(String, default="DISCOVERED")
    raw_jd = Column(JSONB, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Classification, freshness, genuineness, and domain suitability columns
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    role_level = Column(String, nullable=True)
    is_internship = Column(Boolean, nullable=True, default=False)
    eligibility_status = Column(String, nullable=True)
    graduation_year_min = Column(Integer, nullable=True)
    graduation_year_max = Column(Integer, nullable=True)
    domain_category = Column(String, nullable=True)
    is_genuine = Column(Boolean, nullable=True, default=True)
    genuineness_score = Column(Integer, nullable=True, default=100)
    is_fresh = Column(Boolean, nullable=True, default=True)

    requirements = relationship("JobRequirement", back_populates="job")
    applications = relationship("Application", back_populates="job")

class JobSourceRegistry(Base):
    __tablename__ = "job_source_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company = Column(String, nullable=False)
    career_url = Column(String, nullable=False)
    source_type = Column(String, nullable=False) # GREENHOUSE, LEVER, ASHBY, DIRECT_CAREER, LINKEDIN, INTERNSHALA, NAUKRI
    external_company_id = Column(String, nullable=True) # board slug or search query
    enabled = Column(Boolean, default=True)
    scan_interval_minutes = Column(Integer, default=30)
    
    last_scan_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
    jobs_found = Column(Integer, default=0)
    status = Column(String, default="ACTIVE") # ACTIVE, PAUSED, ERROR, BLOCKED, UNSUPPORTED
    country_focus = Column(String, nullable=True)   # e.g., 'India', 'USA', 'Global'
    tags = Column(JSONB, nullable=True)             # e.g., ["fintech", "india", "saas"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobRequirement(Base):
    __tablename__ = "job_requirements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    requirement_type = Column(String) # SKILL, EXPERIENCE, EDUCATION
    value = Column(String)
    is_required = Column(Boolean, default=True)
    
    job = relationship("Job", back_populates="requirements")

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, default="PREPARING")
    auto_submit = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(String, nullable=True)
    error_type = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    resume_id = Column(UUID(as_uuid=True), nullable=True)
    daily_limit_policy = Column(String, nullable=True)

    job = relationship("Job", back_populates="applications")
    user = relationship("User")
    answers = relationship("ApplicationAnswer", back_populates="application")
    events = relationship("ApplicationEvent", back_populates="application")

class ApplicationAnswer(Base):
    __tablename__ = "application_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    question_text = Column(String, nullable=False)
    question_type = Column(String)
    answer_text = Column(String)
    source_evidence_id = Column(UUID(as_uuid=True), ForeignKey("candidate_claims.id"), nullable=True)
    
    application = relationship("Application", back_populates="answers")

class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    worker_id = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    
    application = relationship("Application", back_populates="events")

class SubmissionEvidence(Base):
    __tablename__ = "submission_evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    url = Column(String, nullable=False)
    confirmation_text = Column(String, nullable=True)
    screenshot_path = Column(String, nullable=True)
    
    application = relationship("Application")

class GmailConnection(Base):
    __tablename__ = "gmail_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email_address = Column(String, nullable=False)
    provider = Column(String, default="google")
    encrypted_access_token = Column(String, nullable=False)
    encrypted_refresh_token = Column(String, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)
    scopes = Column(String, nullable=True)
    status = Column(String, default="CONNECTED")
    last_sync_at = Column(DateTime, nullable=True)
    last_history_id = Column(String, nullable=True) # Incremental cursor
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    emails = relationship("Email", back_populates="gmail_connection")

class Email(Base):
    __tablename__ = "emails"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gmail_connection_id = Column(UUID(as_uuid=True), ForeignKey("gmail_connections.id"), nullable=False)
    provider_message_id = Column(String, nullable=False, unique=True)
    thread_id = Column(String, nullable=False)
    sender = Column(String, nullable=True)
    sender_domain = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=False)
    snippet = Column(String, nullable=True)
    classification = Column(String, nullable=True)
    classification_confidence = Column(Float, nullable=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    gmail_connection = relationship("GmailConnection", back_populates="emails")
    application = relationship("Application")
    job = relationship("Job")

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True)
    title = Column(String, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    timezone = Column(String, nullable=True)
    meeting_url = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    interviewer = Column(String, nullable=True)
    status = Column(String, default="DETECTED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application")
    email = relationship("Email")

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True)
    platform = Column(String, nullable=True)
    url = Column(String, nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(String, default="DETECTED")
    instructions_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    application = relationship("Application")
    email = relationship("Email")

class MasterResume(Base):
    __tablename__ = "master_resumes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=False)
    version_name = Column(String, nullable=False) # e.g. "AI_ML", "FULL_STACK"
    content = Column(JSONB, nullable=False) # Structured sections

class GeneratedResume(Base):
    __tablename__ = "generated_resumes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)
    base_version_id = Column(UUID(as_uuid=True), ForeignKey("master_resumes.id"), nullable=False)
    tailored_content = Column(JSONB, nullable=False)
    diff_report = Column(JSONB, nullable=True) # Tracks changes made from master
    created_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=True) # S3 key for PDF/DOCX

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), nullable=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True)
    type = Column(String, nullable=False)
    priority = Column(String, nullable=False) # CRITICAL, HIGH, NORMAL, LOW
    title = Column(String, nullable=False)
    body = Column(String, nullable=False)
    payload = Column(JSONB, nullable=True)
    source_event_id = Column(String, nullable=True)
    dedupe_key = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(String, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'dedupe_key', name='_user_dedupe_uc'),
    )

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    endpoint = Column(String, nullable=False, unique=True)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    job_match_enabled = Column(Boolean, default=True)
    application_updates_enabled = Column(Boolean, default=True)
    interview_enabled = Column(Boolean, default=True)
    assessment_enabled = Column(Boolean, default=True)
    action_required_enabled = Column(Boolean, default=True)
    rejection_enabled = Column(Boolean, default=True)
    offer_enabled = Column(Boolean, default=True)
    system_enabled = Column(Boolean, default=True)
    daily_summary_enabled = Column(Boolean, default=False)
    
    web_push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)

    alert_email = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    min_match_score_threshold = Column(Integer, default=60)
    fresh_only_alerts = Column(Boolean, default=True)
    
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String, default="22:00")
    quiet_hours_end = Column(String, default="07:00")
    timezone = Column(String, default="Asia/Kolkata")
