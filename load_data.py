"""
Load researcher data from Excel files into the database.
This script loads data from 2 Excel files:
1. HumberInternalResearch.xlsx - Internal Humber researchers
2. ExternalResearch.xlsx - External researchers
"""

import pandas as pd
import re
from app import app, db, Researcher, Match, EmailLog

def clean_text(value):
    """Clean and normalize text values from Excel"""
    if pd.isna(value) or value is None:
        return ''
    return str(value).strip()

def preprocess_text(text: str) -> str:
    """
    Basic preprocessing for text fields:
    - Lowercase
    - Remove special characters
    - Keep only alphanumeric and spaces
    """
    if pd.isna(text) or not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Remove extra spaces
    text = " ".join(text.split())
    return text

def compute_and_store_matches():
    """Pre-compute matches for all internal researchers and store in database
    Optimized for 4GB RAM with batch processing and memory management.
    """
    import gc
    from matching import find_matches
    
    # Clear existing matches
    Match.query.delete()
    db.session.commit()
    print("✓ Cleared old matches\n")
    
    # Get all internal researchers
    internal_researchers = Researcher.query.filter_by(researcher_type='internal').all()
    total_researchers = len(internal_researchers)
    print(f"Computing matches for {total_researchers} internal researchers...\n")
    print("Processing in batches of 5 to optimize memory usage...\n")
    
    matches_stored = 0
    errors = 0
    
    # Process in smaller batches of 5 to reduce memory pressure
    batch_size = 5
    
    for batch_start in range(0, total_researchers, batch_size):
        batch_end = min(batch_start + batch_size, total_researchers)
        batch = internal_researchers[batch_start:batch_end]
        
        print(f"\n--- Batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end} of {total_researchers}) ---")
        
        for idx, internal in enumerate(batch, start=batch_start+1):
            try:
                print(f"  [{idx}/{total_researchers}] {internal.name}...", end=" ")
                
                # Find top 1 match for this researcher
                matches = find_matches(internal, top_n=1)
                
                for rank, match_data in enumerate(matches, 1):
                    # Get external researcher by email
                    external = Researcher.query.filter_by(email=match_data['email']).first()
                    
                    if external:
                        # Store match in database
                        match = Match(
                            internal_researcher_id=internal.id,
                            external_researcher_id=external.id,
                            similarity_percentage=match_data['similarity_percentage'],
                            match_rank=rank
                        )
                        db.session.add(match)
                        matches_stored += 1
                        print(f"✓ {match_data['similarity_percentage']:.1f}%")
                    else:
                        print("✗ No match found")
            
            except Exception as e:
                print(f"✗ Error: {str(e)[:50]}")
                errors += 1
                continue
        
        # Commit after each batch and force garbage collection
        db.session.commit()
        gc.collect()  # Free up memory
        print(f"  ✓ Batch committed ({matches_stored} matches total, {errors} errors)")
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"✅ Matching Complete!")
    print(f"  Total processed: {total_researchers}")
    print(f"  Matches stored: {matches_stored}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")

