"""
Data loading script for AcademiaMatch
Loads researcher data from Excel files into the database
"""
import pandas as pd
from app import app, db, Researcher
import os

def clean_text(text):
    """Clean and normalize text data"""
    if pd.isna(text) or text is None:
        return ""
    return str(text).strip()

def load_external_researchers(file_path):
    """Load external researchers from Excel file"""
    if not os.path.exists(file_path):
        print(f"⚠ External researchers file not found: {file_path}")
        return 0
    
    print(f"Loading external researchers from: {file_path}")
    df = pd.read_excel(file_path)
    
    count = 0
    for _, row in df.iterrows():
        email = clean_text(row.get('Email Address', ''))
        if not email:
            continue
        
        # Check if researcher already exists
        existing = Researcher.query.filter_by(email=email).first()
        if existing:
            print(f"  ⏭ Skipping duplicate: {email}")
            continue
        
        researcher = Researcher(
            name=clean_text(row.get('Your Name', '')),
            email=email,
            organization=clean_text(row.get('Your Orgnization', '')),
            researcher_type='external',
            organization_focus=clean_text(row.get(
                'What is your organization's primary area of focus or industry sector?Please list key words or phrases (e.g., renewable energy, healthcare, logistics, education technology)',
                ''
            )),
            challenge_description=clean_text(row.get(
                'Please describe a challenge or business goal your organization is currently facing that could benefit from academic collaboration.\n(e.g., improving supply chain efficiency, developing sustainable mate',
                ''
            )),
            expertise_sought=clean_text(row.get(
                'What type of expertise or research support are you seeking to address this challenge?(e.g., machine learning, food security, sustainable packaging, behavioral economics)',
                ''
            )),
            lab_tours_interested=clean_text(row.get(
                'Which lab tour(s) would you be interested in joining during our event? (Tour selection will be finalized at the event. As tour lengths will vary, it is anticipated that participants will have time to ',
                ''
            ))
        )
        
        db.session.add(researcher)
        count += 1
    
    db.session.commit()
    print(f"✓ Loaded {count} external researchers")
    return count

def load_internal_researchers_file1(file_path):
    """Load internal researchers from first Excel file (survey responses)"""
    if not os.path.exists(file_path):
        print(f"⚠ Internal researchers file 1 not found: {file_path}")
        return 0
    
    print(f"Loading internal researchers from: {file_path}")
    df = pd.read_excel(file_path)
    
    count = 0
    for _, row in df.iterrows():
        email = clean_text(row.get('Email Address', ''))
        if not email:
            continue
        
        # Check if researcher already exists
        existing = Researcher.query.filter_by(email=email).first()
        if existing:
            print(f"  ⏭ Skipping duplicate: {email}")
            continue
        
        researcher = Researcher(
            name=clean_text(row.get('Your Name', '')),
            email=email,
            organization='Humber Polytechnic',
            researcher_type='internal',
            faculty_department=clean_text(row.get('Your Faculty/Department', '')),
            primary_areas=clean_text(row.get(
                'What are your primary areas of research or expertise?Please list key words or phrases (e.g., machine learning, food security, sustainable packaging, behavioral economics).',
                ''
            )),
            experience_summary=clean_text(row.get(
                'Please provide a brief summary of your experience or capabilities relevant to collaborative research?(e.g., summary of technical skills, related past work, specialized expertise)',
                ''
            )),
            sectors_interested=clean_text(row.get(
                'What sectors or societal challenges are you most interested in addressing through research?(e.g., healthcare innovation, climate resilience, advanced manufacturing, education equity)',
                ''
            ))
        )
        
        db.session.add(researcher)
        count += 1
    
    db.session.commit()
    print(f"✓ Loaded {count} internal researchers from file 1")
    return count

def load_internal_researchers_file2(file_path):
    """Load additional internal researchers from second Excel file"""
    if not os.path.exists(file_path):
        print(f"⚠ Internal researchers file 2 not found: {file_path}")
        return 0
    
    print(f"Loading additional internal researchers from: {file_path}")
    df = pd.read_excel(file_path)
    
    count = 0
    for _, row in df.iterrows():
        email = clean_text(row.get('Humber Email', ''))
        if not email:
            continue
        
        # Check if researcher already exists
        existing = Researcher.query.filter_by(email=email).first()
        if existing:
            print(f"  ⏭ Skipping duplicate: {email}")
            continue
        
        # Combine job title and status for experience summary
        job_title = clean_text(row.get('Job Title', ''))
        job_status = clean_text(row.get('Job Status', ''))
        experience = f"{job_title} ({job_status})" if job_title and job_status else job_title
        
        researcher = Researcher(
            name=clean_text(row.get('Researcher Full Name', '')),
            email=email,
            organization='Humber Polytechnic',
            researcher_type='internal',
            faculty_department=clean_text(row.get('Faculty / Department', '')),
            primary_areas=clean_text(row.get('Research Interest Keywords', '')),
            experience_summary=experience,
            sectors_interested=''  # Not available in this file
        )
        
        db.session.add(researcher)
        count += 1
    
    db.session.commit()
    print(f"✓ Loaded {count} internal researchers from file 2")
    return count

def load_all_data():
    """Load all researcher data from Excel files"""
    print("\n" + "="*60)
    print("Loading Researcher Data into Database")
    print("="*60 + "\n")
    
    with app.app_context():
        # Load external researchers
        external_count = load_external_researchers(
            'ResearchUnplugged_PartneringSessions!_ExternalResearcher.xlsx'
        )
        
        # Load internal researchers from both files
        internal_count1 = load_internal_researchers_file1(
            'ResearchUnplugged_PartneringSessions!1_InternalHumber.xlsx'
        )
        
        internal_count2 = load_internal_researchers_file2(
            'AdditonalInternalHumberResearcher.xlsx'
        )
        
        total_internal = internal_count1 + internal_count2
        total = external_count + total_internal
        
        print("\n" + "="*60)
        print("Data Loading Summary:")
        print(f"  External Researchers: {external_count}")
        print(f"  Internal Researchers: {total_internal} ({internal_count1} + {internal_count2})")
        print(f"  Total Loaded: {total}")
        print("="*60 + "\n")
        
        return total

if __name__ == '__main__':
    load_all_data()
