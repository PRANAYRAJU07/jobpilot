import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import GmailConnection, Email, Application, Job, User, ApplicationEvent, Interview, Assessment
from services.email_intelligence import EmailIntelligenceService

@pytest.fixture
def db():
    return MagicMock()

@pytest.fixture
def setup_data(db):
    user = User(id=uuid4(), email="test@example.com")
    conn = GmailConnection(
        id=uuid4(),
        user_id=user.id,
        email_address="mpranayraju2@gmail.com",
        encrypted_access_token="acc",
        encrypted_refresh_token="ref",
        token_expires_at=datetime.utcnow()
    )
    job = Job(id=uuid4(), title="AI Engineer", company="TechCorp")
    app = Application(id=uuid4(), user_id=user.id, job_id=job.id, status="SUBMISSION_VERIFY")
    
    # Mock queries
    db.query.return_value.all.return_value = [job]
    db.query.return_value.filter_by.return_value.first.return_value = app
    
    return {"user": user, "connection": conn, "job": job, "application": app}


def test_application_confirmation_classification_and_precedence(db, setup_data):
    intelligence = EmailIntelligenceService(db)
    
    email_data = {
        "id": "msg1",
        "thread_id": "thread1",
        "sender": "no-reply@techcorp.com",
        "sender_domain": "techcorp.com",
        "subject": "Thank you for applying to TechCorp",
        "snippet": "We have received your application for the AI Engineer role.",
        "received_at": datetime.utcnow()
    }
    
    email = intelligence.classify_and_match(email_data, setup_data["connection"])
    
    assert email.classification == "APPLICATION_CONFIRMATION"
    assert email.application_id == setup_data["application"].id
    
    # State Precedence Check: SUBMISSION_VERIFY -> CONFIRMED
    assert setup_data["application"].status == "CONFIRMED"

def test_false_positive_interview(db, setup_data):
    intelligence = EmailIntelligenceService(db)
    
    email_data = {
        "id": "msg2",
        "thread_id": "thread2",
        "sender": "marketing@techcorp.com",
        "sender_domain": "techcorp.com",
        "subject": "Weekly Newsletter: 10 Interview Tips",
        "snippet": "Click here to unsubscribe. Here are some interview tips.",
        "received_at": datetime.utcnow()
    }
    
    email = intelligence.classify_and_match(email_data, setup_data["connection"])
    
    # Should not classify as INTERVIEW due to unsubscribe / marketing heuristic
    assert email.classification == "UNKNOWN"

def test_assessment_detection(db, setup_data):
    intelligence = EmailIntelligenceService(db)
    
    email_data = {
        "id": "msg3",
        "thread_id": "thread3",
        "sender": "assessments@hackerrank.com",
        "sender_domain": "hackerrank.com", # Note: Domain matching might fail if company name doesn't match
        "subject": "TechCorp Online Assessment",
        "snippet": "Please complete the hackerrank assessment.",
        "received_at": datetime.utcnow()
    }
    
    email = intelligence.classify_and_match(email_data, setup_data["connection"])
    
    # It should still classify as ASSESSMENT based on keywords, even if application match fails
    assert email.classification == "ASSESSMENT"

def test_rejection_detection(db, setup_data):
    intelligence = EmailIntelligenceService(db)
    
    email_data = {
        "id": "msg4",
        "thread_id": "thread4",
        "sender": "recruiter@techcorp.com",
        "sender_domain": "techcorp.com",
        "subject": "Update on your application",
        "snippet": "We have decided to move forward with other candidates.",
        "received_at": datetime.utcnow()
    }
    
    email = intelligence.classify_and_match(email_data, setup_data["connection"])
    
    assert email.classification == "REJECTION"
    assert setup_data["application"].status == "REJECTED"