def load_all_data():
    """Load all Excel files into the database"""
    
    print("\n" + "="*60)
    print("Loading Researcher Data into Database")
    print("="*60 + "\n")
    
    total_loaded = 0
    
    with app.app_context():
        # Clear existing data (delete in correct order due to foreign keys)
        print("Clearing existing data...")
        EmailLog.query.delete()  # Delete email logs first
        Match.query.delete()     # Delete matches second
        Researcher.query.delete() # Delete researchers last
        db.session.commit()
        print("✓ Database cleared\n")
        
        # File 1: Internal Researchers
        try:
            file1 = 'HumberInternalResearch.xlsx'
            print(f"Loading internal researchers from: {file1}")
            
            df = pd.read_excel(file1)
            loaded = 0
            
            # Rename columns for easier access
            col_names = {
                "Your Name": "name",
                "Email Address": "email",
                "Your Faculty/Department": "faculty",
                df.columns[4]: "expertise",  # "What are your primary areas..."
                df.columns[5]: "summary",    # "Please provide a brief summary..."
                df.columns[6]: "sectors"     # "What sectors or societal challenges..."
            }
            df = df.rename(columns=col_names)
            
            for _, row in df.iterrows():
                email = clean_text(row.get('email', ''))
                name = clean_text(row.get('name', ''))
                
                if not email or not name:
                    continue
                
                # Check if already exists
                if Researcher.query.filter_by(email=email).first():
                    print(f"  ⏭ Skipping duplicate: {email}")
                    continue
                
                # Combine text fields for matching
                expertise_text = clean_text(row.get('expertise', ''))
                summary_text = clean_text(row.get('summary', ''))
                sectors_text = clean_text(row.get('sectors', ''))
                
                # Create combined text for semantic matching
                combined_text = f"{expertise_text}. {summary_text}. {sectors_text}"
                
                researcher = Researcher(
                    name=name,
                    email=email,
                    organization='Humber Polytechnic',
                    researcher_type='internal',
                    faculty_department=clean_text(row.get('faculty', '')),
                    primary_areas=expertise_text,
                    experience_summary=summary_text,
                    sectors_interested=sectors_text
                )
                
                db.session.add(researcher)
                loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {loaded} internal researchers\n")
            total_loaded += loaded
            
        except FileNotFoundError:
            print(f"✗ File not found: {file1}\n")
        except Exception as e:
            print(f"✗ Error loading internal researchers: {str(e)}\n")
            db.session.rollback()
        
        # File 2: External Researchers
        try:
            file2 = 'ExternalResearch.xlsx'
            print(f"Loading external researchers from: {file2}")
            
            df = pd.read_excel(file2)
            loaded = 0
            
            # Rename columns for easier access
            col_names = {
                "Your Name": "name",
                "Email Address": "email",
                "Your Orgnization": "organization",
                df.columns[4]: "sector",      # "What is your organization's primary area..."
                df.columns[5]: "challenge",   # "Please describe a challenge..."
                df.columns[6]: "expertise",   # "What type of expertise..."
                df.columns[7]: "lab_tours"    # "Which lab tour(s)..."
            }
            df = df.rename(columns=col_names)
            
            for _, row in df.iterrows():
                email = clean_text(row.get('email', ''))
                name = clean_text(row.get('name', ''))
                
                if not email or not name:
                    continue
                
                # Check if already exists
                if Researcher.query.filter_by(email=email).first():
                    print(f"  ⏭ Skipping duplicate: {email}")
                    continue
                
                # Get text fields
                sector_text = clean_text(row.get('sector', ''))
                challenge_text = clean_text(row.get('challenge', ''))
                expertise_text = clean_text(row.get('expertise', ''))
                
                researcher = Researcher(
                    name=name,
                    email=email,
                    organization=clean_text(row.get('organization', '')),
                    researcher_type='external',
                    organization_focus=sector_text,
                    challenge_description=challenge_text,
                    expertise_sought=expertise_text,
                    lab_tours_interested=clean_text(row.get('lab_tours', ''))
                )
                
                db.session.add(researcher)
                loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {loaded} external researchers\n")
            total_loaded += loaded
            
        except FileNotFoundError:
            print(f"✗ File not found: {file2}\n")
        except Exception as e:
            print(f"✗ Error loading external researchers: {str(e)}\n")
            db.session.rollback()
        
        # Summary
        print("="*60)
        print(f"Data Loading Complete!")
        print(f"Total researchers loaded: {total_loaded}")
        print(f"Internal: {Researcher.query.filter_by(researcher_type='internal').count()}")
        print(f"External: {Researcher.query.filter_by(researcher_type='external').count()}")
        print("\n⚠️  Next: Visit /admin/compute-matches to pre-compute matches")
        print("="*60)
        
        return total_loaded

if __name__ == '__main__':
    load_all_data()
