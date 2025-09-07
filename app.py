import json
import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

SUBJECTS_FILE = 'subjects.json'
# BASE_URL is still needed for ER and GT links in the template
BASE_URL = "https://dynamicpapers.com/wp-content/uploads/2015/09/"

# Helper functions (load_subjects, save_subjects) remain unchanged
def load_subjects():
    if not os.path.exists(SUBJECTS_FILE):
        return {}
    with open(SUBJECTS_FILE, 'r') as f:
        return json.load(f)

def save_subjects(subjects):
    with open(SUBJECTS_FILE, 'w') as f:
        json.dump(subjects, f, indent=2)

# --- MODIFIED FUNCTION ---
# This function now generates links to local static files instead of an external URL.
def generate_urls(subject_code, start_year, end_year, papers_dict, variants, sessions, types):
    years = list(range(int(start_year), int(end_year) + 1))
    results = {}

    for year in sorted(years, reverse=True):
        year_str = str(year)
        results[year_str] = {}
        year_short = year_str[2:]
        
        for session_code in ['w', 's', 'm']:
            if session_code not in sessions: continue
            if year == datetime.now().year and session_code == 'w' and datetime.now().month < 10: continue

            session_map = {'w': "Oct/Nov", 's': "May/June", 'm': "Feb/March"}
            session_name = f"{session_map[session_code]} {year}"
            
            results[year_str][session_name] = {
                'code': session_code,
                'short_code': f"{session_code}{year_short}",
                'papers': {}
            }

            for paper_num, paper_desc in papers_dict.items():
                paper_key = f"Paper {paper_num}: {paper_desc}"
                paper_data = results[year_str][session_name]['papers'][paper_key] = {'qp': [], 'ms': []}

                for variant_num in variants:
                    if session_code == 'm' and variant_num != '2': continue
                    paper_variant = f"{paper_num}{variant_num}"

                    # --- START OF CHANGE ---
                    
                    # Process Question Papers ('qp')
                    if 'qp' in types:
                        filename = f"{subject_code}_{session_code}{year_short}_qp_{paper_variant}.pdf"
                        # Check if the file exists locally in the static folder
                        local_file_path = os.path.join('static', 'yearly_papers', subject_code, filename)
                        if os.path.exists(local_file_path):
                            # If it exists, create the static URL path
                            static_url_path = f"/static/yearly_papers/{subject_code}/{filename}"
                            paper_data['qp'].append(static_url_path)
                    
                    # Process Mark Schemes ('ms')
                    if 'ms' in types:
                        filename = f"{subject_code}_{session_code}{year_short}_ms_{paper_variant}.pdf"
                        # Check if the file exists locally
                        local_file_path = os.path.join('static', 'yearly_papers', subject_code, filename)
                        if os.path.exists(local_file_path):
                            # If it exists, create the static URL path
                            static_url_path = f"/static/yearly_papers/{subject_code}/{filename}"
                            paper_data['ms'].append(static_url_path)
                            
                    # --- END OF CHANGE ---
    return results

# --- ROUTES (No changes needed below this line) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    subjects = load_subjects()
    
    # --- START OF FIX ---
    # Also load topics_data here so the template never gets an error
    try:
        with open('topics.json', 'r') as f:
            topics_data = json.load(f)
    except FileNotFoundError:
        topics_data = {}
    # --- END OF FIX ---

    if request.method == 'POST':
        year_range = request.form.get('year_range', '2020-2025').split('-')
        start_year, end_year = year_range[0], year_range[1]
        variants = ['1', '2', '3'] if request.form.get('variants_all') else request.form.getlist('variants')
        sessions = ['w', 's', 'm'] if request.form.get('sessions_all') else request.form.getlist('sessions')
        
        all_results = {}
        for code, data in subjects.items():
            all_results[code] = {
                "name": data["name"],
                "subject_code": code,
                "base_url": BASE_URL,
                "links": generate_urls(code, start_year, end_year, data["papers"], variants, sessions, ['qp', 'ms'])
            }
        # Add topical_subjects to the render_template call
        return render_template('index.html', results=all_results, submitted=True, subjects=subjects, active_view='yearly', topical_subjects=topics_data)

    # Add topical_subjects to this render_template call as well
    return render_template('index.html', results=None, submitted=False, subjects=subjects, active_view='yearly', topical_subjects=topics_data)

@app.route('/topical')
def topical():
    subjects = load_subjects()
    try:
        with open('topics.json', 'r') as f:
            topics_data = json.load(f)
    except FileNotFoundError:
        topics_data = {}

    # We now send ALL topical data to the template. JavaScript will handle showing/hiding.
    return render_template(
        'index.html', 
        subjects=subjects, 
        active_view='topical',
        topical_subjects=topics_data, # This now contains ALL subjects' topical data
        submitted=False
    )
@app.route('/add_subject', methods=['POST'])
def add_subject():
    subjects = load_subjects()
    
    code = request.form['code']
    name = request.form['name']
    papers_str = request.form['papers']
    
    papers_dict = {}
    for part in papers_str.split(','):
        if ':' in part:
            num, desc = part.split(':', 1)
            papers_dict[num.strip()] = desc.strip()
            
    if code and name and papers_dict:
        subjects[code] = {"name": name, "papers": papers_dict}
        save_subjects(subjects)
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)