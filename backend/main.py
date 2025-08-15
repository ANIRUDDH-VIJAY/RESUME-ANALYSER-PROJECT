# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import docx2txt
import PyPDF2
from io import BytesIO
import fitz # PyMuPDF
import re
import os
import joblib
import spacy # Import spacy for the NER model

# Import your nlp_processing functions
from backend.utils.nlp_processing import extract_skills, calculate_job_fit_score

# --- Model Loading for Job Role Classifier ---
job_role_vectorizer = None
job_role_model = None
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.joblib')
    MODEL_PATH = os.path.join(MODELS_DIR, 'job_role_classifier_model.joblib')

    job_role_vectorizer = joblib.load(VECTORIZER_PATH)
    job_role_model = joblib.load(MODEL_PATH)
    print("Job Role Classifier model and vectorizer loaded successfully!")
except Exception as e:
    print(f"Error loading job role classifier models: {e}")
    print("Please ensure you have run the Jupyter Notebook to save the models to backend/models/.")
    job_role_vectorizer = None
    job_role_model = None

# --- Custom NER Model Loading for Job Description Parsing ---
# We will load a pre-trained large spaCy model instead of custom-trained
jd_ner_model = None
try:
    # Attempt to load the large English model first
    jd_ner_model = spacy.load("en_core_web_lg")
    print("Pre-trained 'en_core_web_lg' spaCy model loaded successfully for JD parsing!")
except OSError:
    print("SpaCy model 'en_core_web_lg' not found. Attempting to download...")
    try:
        spacy.cli.download("en_core_web_lg")
        jd_ner_model = spacy.load("en_core_web_lg")
        print("Downloaded and loaded 'en_core_web_lg' for JD parsing!")
    except Exception as download_e:
        print(f"Error downloading 'en_core_web_lg': {download_e}")
        print("Falling back to 'en_core_web_sm' for JD parsing.")
        try:
            jd_ner_model = spacy.load("en_core_web_sm")
            print("Loaded 'en_core_web_sm' for JD parsing.")
        except OSError:
            print("Error: Neither 'en_core_web_lg' nor 'en_core_web_sm' found. JD parsing will be limited.")
            jd_ner_model = None
except Exception as e:
    print(f"An unexpected error occurred loading spaCy model: {e}")
    jd_ner_model = None


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Utility functions for text extraction from files
async def _extract_text_from_file(file: UploadFile) -> str:
    file_content = await file.read()
    if file.content_type == "application/pdf":
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing PDF: {e}")
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            text = docx2txt.process(BytesIO(file_content))
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing DOCX: {e}")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type.")


@app.get("/test")
async def read_root():
    return {"message": "Backend is working!"}


@app.post("/extract-resume-data/")
async def extract_resume_data_endpoint(resume_file: UploadFile = File(...)):
    """
    Extracts structured data (personal info, education, experience, skills) from a resume.
    """
    try:
        resume_text = await _extract_text_from_file(resume_file)
        
        # Use your nlp_processing.py to extract skills
        extracted_skills_list = extract_skills(resume_text)

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text)
        phone_match = re.search(r"(\+\d{1,3})?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", resume_text)

        resume_info = {
            "filename": resume_file.filename,
            "email": email_match.group(0) if email_match else "Not Found",
            "phone": phone_match.group(0) if phone_match else "Not Found",
            "extracted_skills": extracted_skills_list,
            "education": ["Education parsing not yet fully implemented for this endpoint"],
            "experience": ["Experience parsing not yet fully implemented for this endpoint"],
            "full_resume_text": resume_text
        }

        return JSONResponse(content={"resume_info": resume_info})

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error during resume data extraction: {e}")


