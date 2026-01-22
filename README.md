# CV Fit Resume Analyzer

CV Fit is an advanced candidate screening tool that matches resumes against a job description (JD) using Natural Language Processing (NLP). It calculates a similarity score based on content match and identified key sections.

## Features

-   **Resume Analysis**: Upload multiple PDF resumes to analyze against a Job Description.
-   **Job Description Parsing**: Support for pasting JD text or uploading a JD PDF.
-   **Smart Scoring**: Uses TF-IDF and Cosine Similarity to calculate a match percentage (0-100%).
-   **Section Detection**: Automatically detects key resume sections:
    -   Skills
    -   Projects
    -   Internships
    -   Experience
    -   Achievements
    -   Certifications
-   **Keyword Matching**: Identifies matched and missing keywords from the JD.
-   **Status & Recommendation**: Automatically rejects/selects candidates based on a configurable threshold and practical experience requirements.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <project-directory>
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Application**:
    ```bash
    python app.py
    ```

2.  **Access the Interface**:
    Open your browser and navigate to `http://127.0.0.1:5000`.

3.  **Perform Analysis**:
    -   **Step 1**: Enter the Job Description (Text or PDF).
    -   **Step 2**: Upload Candidate Resumes (PDF).
    -   **Step 3**: Set the Match Threshold (default 0.5) and click "Run Analysis".

## Requirements

-   Flask
-   pypdf
-   scikit-learn
-   nltk
