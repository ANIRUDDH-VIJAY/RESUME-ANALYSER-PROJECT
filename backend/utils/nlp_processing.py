# backend/utils/nlp_processing.py

import spacy
import re
from typing import List, Dict, Set

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    exit()

# --- Canonical List of Skills & Aliases ---
# Key: canonical skill name (preferred display/comparison form)
# Value: a set of all its common lowercase aliases/variations found in text
CANONICAL_SKILLS_MAP = {
    "Python": {"python"}, "Java": {"java"}, "C++": {"c++"}, "C#": {"c#"},
    "JavaScript": {"javascript", "js"}, "TypeScript": {"typescript"}, "React": {"react", "reactjs"},
    "Node.js": {"node.js", "nodejs"}, "Angular": {"angular", "angularjs"}, "Vue.js": {"vue.js", "vuejs"},
    "SQL": {"sql", "mysql", "postgresql", "sqlite"},
    "NoSQL": {"nosql", "mongodb", "cassandra", "redis", "couchbase"}, # All related NoSQL dbs map to NoSQL
    "ML": {"machine learning", "ml", "machinelearning"},
    "Deep Learning": {"deep learning", "dl", "deeplearning"},
    "NLP": {"nlp", "natural language processing"},
    "Data Analysis": {"data analysis", "data analytics"},
    "Data Science": {"data science"}, "Computer Vision": {"computer vision"}, "AI": {"artificial intelligence", "ai"},
    "HTML": {"html"}, "CSS": {"css"}, "Redux": {"redux"}, "Express.js": {"express.js", "expressjs"},
    "Django": {"django"}, "Flask": {"flask"}, "FastAPI": {"fastapi"}, "Spring Boot": {"spring boot"},
    "AWS": {"aws", "amazon web services"}, "Azure": {"azure", "microsoft azure"}, "GCP": {"gcp", "google cloud platform"},
    "Docker": {"docker", "containerization"},
    "Kubernetes": {"kubernetes"}, "Git": {"git"}, "Jira": {"jira"}, "Jenkins": {"jenkins"},
    "Travis CI": {"travis ci"}, "CircleCI": {"circleci"},
    "TensorFlow": {"tensorflow"}, "PyTorch": {"pytorch"}, "Scikit-learn": {"scikit-learn"},
    "Pandas": {"pandas"}, "NumPy": {"numpy"}, "Matplotlib": {"matplotlib"}, "Seaborn": {"seaborn"},
    "Agile": {"agile"}, "Scrum": {"scrum"}, "DevOps": {"devops"}, "CI/CD": {"ci/cd"},
    "REST API": {"rest api", "restful", "restful api", "restful services"},
    "Microservices": {"microservices", "microservice"}, "Unit Testing": {"unit testing"}, "Integration Testing": {"integration testing"},
    "Linux": {"linux"}, "Unix": {"unix"}, "Bash": {"bash"}, "Shell Scripting": {"shell scripting"},
    "API Development": {"api development"}, "Web Development": {"web development", "full stack web development"},
    "Mobile Development": {"mobile development"}, "Cloud Computing": {"cloud computing", "cloud platforms", "cloud"},
    "Big Data": {"big data"}, "Spark": {"spark", "apache spark"}, "Hadoop": {"hadoop"}, "Kafka": {"kafka"},
    "ETL": {"etl", "extract transform load", "apache airflow"},
    "Data Warehousing": {"data warehousing"},
    "Object-Oriented Programming": {"object-oriented programming", "oop"}, "Functional Programming": {"functional programming"},
    "Algorithms": {"algorithms", "data structures and algorithms"},
    "Data Structures": {"data structures"},
    "Cybersecurity": {"cybersecurity"}, "Network Security": {"network security"}, "Cloud Security": {"cloud security"},
    "Blockchain": {"blockchain"}, "Solidity": {"solidity"},
    "UI/UX Design": {"ui/ux design"}, "Figma": {"figma"}, "Sketch": {"sketch"}, "Adobe XD": {"adobe xd"},
    "Photoshop": {"photoshop"}, "Illustrator": {"illustrator"},
    "Project Management": {"project management"},
    "Risk Management": {"risk management"}, "Business Analysis": {"business analysis"}, "Requirements Gathering": {"requirements gathering"},
    "Technical Documentation": {"technical documentation"}, "Communication": {"communication"}, "Teamwork": {"teamwork"},
    "Problem Solving": {"problem solving"}, "Leadership": {"leadership"},
    "Microsoft Office": {"microsoft office", "ms office"}, "Excel": {"excel"}, "PowerPoint": {"powerpoint"}, "Word": {"word"}, "Google Workspace": {"google workspace", "gsuite"},
    "R": {"r"}, "Go": {"go"}, "Rust": {"rust"}, "Swift": {"swift"}, "Kotlin": {"kotlin"}, "PHP": {"php"}, "Laravel": {"laravel"},
    "Ruby": {"ruby"}, "Ruby on Rails": {"ruby on rails"}, "XGBoost": {"xgboost"}, "Streamlit": {"streamlit"},
    "Statistical Modeling": {"statistical modeling", "statistics", "probability"},
    "Container Orchestration": {"container orchestration"},
    "MLOps": {"mlops", "machine learning operations", "kubeflow"}
}