@app.post("/compare-resume-and-jd/")
async def compare_resume_and_jd(resume_file: UploadFile = File(...), jd_file: UploadFile = File(...)):
    """
    Compares a resume against a job description, extracts skills, and calculates a fit score.
    """
    try:
        # 1. Extract text from uploaded files
        resume_text = await _extract_text_from_file(resume_file)
        jd_text = await _extract_text_from_file(jd_file)

        # 2. Extract skills from resume using nlp_processing.py (rule-based)
        resume_skills = extract_skills(resume_text)

        # 3. Use pre-trained spaCy model for Job Description parsing (for display purposes)
        # This will extract general entities, not your custom ones directly
        parsed_jd_details_from_ner = {
            "required_skills_ner": [],
            "experience_level_ner": "",
            "educational_requirements_ner": ""
        }
        
        if jd_ner_model:
            doc = jd_ner_model(jd_text)
            
            # --- DEBUG PRINTS FOR PRE-TRAINED NER MODEL START ---
            print("\n--- Debug: Pre-trained SpaCy Model Entities Detected in JD ---")
            if doc.ents:
                for ent in doc.ents:
                    print(f"  Entity: '{ent.text}' | Label: '{ent.label_}' | Span: [{ent.start_char}:{ent.end_char}]")
                    # Attempt to map general NER entities to your desired categories
                    # This is a heuristic and will not be perfect but provides some structure
                    if ent.label_ in ['SKILL', 'LANGUAGE', 'PRODUCT', 'ORG', 'NORP', 'FAC', 'GPE', 'PERSON', 'LOC']: # Common relevant labels for skills/tech
                        parsed_jd_details_from_ner["required_skills_ner"].append(ent.text)
                    elif ent.label_ in ['DATE', 'CARDINAL', 'QUANTITY']: # Heuristic for experience
                        # Check for terms commonly associated with experience levels
                        if 'year' in ent.text.lower() or 'experience' in ent.text.lower() or re.search(r'\d+\+', ent.text):
                             if not parsed_jd_details_from_ner["experience_level_ner"]: # Only take the first relevant one
                                parsed_jd_details_from_ner["experience_level_ner"] = ent.text
                    elif ent.label_ in ['ORG', 'EDU', 'GPE']: # Heuristic for education
                         # Check for terms commonly associated with education
                         if 'university' in ent.text.lower() or 'college' in ent.text.lower() or 'degree' in ent.text.lower() or 'ph.d' in ent.text.lower() or 'bachelor' in ent.text.lower() or 'master' in ent.text.lower():
                            if not parsed_jd_details_from_ner["educational_requirements_ner"]: # Only take the first relevant one
                                parsed_jd_details_from_ner["educational_requirements_ner"] = ent.text
            else:
                print("  No entities detected by pre-trained spaCy model for this JD.")
            print("--- Debug: Pre-trained SpaCy Model Entities Detected End ---\n")
            # --- DEBUG PRINTS FOR PRE-TRAINED NER MODEL END ---

            # Deduplicate skills for display
            parsed_jd_details_from_ner["required_skills_ner"] = list(set(parsed_jd_details_from_ner["required_skills_ner"]))


            # CRITICAL: Use rule-based skills for comparison to maintain accuracy for now
            jd_skills_for_comparison = extract_skills(jd_text) 
            print("Note: Using rule-based skills for JD comparison to maintain accuracy.")

        else:
            # Fallback to rule-based skill extraction for JD if NO spaCy model is loaded
            jd_skills_for_comparison = extract_skills(jd_text)
            print("Warning: No spaCy model loaded for JD parsing, falling back to rule-based JD skill extraction.")

        # 4. Calculate job fit score using the reliable extracted skills
        comparison_results = calculate_job_fit_score(resume_skills, jd_skills_for_comparison)
        
        # Prepare resume_info for the frontend response
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text)
        phone_match = re.search(r"(\+\d{1,3})?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", resume_text)

        response_resume_info = {
            "filename": resume_file.filename,
            "email": email_match.group(0) if email_match else "Not Found",
            "phone": phone_match.group(0) if phone_match else "Not Found",
            "education": ["Education parsing not yet fully implemented for display"],
            "experience": ["Experience parsing not yet fully implemented for display"],
            "full_resume_text": resume_text
        }

        # Return the newly extracted JD entities for display
        return JSONResponse(content={
            "resume_info": response_resume_info,
            "jd_extracted_skills": jd_skills_for_comparison, # This is the rule-based list for the fit score display
            "comparison_results": comparison_results,
            "parsed_jd_details": parsed_jd_details_from_ner # NEW: Now from the pre-trained spaCy NER model
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error during comparison: {e}")


@app.post("/predict-job-role/")
async def predict_job_role(request_data: dict):
    """
    Predicts the job role based on the full resume text.
    """
    if not job_role_model or not job_role_vectorizer:
        raise HTTPException(status_code=500, detail="Job role prediction model not loaded. Please check backend logs.")
    
    resume_full_text = request_data.get('resume_full_text', '')
    if not resume_full_text:
        raise HTTPException(status_code=400, detail="No full resume text provided for job role prediction.")

    extracted_resume_skills = extract_skills(resume_full_text)
    processed_skills_string = " ".join(extracted_resume_skills)

    transformed_skills = job_role_vectorizer.transform([processed_skills_string])
    predicted_role = job_role_model.predict(transformed_skills)[0]
    
    return {"predicted_job_role": predicted_role}