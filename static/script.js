
let jdMode = 'text'; // 'text' or 'file'

// Step Navigation
function nextStep(step) {
    // Validation
    if (step === 2) {
        if (jdMode === 'text') {
            const jd = document.getElementById('job_description').value;
            if (!jd.trim()) { alert("Please enter a job description."); return; }
        } else {
            const jdFile = document.getElementById('jd_file').files;
            if (jdFile.length === 0) { alert("Please upload a Job Description PDF."); return; }
        }
    }
    if (step === 3) {
        const files = document.getElementById('resumes').files;
        if (files.length === 0) { alert("Please select resume files."); return; }
    }

    document.querySelectorAll('.step-section').forEach(s => s.classList.add('hidden'));
    document.getElementById('step' + step).classList.remove('hidden');

    document.querySelectorAll('.step-indicator').forEach(i => i.classList.remove('active'));
    document.getElementById('ind-step' + step).classList.add('active');
}

function prevStep(step) {
    document.querySelectorAll('.step-section').forEach(s => s.classList.add('hidden'));
    document.getElementById('step' + step).classList.remove('hidden');
    document.querySelectorAll('.step-indicator').forEach(i => i.classList.remove('active'));
    document.getElementById('ind-step' + step).classList.add('active');
}

// Tab Switch
function switchTab(type) {
    jdMode = type;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');

    if (type === 'text') {
        document.getElementById('jd-text-group').classList.remove('hidden');
        document.getElementById('jd-file-group').classList.add('hidden');
    } else {
        document.getElementById('jd-text-group').classList.add('hidden');
        document.getElementById('jd-file-group').classList.remove('hidden');
    }
}

// File Input Display
document.getElementById('resumes').addEventListener('change', function (e) {
    const count = e.target.files.length;
    document.querySelector('.resume-custom').textContent = count > 0 ? `${count} files selected` : 'Choose files...';
});
document.getElementById('jd_file').addEventListener('change', function (e) {
    const name = e.target.files[0]?.name;
    document.querySelector('.jd-custom').textContent = name || 'Choose JD PDF...';
});

// Slider Value Update
const thresholdInput = document.getElementById('threshold');
const thresholdValue = document.getElementById('thresholdValue');

thresholdInput.addEventListener('input', function () {
    thresholdValue.textContent = this.value; // Display decimal value
});

// Helper: section finding text
function getSectionBadge(name, found) {
    if (found) {
        return `<span class="badge success">${name} ✓</span>`;
    }
    return `<span class="badge danger">${name} ✗</span>`;
}

// Form Submission
document.getElementById('analyzeBtn').addEventListener('click', async function (e) {
    e.preventDefault();

    const form = document.getElementById('wizardForm');
    const formData = new FormData(form);

    // Handle JD Mode Logic
    if (jdMode === 'text') {
        formData.delete('jd_file');
    } else {
        formData.delete('job_description');
    }

    // Show Loading
    document.getElementById('wizardForm').classList.add('hidden');
    document.querySelector('.stepper').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');
    document.querySelector('header p').textContent = "Please wait while we process the resumes...";

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('result').classList.remove('hidden');
            document.querySelector('header').classList.add('hidden'); // Hide header to focus on results

            const tbody = document.querySelector('#resultsTable tbody');
            tbody.innerHTML = '';

            data.results.forEach(r => {
                const tr = document.createElement('tr');
                // Status Class
                let statusClass = 'status-rejected';
                if (r.status === 'Selected') statusClass = 'status-selected';
                if (r.status === 'Error') statusClass = 'status-rejected'; // Red for error too

                // Construct Sections HTML
                // We show vital ones
                let sectionsHtml = '<div class="badges">';
                sectionsHtml += getSectionBadge('Skills', r.sections.Skills);
                sectionsHtml += getSectionBadge('Projects', r.sections.Projects);
                sectionsHtml += getSectionBadge('Intern', r.sections.Internships);
                sectionsHtml += getSectionBadge('Exp', r.sections.Experience);
                sectionsHtml += '</div>';

                // Recommendation tooltip or text
                const recHtml = `<div style="font-size:0.85rem; color: #666; margin-top:4px;">${r.recommendation}</div>`;

                tr.innerHTML = `
                    <td><span class="status-pill ${statusClass}">${r.status}</span></td>
                    <td>
                        <div style="font-weight:600;">${r.filename}</div>
                        ${recHtml}
                    </td>
                    <td><div class="score-circle" style="--p:${r.score}">${Math.round(r.score)}%</div></td>
                    <td>${sectionsHtml}</td>
                `;
                tbody.appendChild(tr);
            });

            // Store for download if needed (not implemented in this simplified script but keeping placeholder if user asks)
            currentAnalysisResults = data.results;

        } else {
            alert('Error: ' + data.error);
            location.reload();
        }
    } catch (err) {
        console.error(err);
        alert('An unexpected error occurred.');
        location.reload();
    }
});

let currentAnalysisResults = [];

document.getElementById('downloadBtn').addEventListener('click', function () {
    if (!currentAnalysisResults.length) { alert("No data."); return; }
    let csv = "Status,Recommendation,Candidate,Score,Sections Found\n";
    currentAnalysisResults.forEach(r => {
        // Flatten sections for CSV
        const sectionsStr = Object.entries(r.sections)
            .filter(([k, v]) => v)
            .map(([k, v]) => k)
            .join(';');

        csv += `${r.status},"${r.recommendation}",${r.filename},${r.score},"${sectionsStr}"\n`;
    });
    const link = document.createElement("a");
    link.href = encodeURI("data:text/csv;charset=utf-8," + csv);
    link.download = "analysis_report.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});
