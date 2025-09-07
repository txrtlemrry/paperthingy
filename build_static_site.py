import os
import json
import shutil
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURATION ---
# All paths should be correct for your 'localPaperFinder' project.

# Base directory of your local web app
APP_DIR = "D:/localPaperFinder(MY WEB APP)"

# The directory where the final static site will be built
BUILD_DIR = os.path.join(APP_DIR, "build")


# --- HELPER FUNCTIONS ---

def load_json_file(path):
    """Safely loads a JSON file from a given path."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {path}: {e}")
        return {}

def generate_static_urls(subject_code, papers_dict):
    """
    Scans the static/yearly_papers directory to find all available papers
    for a subject and organizes them by year and session.
    """
    # Define a wide, fixed range of years to search for papers
    years = list(range(2015, 2026))
    results = {}
    subject_yearly_path = os.path.join(APP_DIR, 'static', 'yearly_papers', subject_code)

    if not os.path.isdir(subject_yearly_path):
        return {} # Return empty if no yearly papers folder exists for this subject

    for year in sorted(years, reverse=True):
        year_str = str(year)
        year_short = year_str[2:]
        
        yearly_sessions = {}
        
        for session_code in ['w', 's', 'm']:
            session_map = {'w': "Oct/Nov", 's': "May/June", 'm': "Feb/March"}
            session_name = f"{session_map[session_code]} {year}"
            
            session_papers = {}
            has_papers_in_session = False

            for paper_num, paper_desc in papers_dict.items():
                paper_key = f"Paper {paper_num}: {paper_desc}"
                paper_data = {'qp': [], 'ms': []}

                for variant_num in ['1', '2', '3']:
                    if session_code == 'm' and variant_num != '2':
                        continue
                    paper_variant = f"{paper_num}{variant_num}"

                    # Check for Question Paper
                    qp_filename = f"{subject_code}_{session_code}{year_short}_qp_{paper_variant}.pdf"
                    if os.path.exists(os.path.join(subject_yearly_path, qp_filename)):
                        paper_data['qp'].append(f"static/yearly_papers/{subject_code}/{qp_filename}")
                        has_papers_in_session = True
                    
                    # Check for Mark Scheme
                    ms_filename = f"{subject_code}_{session_code}{year_short}_ms_{paper_variant}.pdf"
                    if os.path.exists(os.path.join(subject_yearly_path, ms_filename)):
                        paper_data['ms'].append(f"static/yearly_papers/{subject_code}/{ms_filename}")
                        has_papers_in_session = True
                
                if paper_data['qp'] or paper_data['ms']:
                    session_papers[paper_key] = paper_data

            if has_papers_in_session:
                yearly_sessions[session_name] = {
                    'code': session_code,
                    'short_code': f"{session_code}{year_short}",
                    'papers': session_papers
                }

        if yearly_sessions:
            results[year_str] = yearly_sessions
            
    return results


# --- MAIN BUILD PROCESS ---

def main():
    """The main function to orchestrate the entire static site build."""
    print("Starting static site build process...")

    # 1. Clean up old build directory and create a new one
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    print(f"Cleaned and created build directory: {BUILD_DIR}")

    # 2. Set up Jinja2 environment to find the template
    env = Environment(loader=FileSystemLoader(os.path.join(APP_DIR, 'templates')))
    template = env.get_template('index.html')

    # 3. Load all necessary data from your JSON files
    subjects = load_json_file(os.path.join(APP_DIR, 'subjects.json'))
    topical_subjects = load_json_file(os.path.join(APP_DIR, 'topics.json'))
    
    # --- 4. Generate the Yearly Papers Page (index.html) ---
    print("Generating yearly papers page (index.html)...")
    
    all_results = {}
    for code, data in subjects.items():
        all_results[code] = {
            "name": data["name"],
            "subject_code": code,
            "base_url": "https://dynamicpapers.com/wp-content/uploads/2015/09/", 
            "links": generate_static_urls(code, data.get("papers", {}))
        }
    
    # Render the template with the data for the yearly view
    yearly_html_output = template.render(
        results=all_results,
        submitted=True,  # Always show results in the static version
        subjects=subjects,
        active_view='yearly',
        topical_subjects=topical_subjects
    )
    
    # Write the rendered HTML to a file
    with open(os.path.join(BUILD_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(yearly_html_output)
    print("  -> index.html has been generated.")

    # --- 5. Generate the Topical Papers Page (topical.html) ---
    print("Generating topical papers page (topical.html)...")

    # Render the same template, but with data for the topical view
    topical_html_output = template.render(
        subjects=subjects,
        active_view='topical',
        topical_subjects=topical_subjects,
        submitted=False
    )

    # Write the rendered HTML to a different file
    with open(os.path.join(BUILD_DIR, 'topical.html'), 'w', encoding='utf-8') as f:
        f.write(topical_html_output)
    print("  -> topical.html has been generated.")

    # --- 6. Copy all static assets (CSS, PDFs, etc.) to the build folder ---
    print("Copying all static assets...")
    source_static_dir = os.path.join(APP_DIR, 'static')
    destination_static_dir = os.path.join(BUILD_DIR, 'static')
    
    if os.path.exists(source_static_dir):
        shutil.copytree(source_static_dir, destination_static_dir)
        print(f"  -> Successfully copied static assets.")
    else:
        print(f"  -> WARNING: Static directory not found at '{source_static_dir}'")

    print("\nBUILD COMPLETE!")
    print(f"Your static site is ready in the '{BUILD_DIR}' folder.")
    print(f"You can now open '{os.path.join(BUILD_DIR, 'index.html')}' in your browser.")


if __name__ == "__main__":
    main()