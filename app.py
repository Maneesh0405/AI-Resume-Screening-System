from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

app = Flask(__name__)

# Route: Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Helper: Extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Helper: Preprocess Text
def preprocess_text(text):
    text = text.lower()
    # Remove special characters and extra spaces
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

# Helper: Check for Sections
def check_sections(text):
    text_lower = text.lower()
    sections = {
        'Skills': bool(re.search(r'\b(skills|technologies|proficiencies)\b', text_lower)),
        'Projects': bool(re.search(r'\b(projects|academic projects)\b', text_lower)),
        'Internships': bool(re.search(r'\b(internship|intern|training)\b', text_lower)),
        'Experience': bool(re.search(r'\b(experience|work history|employment|profesional experience)\b', text_lower)),
        'Achievements': bool(re.search(r'\b(achievements|awards|accomplishments)\b', text_lower)),
        'Certifications': bool(re.search(r'\b(certifications|certificates|courses)\b', text_lower))
    }
    return sections

# Route: Analyze Resume
@app.route('/analyze', methods=['POST'])
def analyze():
    # Check for Resumes
    if 'resumes' not in request.files:
        return jsonify({'error': 'Missing resumes'}), 400
    
    files = request.files.getlist('resumes')
    # Threshold is now expected to be 0-100 from frontend
    try:
        threshold = float(request.form.get('threshold', 0.5))
    except ValueError:
        threshold = 0.5

    # Check for JD (File OR Text)
    job_description = ""
    if 'jd_file' in request.files and request.files['jd_file'].filename != '':
        job_description = extract_text_from_pdf(request.files['jd_file'])
    elif 'job_description' in request.form and request.form['job_description'].strip() != '':
        job_description = request.form['job_description']
    else:
        return jsonify({'error': 'Missing Job Description (Upload PDF or Paste Text)'}), 400

    if not job_description:
         return jsonify({'error': 'Could not extract text from Job Description'}), 400
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected resume file'}), 400

    results = []

    try:
        # Preprocess JD
        clean_jd = preprocess_text(job_description)
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            vectorizer.fit([clean_jd])
            jd_feature_names = vectorizer.get_feature_names_out()
        except ValueError:
             # Handle case where JD has valid text but no valid words after stopword removal
             jd_feature_names = []
        
        tfidf = TfidfVectorizer()

        for file in files:
            if file.filename == '': continue
            
            # 1. Extract & Preprocess
            resume_text = extract_text_from_pdf(file)
            clean_resume = preprocess_text(resume_text)
            
            # Check for unreadable/image PDF
            if len(clean_resume) < 50:
                results.append({
                    'filename': file.filename,
                    'score': 0,
                    'status': "Error",
                    'recommendation': "Unreadable PDF (Image-based or Encrypted)",
                    'sections': {'Skills': False, 'Projects': False, 'Achievements': False, 'Certifications': False, 'Internships': False, 'Experience': False},
                    'matched_keywords': [],
                    'missing_keywords': [],
                    'debug_lengths': {'resume': len(clean_resume), 'jd': len(clean_jd)}
                })
                continue

            # 2. Score
            match_percentage = 0
            try:
                text_list = [clean_resume, clean_jd]
                count_matrix = tfidf.fit_transform(text_list)
                # match_percentage is 0-100
                match_percentage = cosine_similarity(count_matrix)[0][1] * 100
            except ValueError:
                match_percentage = 0
            
            # 3. Section Analysis
            sections_found = check_sections(resume_text) # Pass original text for regex
            
            # 5. Keywords Analysis
            resume_words = set(clean_resume.split())
            matched_keywords = [word for word in jd_feature_names if word in resume_words]
            missing_keywords = [word for word in jd_feature_names if word not in resume_words]
            
            # 6. Status Determination
            # Requirement: 
            # - Check Internship and Experience
            # - Threshold Value
            
            # Logic:
            # - Must meet Threshold (converted to percentage for comparison)
            # - Must have Experience OR Internships (Practical exposure)
            
            has_practical_exp = sections_found['Internships'] or sections_found['Experience']
            meets_threshold = match_percentage >= (threshold * 100)
            
            status = "Rejected"
            recommendation = "Low fit"

            if meets_threshold:
                status = "Selected"
                if not has_practical_exp:
                    recommendation = "Good Score (No Internship/Experience)"
                else:
                    recommendation = "Strong Candidate"
            else:
                status = "Rejected"
                recommendation = "Below Threshold"

            results.append({
                'filename': file.filename,
                'score': round(match_percentage, 2), # Already percentage
                'status': status,
                'recommendation': recommendation,
                'sections': sections_found,
                'matched_keywords': matched_keywords[:10],
                'missing_keywords': missing_keywords[:5],
                'debug_lengths': {'resume': len(clean_resume), 'jd': len(clean_jd)}
            })
        
        # Sort: Selected first, then by score
        results.sort(key=lambda x: (x['status'] == 'Rejected', -x['score']))

        return jsonify({
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
