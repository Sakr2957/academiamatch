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
    # Use the caller's app context (don't create a new one)
    total_loaded = 0
    
    # Load internal researchers
    try:
        print("="*60)
        print("Loading Internal Researchers (Humber)...")
        print("="*60 + "\n")
        
        df_internal = pd.read_excel('HumberInternalResearch.xlsx')
        
        # Track emails to skip duplicates within the Excel file
        seen_emails = set()
        skipped = 0
        
        for _, row in df_internal.iterrows():
            email = str(row.get('Email Address', '')).lower().strip()
            
            # Skip if we've already seen this email
            if email in seen_emails:
                print(f"  ⏭️  Skipping duplicate email: {email}")
                skipped += 1
                continue
            
            seen_emails.add(email)
            
            researcher = Researcher(
                name=str(row.get('Your Name', '')),
                email=email,
                researcher_type='internal',
                organization='Humber Polytechnic',
                faculty_department=clean_text(row.get('Your Faculty/Department', '')),
                primary_areas=clean_text(row.get('What are your primary areas of research or expertise?Please list key words or phrases (e.g., machine learning, food security, sustainable packaging, behavioral economics).', '')),
                experience_summary=clean_text(row.get('Please provide a brief summary of your experience or capabilities relevant to collaborative research?(e.g., summary of technical skills, related past work, specialized expertise)', '')),
                sectors_interested=clean_text(row.get('What sectors or societal challenges are you most interested in addressing through research?(e.g., healthcare innovation, climate resilience, advanced manufacturing, education equity)', ''))
            )
            db.session.add(researcher)
            total_loaded += 1
        
        db.session.commit()
        print(f"✓ Loaded {len(df_internal) - skipped} internal researchers ({skipped} duplicates skipped)\n")
        
    except Exception as e:
        print(f"✗ Error loading internal researchers: {str(e)}\n")
        db.session.rollback()
    
    # Load external researchers
    try:
        print("="*60)
        print("Loading External Researchers...")
        print("="*60 + "\n")
        
        df_external = pd.read_excel('ExternalResearch.xlsx')
        
        # Track emails to skip duplicates within the Excel file
        seen_emails_ext = set()
        skipped_ext = 0
        
        for _, row in df_external.iterrows():
            email = str(row.get('Email Address', '')).lower().strip()
            
            # Skip if we've already seen this email
            if email in seen_emails_ext:
                print(f"  ⏭️  Skipping duplicate email: {email}")
                skipped_ext += 1
                continue
            
            seen_emails_ext.add(email)
            
            researcher = Researcher(
                name=str(row.get('Your Name', '')),
                email=email,
                researcher_type='external',
                organization=clean_text(row.get('Your Orgnization', '')),
                organization_focus=clean_text(row.get('What is your organization\'s primary area of focus or industry sector?Please list key words or phrases (e.g., renewable energy, healthcare, logistics, education technology)', '')),
                challenge_description=clean_text(row.get('Please describe a challenge or business goal your organization is currently facing that could benefit from academic collaboration.\n(e.g., improving supply chain efficiency, developing sustainable mate', '')),
                expertise_sought=clean_text(row.get('What type of expertise or research support are you seeking to address this challenge?(e.g., machine learning, food security, sustainable packaging, behavioral economics)', '')),
                lab_tours_interested=clean_text(row.get('Which lab tour(s) would you be interested in joining during our event? (Tour selection will be finalized at the event. As tour lengths will vary, it is anticipated that participants will have time to ', ''))
            )
            db.session.add(researcher)
            total_loaded += 1
        
        db.session.commit()
        print(f"✓ Loaded {len(df_external) - skipped_ext} external researchers ({skipped_ext} duplicates skipped)\n")
        
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
