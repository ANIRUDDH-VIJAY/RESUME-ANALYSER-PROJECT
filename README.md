# AI-Powered Resume Analyzer & Job Match Scorer

**Project Status:** In Progress (Actively Developing)

An intelligent full-stack application designed to help job seekers optimize their resumes for Applicant Tracking Systems (ATS) and match their skills against job descriptions. This project leverages advanced NLP techniques to provide actionable insights.

## Key Features

-   [cite_start]**Resume Parsing:** Extracts key information from uploaded resumes, including contact details, skills, experience, and education[cite: 110].
-   [cite_start]**Skill Extraction & Gap Analysis:** Identifies skills present in the resume and compares them against a target job description to find keyword gaps[cite: 110].
-   **Job Match Scoring:** Generates a score indicating how well a resume matches a job description, helping users tailor their applications.
-   [cite_start]**Semantic Search:** Uses a vector database to find semantically similar skills and job roles, going beyond simple keyword matching[cite: 111].
-   [cite_start]**Interactive Dashboard:** Visualizes the analysis results using dynamic charts and graphs for an intuitive user experience[cite: 111].

## Tech Stack

| Category      | Technology                                           |
| ------------- | ---------------------------------------------------- |
| **Backend** | FastAPI, Python                                     |
| **Frontend** | React, Tailwind CSS                                  |
| **Database** | [cite_start]MongoDB (Primary Storage), Qdrant/FAISS (Vector DB) [cite: 109, 111] |
| [cite_start]**NLP** | spaCy, Hugging Face Transformers                     [cite: 110] |
| **Dashboard** | [cite_start]Plotly.js                                            [cite: 111] |

## Getting Started

### Prerequisites

-   Python 3.8+
-   Node.js & npm
-   MongoDB instance

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/YOUR-USERNAME/RESUME-ANALYSER-PROJECT.git](https://github.com/YOUR-USERNAME/RESUME-ANALYSER-PROJECT.git)
    cd RESUME-ANALYSER-PROJECT
    ```

2.  **Backend Setup (FastAPI):**
    ```sh
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```

3.  **Frontend Setup (React):**
    ```sh
    cd frontend
    npm install
    npm start
    ```

*Note: You will need to create a `.env` file with your database connection strings and any necessary API keys. A `env.example` file should be included to show the required variables.*
