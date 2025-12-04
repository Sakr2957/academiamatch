import pandas as pd
from app import db, Researcher, Match
import re

def clean_text(text):
    """Clean and normalize text fields"""
    if pd.isna(text):
        return ""
    
    # Convert to string
    text = str(text)
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:()\-]', '', text)
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove extra spaces
    text = " ".join(text.split())
    return text

def compute_and_store_matches_incremental(batch_number=1, batch_size=10):
    """Pre-compute matches incrementally - processes 10 researchers per run.
    Call this multiple times to process all researchers.
    
    Args:
        batch_number: Which batch to process (1-based)
        batch_size: Number of researchers per batch (default: 10)
    
    Returns:
        dict with progress info
    """
    import gc
    from matching import find_matches
    
    # Get all internal researchers
    internal_researchers = Researcher.query.filter_by(researcher_type='internal').all()
    total_researchers = len(internal_researchers)
    
    # Calculate which researchers to process in this batch
    start_idx = (batch_number - 1) * batch_size
    end_idx = min(start_idx + batch_size, total_researchers)
    
    # Check if this batch is valid
    if start_idx >= total_researchers:
        return {
            'status': 'complete',
            'message': 'All researchers already processed!',
            'total': total_researchers,
            'processed': Match.query.count(),
            'remaining': 0
        }
    
    batch = internal_researchers[start_idx:end_idx]
    
    print(f"\n{'='*60}")
    print(f"Incremental Match Computation - Batch {batch_number}")
    print(f"Processing researchers {start_idx+1}-{end_idx} of {total_researchers}")
    print(f"{'='*60}\n")
    
    matches_stored = 0
    errors = 0
    
    for idx, internal in enumerate(batch, start=start_idx+1):
        try:
            print(f"  [{idx}/{total_researchers}] {internal.name}...", end=" ")
            
            # Check if match already exists
            existing = Match.query.filter_by(internal_researcher_id=internal.id).first()
            if existing:
                print("⏭️ Already computed")
                continue
            
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
    
    # Commit and cleanup
    db.session.commit()
    gc.collect()
    
    # Calculate progress
    total_matches = Match.query.count()
    remaining = total_researchers - total_matches
    
    print(f"\n{'='*60}")
    print(f"✅ Batch {batch_number} Complete!")
    print(f"  Processed in this batch: {matches_stored}")
    print(f"  Total matches in database: {total_matches}/{total_researchers}")
    print(f"  Remaining: {remaining}")
    print(f"{'='*60}\n")
    
    return {
        'status': 'success' if remaining > 0 else 'complete',
        'batch_number': batch_number,
        'processed_this_batch': matches_stored,
        'total_matches': total_matches,
        'total_researchers': total_researchers,
        'remaining': remaining,
        'next_batch': batch_number + 1 if remaining > 0 else None
    }

def load_all_data():
    """Load all Excel files into the database"""
    from app import app
    
    with app.app_context():
        total_loaded = 0
        
        # Load internal researchers
        try:
            print("="*60)
            print("Loading Internal Researchers (Humber)...")
            print("="*60 + "\n")
            
            df_internal = pd.read_excel('HumberInternalResearch.xlsx')
            
            for _, row in df_internal.iterrows():
                researcher = Researcher(
                    name=str(row.get('Name', '')),
                    email=str(row.get('Email', '')).lower().strip(),
                    researcher_type='internal',
                    organization='Humber Polytechnic',
                    department=clean_text(row.get('Department', '')),
                    research_interests=clean_text(row.get('Research Interests', '')),
                    expertise=clean_text(row.get('Expertise', '')),
                    current_projects=clean_text(row.get('Current Projects', '')),
                    collaboration_goals=clean_text(row.get('Collaboration Goals', ''))
                )
                db.session.add(researcher)
                total_loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {len(df_internal)} internal researchers\n")
            
        except Exception as e:
            print(f"✗ Error loading internal researchers: {str(e)}\n")
            db.session.rollback()
        
        # Load external researchers
        try:
            print("="*60)
            print("Loading External Researchers...")
            print("="*60 + "\n")
            
            df_external = pd.read_excel('ExternalResearch.xlsx')
            
            for _, row in df_external.iterrows():
                researcher = Researcher(
                    name=str(row.get('Name', '')),
                    email=str(row.get('Email', '')).lower().strip(),
                    researcher_type='external',
                    organization=clean_text(row.get('Organization', '')),
                    research_focus=clean_text(row.get('Research Focus', '')),
                    industry_sector=clean_text(row.get('Industry Sector', '')),
                    partnership_interests=clean_text(row.get('Partnership Interests', '')),
                    available_resources=clean_text(row.get('Available Resources', ''))
                )
                db.session.add(researcher)
                total_loaded += 1
            
            db.session.commit()
            print(f"✓ Loaded {len(df_external)} external researchers\n")
            
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
