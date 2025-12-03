"""
Load researcher data from Excel files into the database.
This script loads data from 3 Excel files:
1. External researchers
2. Internal researchers (survey responses)
3. Additional internal researchers
"""

import pandas as pd
from app import app, db, Researcher

def clean_text(value):
    """Clean and normalize text values from Excel"""
    if pd.isna(value) or value is None:
        return ''
    return str(value).strip()

def load_all_data():
    """Load all Excel files into the database"""
    
    print("\n" + "="*60)
    print("Loading Researcher Data into Database")
    print("="*60 + "\n")
    
    total_loaded = 0
    
    with app.app_context():
        # File 1: External Researchers
        try:
            file1 = 'ResearchUnplugged_PartneringSessions!_ExternalResearcher.xlsx'
            print(f"Loading external researchers from: {file1}")
            
            df = pd.read_excel(file1)
            loaded = 0
            
            for _, row in df.iterrows():
                email = clean_text(row.get('Email Address', ''))
                name = clean_text(row.get('Your Name', ''))
                
                if not email or not name:
                    continue
                
                # Check if already exists
                if Researcher.query.filter_by(email=email).first():
                    print(f"  ⏭ Skipping duplicate: {email}")
                    continue
                
                researcher = Researcher(
                    name=name,
                    email=email,
                    organization=clean_text(row.get('Your Orgnization', '')),
                    researcher_type='external',
                    organization_focus=clean_text(row.get('What is your organization\'s primary area of focus or industry sector?Please list key words or phrases (e.g., renewable energy, healthcare, logistics, education technology)', '')),
                    challenge_description=clean_text(row.get('Please describe a challenge or business goal your organization is currently facing that could benefit from academic collaboration.\n(e.g., improving supply chain efficiency, developing sustainable mate', '')),
                    expertise_sought=clean_text(row.get('What type of expertise or research support are you seeking to address this challenge?(e.g., machine learning, food security, sustainable packaging, behavioral economics)', '')),
                    lab_tours_interested=clean_text(row.get('Which lab tour(s) would you be interested in joining during our event? (Tour selection will be finalized at the event. As tour lengths will vary, it is anticipated that participants will have time to ', ''))
                )
                
                db.session.add(researcher)
                loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {loaded} external researchers\n")
            total_loaded += loaded
            
        except FileNotFoundError:
            print(f"✗ File not found: {file1}\n")
        except Exception as e:
            print(f"✗ Error loading external researchers: {str(e)}\n")
            db.session.rollback()
        
        # File 2: Internal Researchers (Survey)
        try:
            file2 = 'ResearchUnplugged_PartneringSessions!1_InternalHumber.xlsx'
            print(f"Loading internal researchers from: {file2}")
            
            df = pd.read_excel(file2)
            loaded = 0
            
            for _, row in df.iterrows():
                email = clean_text(row.get('Email Address', ''))
                name = clean_text(row.get('Your Name', ''))
                
                if not email or not name:
                    continue
                
                # Check if already exists
                if Researcher.query.filter_by(email=email).first():
                    print(f"  ⏭ Skipping duplicate: {email}")
                    continue
                
                researcher = Researcher(
                    name=name,
                    email=email,
                    organization='Humber Polytechnic',
                    researcher_type='internal',
                    faculty_department=clean_text(row.get('Faculty/Department', '')),
                    primary_areas=clean_text(row.get('What are your primary research areas or areas of expertise? Please list key words or phrases (e.g., artificial intelligence, sustainable design, healthcare innovation).', '')),
                    experience_summary=clean_text(row.get('Briefly describe your research experience or expertise (e.g., publications, projects, industry collaborations).', '')),
                    sectors_interested=clean_text(row.get('Are there specific industry sectors or external organizations you\'re interested in collaborating with? (e.g., healthcare, technology, manufacturing)', ''))
                )
                
                db.session.add(researcher)
                loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {loaded} internal researchers from file 1\n")
            total_loaded += loaded
            
        except FileNotFoundError:
            print(f"✗ File not found: {file2}\n")
        except Exception as e:
            print(f"✗ Error loading internal researchers (file 1): {str(e)}\n")
            db.session.rollback()
        
        # File 3: Additional Internal Researchers
        try:
            file3 = 'AdditonalInternalHumberResearcher.xlsx'
            print(f"Loading additional internal researchers from: {file3}")
            
            df = pd.read_excel(file3)
            loaded = 0
            
            for _, row in df.iterrows():
                email = clean_text(row.get('Humber Email', ''))
                name = clean_text(row.get('Researcher Full Name', ''))
                
                if not email or not name:
                    continue
                
                # Check if already exists
                if Researcher.query.filter_by(email=email).first():
                    print(f"  ⏭ Skipping duplicate: {email}")
                    continue
                
                # Get job info
                job_title = clean_text(row.get('Job Title', ''))
                job_status = clean_text(row.get('Job Status', ''))
                experience = f"{job_title}"
                if job_status:
                    experience += f" ({job_status})"
                
                researcher = Researcher(
                    name=name,
                    email=email,
                    organization='Humber Polytechnic',
                    researcher_type='internal',
                    faculty_department=clean_text(row.get('Faculty', '')),
                    primary_areas=clean_text(row.get('Research Interest Keywords', '')),
                    experience_summary=experience,
                    sectors_interested=''
                )
                
                db.session.add(researcher)
                loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {loaded} internal researchers from file 2\n")
            total_loaded += loaded
            
        except FileNotFoundError:
            print(f"✗ File not found: {file3}\n")
        except Exception as e:
            print(f"✗ Error loading internal researchers (file 2): {str(e)}\n")
            db.session.rollback()
        
        # Summary
        print("="*60)
        print(f"Data Loading Complete!")
        print(f"Total researchers loaded: {total_loaded}")
        print(f"Internal: {Researcher.query.filter_by(researcher_type='internal').count()}")
        print(f"External: {Researcher.query.filter_by(researcher_type='external').count()}")
        print("="*60 + "\n")
        
        return total_loaded

if __name__ == '__main__':
    load_all_data()