# Invert the map for efficient lookup of canonical form from any alias
ALIAS_TO_CANONICAL = {alias: canonical for canonical, aliases in CANONICAL_SKILLS_MAP.items() for alias in aliases}


# Helper to get the canonical form of a skill (returns canonical or original text if not found)
def _get_canonical_skill(skill_text: str) -> str:
    return ALIAS_TO_CANONICAL.get(skill_text.lower(), skill_text)


# Helper to normalize skill casing for display based on its canonical form
def _normalize_skill_casing(skill_text: str) -> str:
    canonical = _get_canonical_skill(skill_text)
    # Return the canonical form's preferred casing from CANONICAL_SKILLS_MAP keys
    for predefined_skill_key in CANONICAL_SKILLS_MAP.keys():
        if predefined_skill_key == canonical:
            return predefined_skill_key
    # Fallback if somehow a skill isn't in canonical map keys (shouldn't happen with good mapping)
    return canonical.title()


def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    doc = nlp(text_lower)
    found_skills_canonical_lower: Set[str] = set() # Store canonical, lowercased forms for true uniqueness

    # --- Strict non-skill entities and exclusion patterns ---
    # Expanded and refined further
    non_skill_entities_lower = {
        # General terms (expanded to filter more aggressively)
        "company", "project", "team", "solution", "system", "role", "position", "highlights",
        "experience", "responsibilities", "qualifications", "education", "benefits", "overview", "job overview",
        "intern", "engineer", "analyst", "developer", "manager", "specialist", "scientist", "firm",
        "client", "customer", "stakeholder", "user", "model", "product", "services", "building", "implementing",
        "research", "development", "design", "testing", "management", "quality", "quality assurance",
        "business", "strategy", "metrics", "performance", "optimization", "growth", "impact",
        "problem", "flow", "workflow", "process", "report", "communication", "leadership", "teamwork", "problem solving",
        "agile", "scrum", "kanban", "methodology", "methodologies", "principles", "concepts", "frameworks",
        "platform", "library", "tool", "software", "hardware", "service", "api", "database",
        "server", "architecture", "security", "data", "science", "learning", "network", "cloud",
        "computing", "analytics", "prediction", "forecasting", "technical", "documentation",
        "requirements", "gathering", "mobile", "web", "full stack", "distributed", "frontend", "backend",
        "quantitative", "foundation", "foundations", "exposure", "theory", "theoretical", "related",
        "rmse", "linear", "alpha", "delta", "gpa", "india", "jaipur", "delhi", "mumbai", "location", # Locations, metrics, generic words
        "june", "march", "may", "jan", "jun", "february", "april", "july", "august", "september", "october", "november", "december", # Month names
        "2020", "2021", "2022", "2023", "2024", "2025", "2026", "2027", "2028", "2029", "2030", # Years
        "microsoft", "google", "amazon", "apple", "ibm", "oracle", "accenture", "tata", # Major companies (unless specific product)
        "gmail", "linkedin", "github", "powerpoint", "excel", "word", "outlook", "vs code", # Generic software/platforms
        "pythonsoftwarefoundation", "explosion", # From tracebacks/system
        "records", "rows", "features", "datasets", "day", "days", "months", "years", "percent", "rate", # Units/quantities
        "cut", "achieved", "engineered", "spearheaded", "optimized", "collaborated", "championed", "managed", "solved", "built", "implemented", "utilized", "contributing", "designing", "maintaining", "integrate", "conduct", "participate", "translate", "ensure", "monitor", # Action verbs
        "pipeline", "pipelines", "models", "systems", "architecture", "products", "environment", "environments", "lifecycle",
        "workflow orchestration tools", "data visualization tools", # Generic descriptions for tool categories
        "job", "title", "company", "about", "overview", "responsibilities", "required", "preferred", "qualifications", "benefits",
        "experience highlights", "selected projects", "technical skills", "education", "certifications", "profile", # Section headers
        "api development", "web development", "mobile development", # These are skills, but included to ensure custom processing
        "high school", "diploma", "honours", "hons", "bachelor", "master", "phd", "university", "college", "school", "institute", # Education related terms
        "full stack" # Part of "full stack web development", ensure it's not picked up alone
    }

    compiled_exclusion_patterns = [
        re.compile(r"^\d+(\.\d+)?%?$"), # Percentages like "87%" or just "87"
        re.compile(r"^\d+$"), # Pure numbers
        re.compile(r"^\w\s*\d+(\.\d+)?$"), # Single letter + number (e.g., c 2025), potentially with decimals
        re.compile(r"^\d{4}$"), # Years
        re.compile(r"rmse(~)?\s*\d+(\.\d+)?"), # RMSE values (more robust)
        re.compile(r"\b(hours|minutes|seconds|days|weeks|months|years|records|features|rows)\b", re.IGNORECASE), # Units
        re.compile(r"^\s*[\-\*]\s*"), # Bullet points (more robust)
        re.compile(r"^(?=.*\d)(?=.*[a-zA-Z]).+$") # Alphanumeric strings that might be codes/ids, not skills (e.g., "ID123")
    ]


    # --- Extraction Logic ---
    # Phase 1: Match from the canonical map's aliases
    for canonical_skill, aliases in CANONICAL_SKILLS_MAP.items():
        for alias in aliases:
            # Check for the alias in the text
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                found_skills_canonical_lower.add(canonical_skill.lower()) # Add canonical (lowercased) form


    # Phase 2: NER entities with filtering
    for ent in doc.ents:
        entity_text = ent.text.strip()
        normalized_ent_text_lower = entity_text.lower()

        # Apply basic length filter (skip single characters or very long phrases)
        if not (1 <= len(entity_text.split()) <= 5):
            continue

        # Check against non-skill list and compiled regex patterns
        if normalized_ent_text_lower in non_skill_entities_lower or \
           any(pattern.search(normalized_ent_text_lower) for pattern in compiled_exclusion_patterns):
            continue

        # Convert entity text to its canonical form if it's an alias
        canonical_from_ner = ALIAS_TO_CANONICAL.get(normalized_ent_text_lower)

        if canonical_from_ner:
            found_skills_canonical_lower.add(canonical_from_ner.lower())
        # If not a known alias, consider adding based on NER label (with caution)
        elif ent.label_ in ["ORG", "PRODUCT", "LANGUAGE", "WORK_OF_ART", "EVENT"]:
            # Only add if it's not a generic company name or too broad and is likely a skill
            if normalized_ent_text_lower not in ["microsoft", "google", "amazon", "apple", "ibm", "oracle", "apache"]: # Avoid very broad company names unless they are also specific products
                found_skills_canonical_lower.add(entity_text.lower()) # Add lowercased original, will be canonicalized later
        elif ent.label_ == "PERSON":
            # Special case for 'R' language if it gets tagged as PERSON
            if normalized_ent_text_lower == "r":
                found_skills_canonical_lower.add("r")
            else:
                continue # Skip other general person names


    # Phase 3: Broad regex patterns (for skills potentially missed by NER/direct list)
    tech_patterns = [
        r"\b(?:c\+\+|c#|node\.js|vue\.js|react\.js|\.net|sql|nosql|restful|graphql)\b",
        r"\b(api|rest|graphql|oauth|jwt)\b",
        r"\b(cloud|azure|aws|gcp|vmware)\b",
        r"\b(ml|ai|dl|nlp|mlops)\b",
        r"\b(ci\/cd|devops|etl)\b",
        r"\b(xgboost|streamlit|jupyter)\b",
        r"\b(data analysis|data science|machine learning|deep learning|computer vision)\b",
        r"\b(algorithms|data structures|object-oriented programming|functional programming)\b",
        r"\b(pytorch|tensorflow|scikit-learn|pandas|numpy|matplotlib|seaborn)\b",
        r"\b(big data|time series analysis|container orchestration|data warehousing)\b",
        r"\b(project management|risk management|statistical modeling|web development|api development|mobile development|business analysis|requirements gathering|technical documentation)\b",
        r"\b(linux|unix|bash|shell scripting)\b",
        r"\b(jira|jenkins|travis ci|circleci|git)\b",
        r"\b(express\.js|django|flask|spring boot)\b",
        r"\b(html|css|redux)\b"
    ]
    for pattern in tech_patterns:
        for match in re.findall(pattern, text_lower):
            found_skills_canonical_lower.add(_get_canonical_skill(match).lower()) # Add canonical (lowercased) form

    # Final Deduplication & Canonical Casing for display
    # Convert the set of lowercased canonical forms to a sorted list of preferred-cased canonical forms
    final_display_skills: List[str] = sorted(list(_normalize_skill_casing(s) for s in found_skills_canonical_lower))

    return final_display_skills


