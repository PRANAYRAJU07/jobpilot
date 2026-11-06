import sys
import os
import uuid
import hashlib

# Ensure apps/backend is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/backend')))

from database import SessionLocal
import models
from auth import get_password_hash

def seed_profile():
    db = SessionLocal()
    try:
        # 1. Create or get user
        user = db.query(models.User).filter_by(email="pranay@example.com").first()
        if not user:
            user = models.User(
                email="pranay@example.com",
                password_hash=get_password_hash("password123")
            )
            db.add(user)
            db.commit()

        # 3. Create Candidate Profile
        profile = db.query(models.CandidateProfile).filter_by(user_id=user.id).first()
        if not profile:
            profile = models.CandidateProfile(
                user_id=user.id,
                full_name="M Pranay Raju",
                phone="+91 0000000000",
                github="https://github.com/pranay",
                linkedin="https://linkedin.com/in/pranay",
                education="B.Tech CSE (AI & ML) at Malla Reddy University",
                cgpa=8.92,
                graduation_year=2027
            )
            db.add(profile)
            db.commit()
            
        # 2. Create Document (Resume)
        doc = db.query(models.Document).filter_by(profile_id=profile.id, filename="Pranay_Raju_Resume.pdf").first()
        if not doc:
            doc = models.Document(
                profile_id=profile.id,
                filename="Pranay_Raju_Resume.pdf",
                hash=hashlib.sha256(b"dummy resume content").hexdigest()
            )
            db.add(doc)
            db.commit()

        # 4. Create Projects
        projects = [
            {"title": "ASFO — Adaptive Semantic Federated Optimization", "desc": "Federated learning project using PyTorch and Docker."},
            {"title": "Video-to-Text Extractor", "desc": "Extracted text from video frames using OpenCV."},
            {"title": "AI-Enabled Hospital Management System", "desc": "Hospital management using FastAPI, PostgreSQL."},
            {"title": "Trading Platform", "desc": "Trading system built using Python, Redis, and WebSockets."}
        ]
        
        proj_map = {}
        for p in projects:
            cp = db.query(models.CandidateProject).filter_by(profile_id=profile.id, title=p["title"]).first()
            if not cp:
                cp = models.CandidateProject(profile_id=profile.id, title=p["title"], description=p["desc"])
                db.add(cp)
                db.commit()
            proj_map[p["title"]] = cp

        # 5. Create Skills & Claims
        skills = [
            ("Python", "Programming", proj_map["ASFO — Adaptive Semantic Federated Optimization"].id),
            ("Java", "Programming", None),
            ("JavaScript", "Programming", None),
            ("SQL", "Programming", proj_map["AI-Enabled Hospital Management System"].id),
            ("C", "Programming", None),
            ("PyTorch", "AI/ML", proj_map["ASFO — Adaptive Semantic Federated Optimization"].id),
            ("TensorFlow", "AI/ML", None),
            ("Scikit-learn", "AI/ML", None),
            ("Pandas", "AI/ML", None),
            ("NumPy", "AI/ML", None),
            ("OpenCV", "AI/ML", proj_map["Video-to-Text Extractor"].id),
            ("SHAP", "AI/ML", None),
            ("LLMs", "AI Systems", None),
            ("RAG", "AI Systems", None),
            ("Embeddings", "AI Systems", None),
            ("Agentic AI", "AI Systems", None),
            ("Prompt Engineering", "AI Systems", None),
            ("Knowledge Graphs", "AI Systems", None),
            ("Explainable AI", "AI Systems", None),
            ("AI Workflow Automation", "AI Systems", None),
            ("FastAPI", "Backend", proj_map["AI-Enabled Hospital Management System"].id),
            ("Flask", "Backend", None),
            ("REST APIs", "Backend", None),
            ("JSON", "Backend", None),
            ("API Integration", "Backend", None),
            ("Authentication", "Backend", None),
            ("Role-based workflows", "Backend", None),
            ("Data pipelines", "Backend", None),
            ("PostgreSQL", "Databases", proj_map["AI-Enabled Hospital Management System"].id),
            ("MySQL", "Databases", None),
            ("SQLite", "Databases", None),
            ("Redis", "Databases", proj_map["Trading Platform"].id),
            ("Docker", "Engineering", proj_map["ASFO — Adaptive Semantic Federated Optimization"].id),
            ("Docker Compose", "Engineering", None),
            ("Git", "Engineering", None),
            ("GitHub", "Engineering", None),
            ("Linux", "Engineering", None),
            ("MLflow", "Engineering", None),
            ("DVC", "Engineering", None),
            ("Pytest", "Engineering", None),
            ("MkDocs", "Engineering", None),
            ("AWS", "Engineering", None)
        ]

        for s_name, s_cat, proj_id in skills:
            sk = db.query(models.CandidateSkill).filter_by(profile_id=profile.id, name=s_name).first()
            if not sk:
                sk = models.CandidateSkill(profile_id=profile.id, name=s_name, category=s_cat)
                db.add(sk)
                db.commit()
                
            claim = db.query(models.CandidateClaim).filter_by(profile_id=profile.id, skill_id=sk.id).first()
            if not claim:
                claim = models.CandidateClaim(
                    profile_id=profile.id,
                    skill_id=sk.id,
                    claim_text=f"Has skill {s_name}",
                    verification_status="SUPPORTED" if proj_id or doc else "UNVERIFIED",
                    project_evidence_id=proj_id,
                    document_evidence_id=doc.id if not proj_id else None
                )
                db.add(claim)
                db.commit()
                
        print("Profile, Projects, Skills, and Claims seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_profile()
