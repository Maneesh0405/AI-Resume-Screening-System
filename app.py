from flask import Flask, render_template, request, jsonify
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text


def preprocess_text(text):
    text = text.lower()

    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text


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


@app.route('/analyze', methods=['POST'])
def analyze():

    if 'resumes' not in request.files:
        return jsonify({'error': 'Missing resumes'}), 400
    
    files = request.files.getlist('resumes')

    try:
        threshold = float(request.form.get('threshold', 0.5))
    except ValueError:
        threshold = 0.5


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

        clean_jd = preprocess_text(job_description)
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            vectorizer.fit([clean_jd])
            jd_feature_names = vectorizer.get_feature_names_out()
        except ValueError:
             jd_feature_names = []
        
        tfidf = TfidfVectorizer()

        for file in files:
            if file.filename == '': continue
            

            resume_text = extract_text_from_pdf(file)
            clean_resume = preprocess_text(resume_text)
            

            if len(clean_resume) < 50:
                results.append({
                    'filename': file.filename,
                    'score': 0,
                    'status': "Error",
                    'recommendation': "Unreadable PDF (Image-based or Encrypted)",
                    'sections': {'Skills': False, 'Projects': False, 'Achievements': False, 'Certifications': False, 'Internships': False, 'Experience': False},
                    'matched_keywords': [],
                    'missing_keywords': [],

                })
                continue


            match_percentage = 0
            try:
                text_list = [clean_resume, clean_jd]
                count_matrix = tfidf.fit_transform(text_list)

                match_percentage = cosine_similarity(count_matrix)[0][1] * 100
            except ValueError:
                match_percentage = 0
            
            sections_found = check_sections(resume_text)
            

            resume_words = set(clean_resume.split())
            matched_keywords = [word for word in jd_feature_names if word in resume_words]
            missing_keywords = [word for word in jd_feature_names if word not in resume_words]
            

            
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
                'score': round(match_percentage, 2),
                'status': status,
                'recommendation': recommendation,
                'sections': sections_found,
                'matched_keywords': matched_keywords[:10],
                'missing_keywords': missing_keywords[:5],

            })
        

        results.sort(key=lambda x: (x['status'] == 'Rejected', -x['score']))

        return jsonify({
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