# calculate_job_fit_score remains the same as it relies on the output of extract_skills
def calculate_job_fit_score(resume_skills: List[str], jd_skills: List[str]) -> Dict[str, any]:
    # Debug prints (keep these for now to monitor)
    print(f"\n--- Debug: calculate_job_fit_score called ---")
    print(f"Resume skills received ({len(resume_skills)}): {resume_skills}") # Print full lists now
    print(f"JD skills received ({len(jd_skills)}): {jd_skills}")

    # Normalize all skills to lowercase canonical forms for robust set operations
    resume_skills_lower = set(_get_canonical_skill(skill).lower() for skill in resume_skills)
    jd_skills_lower = set(_get_canonical_skill(skill).lower() for skill in jd_skills)

    print(f"Resume skills lower ({len(resume_skills_lower)}): {resume_skills_lower}")
    print(f"JD skills lower ({len(jd_skills_lower)}): {jd_skills_lower}")


    # Find common skills (intersection of lowercased canonical sets)
    matched_lower_skills = resume_skills_lower.intersection(jd_skills_lower)

    # Convert back to consistently cased skills for presentation
    # Ensure no duplicates in the output lists (already handled by set logic, but _normalize_skill_casing might yield same str from different inputs)
    matched_skills = []
    seen_matched = set()
    for s in jd_skills: # Iterate JD skills as primary source for 'matched' list order/preference
        canonical_s = _get_canonical_skill(s)
        normalized_s_display = _normalize_skill_casing(canonical_s)
        if canonical_s.lower() in matched_lower_skills and normalized_s_display not in seen_matched:
            matched_skills.append(normalized_s_display)
            seen_matched.add(normalized_s_display)
    matched_skills.sort()

    missing_skills = []
    seen_missing = set()
    for s in jd_skills:
        canonical_s = _get_canonical_skill(s)
        normalized_s_display = _normalize_skill_casing(canonical_s)
        if canonical_s.lower() not in resume_skills_lower and normalized_s_display not in seen_missing:
            missing_skills.append(normalized_s_display)
            seen_missing.add(normalized_s_display)
    missing_skills.sort()

    extra_skills = []
    seen_extra = set()
    for s in resume_skills: # Iterate resume skills for 'extra' list
        canonical_s = _get_canonical_skill(s)
        normalized_s_display = _normalize_skill_casing(canonical_s)
        if canonical_s.lower() not in jd_skills_lower and normalized_s_display not in seen_extra:
            extra_skills.append(normalized_s_display)
            seen_extra.add(normalized_s_display)
    extra_skills.sort()

    # Calculate score based on the count of unique matched lowercased canonical skills
    score = 0
    if len(jd_skills_lower) > 0:
        score = (len(matched_lower_skills) / len(jd_skills_lower)) * 100
    score = round(score, 2)

    print(f"Fit score calculated: {score}")
    print(f"Matched skills: {matched_skills}")
    print(f"Missing skills: {missing_skills}")
    print(f"Extra skills: {extra_skills}")
    print(f"--- Debug: calculate_job_fit_score finished ---")

    return {
        "fit_score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills
    }