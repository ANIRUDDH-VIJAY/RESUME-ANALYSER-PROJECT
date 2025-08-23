import re
import spacy
from collections import Counter
import os # Import os for path manipulation

# --- Global spaCy Model Loading ---
# Load the custom NER model globally when the module is imported
# This avoids loading it for every function call, improving performance.
nlp_custom_ner = None
try:
    # Use a relative path from the nlp_processing.py file's location
    # Assumes nlp_processing.py is in backend/utils/
    # and the model is in backend/models/ner_model/model-best/
    current_dir = os.path.dirname(__file__)
    ner_model_path = os.path.join(current_dir, '../models/ner_model/model-best')

    # Check if 'model-best' exists, otherwise try 'model-last'
    if not os.path.exists(ner_model_path):
        ner_model_path = os.path.join(current_dir, '../models/ner_model/model-last')
        print("model-best not found, attempting to load model-last.")

    if os.path.exists(ner_model_path):
        nlp_custom_ner = spacy.load(ner_model_path)
        print(f"Custom NER model loaded successfully from: {ner_model_path}")
    else:
        print(f"Custom NER model not found at: {ner_model_path}. Continuing without custom NER.")

except Exception as e:
    print(f"Error loading custom NER model for nlp_processing: {e}")
    nlp_custom_ner = None # If model fails to load, handle gracefully

# --- Comprehensive List of Known Skills (Your existing rule-based foundation) ---
# This should include a wide range of programming languages, tools, frameworks etc.
# You can expand this list significantly over time.
CANONICAL_SKILLS_MAP = {
    # Programming Languages
    "python": "Python", "py": "Python",
    "java": "Java", "c++": "C++", "c#": "C#", "c": "C",
    "javascript": "JavaScript", "js": "JavaScript", "typescript": "TypeScript",
    "go": "Go", "golang": "Go", "ruby": "Ruby", "php": "PHP",
    "swift": "Swift", "kotlin": "Kotlin", "scala": "Scala", "r": "R",
    "html": "HTML", "css": "CSS", "sql": "SQL", "bash": "Bash",
    "matlab": "MATLAB", "rust": "Rust", "perl": "Perl", "dart": "Dart",

    # Frameworks & Libraries
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "react": "React.js", "reactjs": "React.js", "angular": "Angular", "vue": "Vue.js",
    "nodejs": "Node.js", "node.js": "Node.js", "express": "Express.js",
    "spring": "Spring Boot", "spring boot": "Spring Boot",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow", "keras": "Keras",
    "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "numpy": "NumPy", "pandas": "Pandas", "matplotlib": "Matplotlib", "seaborn": "Seaborn",
    "hadoop": "Hadoop", "spark": "Spark", "airflow": "Airflow",
    "kafka": "Kafka", "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "aws": "AWS", "amazon web services": "AWS", "azure": "Azure", "gcp": "GCP", "google cloud": "GCP",
    "git": "Git", "github": "GitHub", "gitlab": "GitLab", "bitbucket": "Bitbucket",
    "jenkins": "Jenkins", "travis ci": "Travis CI", "gitlab ci": "GitLab CI",

    # Databases
    "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mongodb": "MongoDB", "mongo": "MongoDB", "sqlite": "SQLite",
    "oracle": "Oracle DB", "redis": "Redis", "cassandra": "Cassandra",

    # Concepts/Domains
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "deep learning": "Deep Learning", "dl": "Deep Learning",
    "natural language processing": "NLP", "nlp": "NLP",
    "computer vision": "Computer Vision", "cv": "Computer Vision",
    "data science": "Data Science", "data analysis": "Data Analysis",
    "big data": "Big Data", "cloud computing": "Cloud Computing",
    "devops": "DevOps", "agile": "Agile", "scrum": "Scrum",
    "api development": "API Development", "web development": "Web Development",
    "mobile development": "Mobile Development", "testing": "Testing",
    "blockchain": "Blockchain", "cybersecurity": "Cybersecurity",
    "network security": "Network Security", "data structures": "Data Structures",
    "algorithms": "Algorithms", "object-oriented programming": "OOP", "oop": "OOP",

    # Operating Systems/Tools
    "linux": "Linux", "unix": "Unix", "windows": "Windows", "excel": "Excel",
    "powerpoint": "PowerPoint", "jira": "Jira", "confluence": "Confluence",
    "tableau": "Tableau", "power bi": "Power BI", "looker": "Looker",
    "salesforce": "Salesforce",

    # Add more as needed based on common skills in resumes/JDs
}

# Compile regex patterns for faster matching (optional but good for large lists)
compiled_skill_patterns = {
    re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE): canonical_name
    for alias, canonical_name in CANONICAL_SKILLS_MAP.items()
}

