# AI-Powered Resume Analyzer & Job Match Scorer

**Project Status:** In Progress (Actively Developing)

An intelligent full-stack application designed to help job seekers optimize their resumes for Applicant Tracking Systems (ATS) and match their skills against job descriptions. This project leverages advanced NLP techniques to provide actionable insights.

## Key Features

-   **Resume Parsing:** Extracts key information from uploaded resumes, including contact details, skills, experience, and education.
-   **Skill Extraction & Gap Analysis:** Identifies skills present in the resume and compares them against a target job description to find keyword gaps.
-   **Job Match Scoring:** Generates a score indicating how well a resume matches a job description, helping users tailor their applications.
-   **Semantic Search:** Uses a vector database to find semantically similar skills and job roles, going beyond simple keyword matching.
-   **Interactive Dashboard:** Visualizes the analysis results using dynamic charts and graphs for an intuitive user experience.

## Tech Stack

| Category      | Technology                                           |
| ------------- | ---------------------------------------------------- |
| **Backend** | FastAPI, Python                                     |
| **Frontend** | React, Tailwind CSS                                  |
| **Database** | MongoDB (Primary Storage), Qdrant/FAISS (Vector DB) |
| **NLP** | spaCy, Hugging Face Transformers                     |
| **Dashboard** | Plotly.js                                            |

## Getting Started

### Prerequisites

-   Python 3.8+
-   Node.js & npm
-   MongoDB instance

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/ANIRUDDH-VIJAY/RESUME-ANALYSER-PROJECT.git](https://github.com/ANIRUDDH-VIJAY/RESUME-ANALYSER-PROJECT.git)
    cd RESUME-ANALYSER-PROJECT
    ```

2.  **Backend Setup (FastAPI):**
    ```sh
    # From the root directory
    cd backend 
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

3.  **Frontend Setup (React):**
    ```sh
    # From the root directory
    cd resume-analyzer-ui
    npm install
    npm start
    ```

*Note: You will need to create a `.env` file with your database connection strings and any necessary API keys. A `env.example` file should be included to show the required variables.*
