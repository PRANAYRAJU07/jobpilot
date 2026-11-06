# Phase 15.1 - Current State of Candidate & Matching

## Models
- **CandidateProfile**: Stores basic details (name, education, cgpa, grad year, links).
- **CandidateProject**: Represents projects a candidate has worked on (ASFO, etc).
- **CandidateSkill**: Represents explicit skills (Python, PyTorch).
- **CandidateClaim**: Represents the connection between a skill/claim and its evidence (Project or Document) along with a `verification_status` (`UNVERIFIED`, `VERIFIED`/`SUPPORTED`).
- **Document**: Represents uploaded resumes/source files.
- **JobEngineService**: Contains JD Analysis, Eligibility Check, and Match Score calculation logic.

## Analysis State
Currently, thousands of jobs are in the `jobs` table with `status = "ANALYZED_NO_PROFILE"` because the JobEngine gracefully bails out if it finds no user profile during discovery.

## Plan
1. Create a User.
2. Create a Document (Resume).
3. Create a CandidateProfile for M Pranay Raju with all explicit fields (B.Tech CSE, 8.92 CGPA, 2027 grad year).
4. Create CandidateProjects (ASFO, Video-to-Text, AI-HMS, Trading Platform).
5. Create CandidateSkills and CandidateClaims mapped to the Resume and Projects.
6. Verify TruthEngine behavior (Claim -> Evidence -> Status).
7. Execute JobEngine pipeline against the populated profile and 20 real jobs to verify the end-to-end `ANALYZED_NO_PROFILE` -> `MATCHED`/`NOT_ELIGIBLE` transition.