# Entities that might be misclassified as skills (e.g., locations, metrics)
non_skill_entities_lower = set([
    "usa", "india", "london", "new york", "los angeles", "california", "texas",
    "master", "bachelor", "degree", "phd", "university", "college",
    "experience", "years", "months", "team", "project", "client", "customer",
    "management", "senior", "junior", "lead", "associate", "analyst", "engineer",
    "developer", "scientist", "manager", "director", "specialist",
    "rmse", "mae", "accuracy", "precision", "recall", "f1", "f1-score",
    # Add labels from your spaCy NER model here if they are NOT skills but might be extracted
    # Example: "EDUCATIONAL_REQUIREMENTS", "EXPERIENCE_LEVEL", "REQUIRED_SKILLS"
    "educational_requirements", "experience_level", "required_skills"
])

compiled_exclusion_patterns = [
    re.compile(r'\b\d{1,2}\s*(?:years?|yrs?|months?)\b', re.IGNORECASE), # e.g., "5 years"
    re.compile(r'\b(?:master\'?s|bachelor\'?s|ph\.?d\.?|associate\'?s)\b', re.IGNORECASE), # degrees
    re.compile(r'\b(?:university|college|institute)\b', re.IGNORECASE), # educational institutions
]


def _normalize_skill_casing(skill_name: str) -> str:
    """Normalizes skill casing for consistency (e.g., 'python' -> 'Python')."""
    return CANONICAL_SKILLS_MAP.get(skill_name.lower(), skill_name)

def extract_skills(text: str) -> list:
    """
    Extracts skills from text using a combination of custom NER and rule-based matching.
    """
    if not text:
        return []

    found_skills_raw = set() # Use a raw set for initial collection

    # --- 1. Extract entities using the custom spaCy NER model ---
    if nlp_custom_ner:
        doc = nlp_custom_ner(text)
        for ent in doc.ents:
            # Here, you need to decide which labels from your custom NER model
            # should be treated as "skills".
            # Based on your training, these are likely: 'EDUCATIONAL_REQUIREMENTS', 'EXPERIENCE_LEVEL', 'REQUIRED_SKILLS'.
            # If your future training adds a specific 'SKILL' label, you'd add:
            # if ent.label_ in ["SKILL", "TECHNICAL_SKILL", "REQUIRED_SKILLS"]:
            if ent.label_ in ["EDUCATIONAL_REQUIREMENTS", "EXPERIENCE_LEVEL", "REQUIRED_SKILLS"]:
                 found_skills_raw.add(ent.text.strip())
            # For now, let's also pass the *entire text* through the rule-based system
            # as the current NER model doesn't explicitly detect granular "SKILL" type entities.

    # --- 2. Extract skills using rule-based/lexicon matching (from your original logic) ---
    text_lower = text.lower()
    for pattern, canonical_name in compiled_skill_patterns.items():
        if pattern.search(text_lower):
            found_skills_raw.add(canonical_name)

    # --- 3. Filter out non-skills using exclusion lists and patterns ---
    filtered_skills = set()
    for skill in found_skills_raw:
        skill_lower = skill.lower()

        # Basic exact match exclusion
        if skill_lower in non_skill_entities_lower:
            continue

        # Exclusion using compiled regex patterns
        is_excluded = False
        for pattern in compiled_exclusion_patterns:
            if pattern.search(skill_lower):
                is_excluded = True
                break
        if is_excluded:
            continue

        # Further simple length filtering to avoid very short common words
        if len(skill_lower) <= 2:
             # Allow common short tech acronyms
            if skill_lower not in ["ci", "ml", "dl", "ai", "db", "os", "qa", "hr"]:
                continue

        # Normalize casing for consistency
        filtered_skills.add(_normalize_skill_casing(skill))

    return sorted(list(filtered_skills))


def calculate_job_fit_score(resume_skills: list, jd_skills: list) -> dict:
    """
    Calculates a job fit score based on matched, missing, and extra skills.
    Assumes skills are normalized (e.g., "Python", "AWS").
    """
    if not jd_skills:
        return {
            "fit_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "extra_skills": sorted(list(set(resume_skills)))
        }

    resume_skills_set = set(s.lower() for s in resume_skills)
    jd_skills_set = set(s.lower() for s in jd_skills)

    matched_skills_raw = resume_skills_set.intersection(jd_skills_set)
    missing_skills_raw = jd_skills_set.difference(resume_skills_set)
    extra_skills_raw = resume_skills_set.difference(jd_skills_set)

    # Convert back to original casing using the CANONICAL_SKILLS_MAP where possible
    matched_skills = sorted(list(set(_normalize_skill_casing(s) for s in matched_skills_raw)))
    missing_skills = sorted(list(set(_normalize_skill_casing(s) for s in missing_skills_raw)))
    extra_skills = sorted(list(set(_normalize_skill_casing(s) for s in extra_skills_raw)))


    # Calculate fit score (simple ratio for now)
    # You can make this more sophisticated (e.g., weighted skills, importance)
    if not jd_skills_set:
        fit_score = 0
    else:
        fit_score = (len(matched_skills_raw) / len(jd_skills_set)) * 100
        # Cap score at 100%
        fit_score = min(100, round(fit_score, 2))

    return {
        "fit_score": fit_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills
    }