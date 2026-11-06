"""
Truth Engine + End-to-End Pipeline Verification Script
Phase 15.1 — Tests REAL evidence graph, eligibility, matching, and failure cases.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/backend')))

from database import SessionLocal
import models
from services.job_engine import JobEngineService

db = SessionLocal()
engine = JobEngineService(db)
profile = db.query(models.CandidateProfile).first()
if not profile:
    print("FATAL: No candidate profile found.")
    sys.exit(1)

print(f"=== Candidate Profile ===")
print(f"  Name:      {profile.full_name}")
print(f"  Education: {profile.education}")
print(f"  CGPA:      {profile.cgpa}")
print(f"  Grad Year: {profile.graduation_year}")

# Build claim evidence map from real DB
claims = db.query(models.CandidateClaim).filter_by(profile_id=profile.id).all()
verified_map = {c.skill.name.lower(): c for c in claims if c.skill and c.verification_status == "SUPPORTED"}
print(f"\n  Verified skills count: {len(verified_map)}")

# ===== TRUTH ENGINE TESTS =====
print("\n=== Truth Engine Tests ===")
tests = [
    # (skill, should_be_supported)
    ("Python",      True),
    ("PyTorch",     True),
    ("FastAPI",     True),
    ("Docker",      True),
    ("OpenCV",      True),
    ("PostgreSQL",  True),
    ("Redis",       True),
    ("SQL",         True),
    ("LLMs",        True),
    ("RAG",         True),
    ("Rust",        False),   # NOT in evidence
    ("Kubernetes",  False),   # NOT in evidence
    ("Spring Boot", False),   # NOT in evidence
    ("Cassandra",   False),   # NOT in evidence
]

passed = 0
failed = 0
for skill, expected in tests:
    found = skill.lower() in verified_map
    result = "PASS" if found == expected else "FAIL"
    evidence = ""
    if found and verified_map.get(skill.lower()):
        c = verified_map[skill.lower()]
        if c.project_evidence:
            evidence = f"(Project: {c.project_evidence.title})"
        elif c.document_evidence:
            evidence = f"(Doc: {c.document_evidence.filename})"
    
    status = "SUPPORTED" if found else "UNSUPPORTED"
    print(f"  [{result}] {skill:25s} expected={'SUPPORTED' if expected else 'UNSUPPORTED':12s} actual={status} {evidence}")
    if result == "PASS":
        passed += 1
    else:
        failed += 1

print(f"\n  Truth Engine: {passed} PASS / {failed} FAIL")

# ===== 20-JOB END-TO-END TEST =====
print("\n=== 20 Real Jobs End-to-End Pipeline Test ===")
# Select a diverse real 20-job sample  
sample_jobs = db.query(models.Job).filter(models.Job.status == "MATCHED").limit(20).all()

print(f"{'#':>2}  {'Company':12s} {'Title':45s} {'Score':5s} {'Matched':3s} {'Missing':3s}")
print("-" * 90)

for i, job in enumerate(sample_jobs, 1):
    raw = job.raw_jd or {}
    ma = raw.get("match_analysis", {})
    score = ma.get("relevance_score", "?")
    matched = len(ma.get("matched_skills", []))
    missing = len(ma.get("missing_skills", []))
    print(f"{i:2}. {(job.company or ''):12s} {(job.title or '')[:45]:45s} {score:5}  {matched:3}/{matched+missing}")

# ===== DEDUPLICATION TEST =====
print("\n=== Deduplication Test ===")
# Re-run a single source and verify 0 new inserts
figma_src = db.query(models.JobSourceRegistry).filter_by(company="Figma").first()
from job_discovery.pipeline import JobDiscoveryPipeline
pipeline = JobDiscoveryPipeline(db)
before_count = db.query(models.Job).filter_by(company="Figma").count()
pipeline.run_discovery(str(figma_src.id))
after_count = db.query(models.Job).filter_by(company="Figma").count()
new_inserts = after_count - before_count
print(f"  Before re-scan: {before_count} Figma jobs")
print(f"  After re-scan:  {after_count} Figma jobs")
print(f"  New inserts:    {new_inserts}  (expected: 0)")
print(f"  Deduplication: {'PASS' if new_inserts == 0 else 'FAIL'}")

# ===== FAILURE CASES =====
print("\n=== Failure Case Tests ===")

# Test 1: malformed JD (no description, no title)
import models as m
fake_job = m.Job(title=None, description=None, company="Test", source="TEST", external_job_id="test-fail-001", raw_jd={})
try:
    req = engine.analyze_jd(fake_job)
    print(f"  [PASS] Malformed JD handled gracefully: extracted {len(req['required_skills'])} skills from empty JD")
except Exception as e:
    print(f"  [FAIL] Malformed JD raised exception: {e}")

# Test 2: check ANALYZED_NO_PROFILE count now
no_profile = db.query(models.Job).filter(models.Job.status == "ANALYZED_NO_PROFILE").count()
print(f"  [INFO] ANALYZED_NO_PROFILE jobs remaining: {no_profile} (expected: 0)")

# ===== DATABASE SUMMARY =====
print("\n=== Database Summary ===")
total = db.query(models.Job).count()
by_source = db.execute(models.Job.__table__.select().with_only_columns([
    models.Job.source, models.Job.company
])).fetchall() if False else None
print(f"  Total jobs: {total}")
print(f"  Total skills with evidence: {len(verified_map)}")
print(f"  Skills: {', '.join(verified_map.keys())}")
print(f"\n  Projects:")
for p in db.query(models.CandidateProject).filter_by(profile_id=profile.id).all():
    print(f"    - {p.title}")
print(f"\n  Claims count: {len(claims)}")

db.close()
print("\n=== Phase 15.1 Verification Complete ===")
