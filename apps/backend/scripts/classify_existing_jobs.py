#!/usr/bin/env python3
"""
Classify all existing jobs with India/internship/role_level metadata.
Safe to re-run — only updates jobs where country IS NULL.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

INDIA_LOCATION_KEYWORDS = [
    'india', 'hyderabad', 'bengaluru', 'bangalore', 'pune', 'chennai',
    'mumbai', 'delhi', 'noida', 'gurugram', 'gurgaon', 'kolkata',
    'ahmedabad', 'jaipur', 'kochi', 'remote - india', 'india remote',
    'remote (india)', 'remote, india', 'blr', 'hyd', 'telangana',
    'karnataka', 'maharashtra', 'tamil nadu', 'andhra'
]

INTERN_KEYWORDS = ['intern', 'internship', 'trainee', 'apprentice']

ROLE_LEVELS = {
    'INTERN': ['intern', 'internship', 'trainee', 'apprentice'],
    'FRESHER': ['fresher', 'graduate', 'entry level', 'entry-level', '0-1 year', '0-2 year', 'new grad', 'campus'],
    'JUNIOR': ['junior', 'jr.', 'jr ', 'associate', '1-2 year', '2-3 year', '1-3 year'],
    'MID': ['mid level', 'mid-level', '3-5 year', '4-6 year', 'ii ', 'level 2'],
    'SENIOR': ['senior', 'sr.', 'sr ', 'lead', '5+ year', '6+ year', '7+ year', '8+ year', '5-8 year'],
    'STAFF': ['staff engineer', 'staff software', 'principal engineer', 'distinguished'],
    'MANAGER': ['manager', 'director', 'head of', 'vp ', 'vice president', 'chief'],
}

def classify_location(location):
    if not location:
        return None, None, False
    loc_lower = location.lower()
    is_india = any(kw in loc_lower for kw in INDIA_LOCATION_KEYWORDS)
    
    city = None
    for c in ['hyderabad', 'bengaluru', 'bangalore', 'pune', 'chennai', 'mumbai', 'delhi', 'noida', 'gurugram', 'gurgaon', 'kolkata', 'kochi', 'ahmedabad', 'jaipur']:
        if c in loc_lower:
            city = c.title()
            break
    
    country = 'India' if is_india else None
    if not country:
        for us_kw in ['united states', ' usa', ', ca', ', ny', ', tx', ', wa', ', ma', 'san francisco', 'new york', 'seattle', 'austin', 'boston']:
            if us_kw in loc_lower:
                country = 'USA'
                break
    if not country:
        for uk_kw in ['united kingdom', ' uk ', 'london', 'manchester']:
            if uk_kw in loc_lower:
                country = 'UK'
                break
    if not country:
        if any(r in loc_lower for r in ['remote', 'worldwide', 'anywhere', 'global']):
            country = 'Remote'
    
    return country, city, is_india

def classify_role(title, description):
    if not title:
        return 'UNKNOWN'
    text = (title + ' ' + (description or '')[:1000]).lower()
    for level, kws in ROLE_LEVELS.items():
        for kw in kws:
            if kw in text:
                return level
    return 'UNKNOWN'

def is_intern(title):
    if not title:
        return False
    return any(kw in title.lower() for kw in INTERN_KEYWORDS)

def check_graduation(description, target=2027):
    import re
    if not description:
        return 'UNKNOWN'
    desc = description.lower()[:3000]
    years = re.findall(r'20(2[3-9]|3[0-2])', desc)
    if years:
        y = [int(yy) for yy in years]
        if target in [2000+int(yy) for yy in years] or max(2000+int(yy) for yy in years) >= target:
            return 'ELIGIBLE'
        if min(2000+int(yy) for yy in years) > target:
            return 'NOT_ELIGIBLE'
    exp = re.findall(r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s*(?:of\s*)?(?:experience|exp)', desc)
    if exp:
        min_exp = min(int(e) for e in exp)
        if min_exp >= 3:
            return 'NOT_ELIGIBLE'
        if min_exp <= 1:
            return 'ELIGIBLE'
    return 'UNKNOWN'


def main():
    db = SessionLocal()
    try:
        total = db.query(models.Job).count()
        unclassified = db.query(models.Job).filter(models.Job.country == None).count()
        print(f"Total jobs: {total}, Unclassified: {unclassified}")
        
        jobs = db.query(models.Job).filter(models.Job.country == None).all()
        
        india_count = 0
        hyd_count = 0
        intern_count = 0
        updated = 0
        
        for i, job in enumerate(jobs):
            country, city, is_india = classify_location(job.location)
            role_level = classify_role(job.title, job.description)
            internship = is_intern(job.title)
            eligibility = check_graduation(job.description)
            
            job.country = country
            job.region = city
            job.role_level = role_level
            job.is_internship = internship
            job.eligibility_status = eligibility
            
            if is_india:
                india_count += 1
            if city and city.lower() == 'hyderabad':
                hyd_count += 1
            if internship:
                intern_count += 1
            updated += 1
            
            if (i + 1) % 100 == 0:
                db.commit()
                print(f"  Processed {i+1}/{len(jobs)}...")
        
        db.commit()
        
        # Also classify all jobs (including previously classified) for summary
        all_india = db.query(models.Job).filter(models.Job.country == 'India').count()
        all_hyd = db.query(models.Job).filter(models.Job.location.ilike('%hyderabad%')).count()
        all_intern = db.query(models.Job).filter(
            (models.Job.is_internship == True) | (models.Job.title.ilike('%intern%'))
        ).count()
        all_eligible = db.query(models.Job).filter(models.Job.eligibility_status == 'ELIGIBLE').count()
        
        print(f"\n=== Classification Complete ===")
        print(f"Updated: {updated} jobs")
        print(f"Total India jobs: {all_india}")
        print(f"Total Hyderabad jobs: {all_hyd}")
        print(f"Total Internship jobs: {all_intern}")
        print(f"Total Eligible (2027): {all_eligible}")
        print(f"Total jobs in DB: {total}")
        
    finally:
        db.close()


if __name__ == '__main__':
    main()
