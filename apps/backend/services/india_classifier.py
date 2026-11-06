"""
India Job Classifier -- determines if a job is India-eligible, its role level, and internship status.
Never fabricates data. Only uses actual job title and location strings.
"""

INDIA_LOCATION_KEYWORDS = [
    'india', 'hyderabad', 'bengaluru', 'bangalore', 'pune', 'chennai',
    'mumbai', 'delhi', 'noida', 'gurugram', 'gurgaon', 'kolkata',
    'ahmedabad', 'jaipur', 'kochi', 'remote - india', 'india remote',
    'remote (india)', 'remote, india', 'blr', 'hyd'
]

INTERN_TITLE_KEYWORDS = [
    'intern', 'internship', 'trainee', 'apprentice'
]

ROLE_LEVEL_MAP = {
    'intern': ['intern', 'internship', 'trainee', 'apprentice'],
    'fresher': ['fresher', 'graduate', 'entry', '0-1 year', '0-2 year', 'new grad'],
    'junior': ['junior', 'jr.', 'associate', '1-2 year', '2-3 year', '1-3 year'],
    'mid': ['mid', 'mid-level', '3-5 year', '4-6 year'],
    'senior': ['senior', 'sr.', 'lead', '5+ year', '6+ year', '7+ year', '8+ year'],
    'staff': ['staff engineer', 'staff software', 'principal'],
    'manager': ['manager', 'director', 'head of', 'vp ', 'vice president'],
}

def classify_location(location):
    """Returns {country, region, is_india, city_guess}"""
    if not location:
        return {'country': None, 'region': None, 'is_india': False, 'city_guess': None}
    
    loc_lower = location.lower()
    is_india = any(kw in loc_lower for kw in INDIA_LOCATION_KEYWORDS)
    
    city_guess = None
    for city in ['hyderabad', 'bengaluru', 'bangalore', 'pune', 'chennai', 'mumbai', 'delhi', 'noida', 'gurugram', 'gurgaon', 'kolkata', 'kochi', 'ahmedabad', 'jaipur']:
        if city in loc_lower:
            city_guess = city.title()
            break
    
    country = 'India' if is_india else None
    if not is_india:
        for us_kw in ['united states', 'usa', ', ca', ', ny', ', tx', ', wa', ', ma', 'san francisco', 'new york', 'seattle', 'austin', 'boston', 'chicago']:
            if us_kw in loc_lower:
                country = 'USA'
                break
        for remote_kw in ['remote', 'anywhere']:
            if remote_kw in loc_lower and not country:
                country = 'Remote'
    
    return {
        'country': country,
        'region': city_guess,
        'is_india': is_india,
        'city_guess': city_guess,
    }


def classify_role_level(title, description):
    """Returns one of: INTERN, FRESHER, JUNIOR, MID, SENIOR, STAFF, MANAGER, UNKNOWN"""
    if not title:
        return 'UNKNOWN'
    
    text = (title + ' ' + (description or '')[:500]).lower()
    
    for level, keywords in ROLE_LEVEL_MAP.items():
        for kw in keywords:
            if kw in text:
                return level.upper()
    return 'UNKNOWN'


def is_internship(title):
    if not title:
        return False
    title_lower = title.lower()
    return any(kw in title_lower for kw in INTERN_TITLE_KEYWORDS)


def check_graduation_eligibility(description, candidate_year=2027):
    """Returns ELIGIBLE, NOT_ELIGIBLE, or UNKNOWN based on graduation year mentions."""
    if not description:
        return 'UNKNOWN'
    
    desc_lower = description.lower()[:2000]
    
    import re
    years_mentioned = re.findall(r'20(2[3-9]|3[0-5])', desc_lower)
    if years_mentioned:
        years = [int(y) for y in years_mentioned]
        if candidate_year in years or max(years) >= candidate_year:
            return 'ELIGIBLE'
        if min(years) > candidate_year:
            return 'NOT_ELIGIBLE'
    
    exp_patterns = re.findall(r'(\d+)\+?\s*(?:to\s*\d+)?\s*years?\s*(?:of)?\s*(?:experience)?', desc_lower)
    if exp_patterns:
        min_exp = min(int(e) for e in exp_patterns)
        if min_exp >= 3:
            return 'NOT_ELIGIBLE'
        if min_exp <= 1:
            return 'ELIGIBLE'
    
    return 'UNKNOWN'
