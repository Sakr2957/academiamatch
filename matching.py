"""
Researcher matching using Sentence Transformers and Cosine Similarity.
Matches internal Humber researchers with external researchers based on semantic similarity.
Uses proper text preprocessing with stopword removal for better matching accuracy.
"""

import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app import Researcher

# Global model instance (loaded once and reused)
_model = None

# English stopwords (common words to remove)
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", 
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
    'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them',
    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll",
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
    'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd',
    'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn',
    "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn',
    "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't",
    'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

def get_model():
    """Get or initialize the Sentence Transformer model"""
    global _model
    if _model is None:
        print("Loading Sentence Transformer model (all-MiniLM-L6-v2)...")
        # Use device='cpu' and optimize for memory
        _model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
        print("✓ Model loaded successfully")
    return _model

def preprocess_text(text: str) -> str:
    """
    Proper text preprocessing with stopword removal and tokenization.
    This matches the approach from the reference notebook for better accuracy.
    
    Steps:
    1. Lowercase
    2. Remove special characters
    3. Remove stopwords
    4. Filter short words (< 3 characters)
    
    Args:
        text: Raw text string
    
    Returns:
        Cleaned text string with stopwords removed
    """
    if not text or text is None:
        return ""
    
    # 1. Lowercase
    text = str(text).lower()
    
    # 2. Remove special characters but keep spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    
    # 3. Tokenize and remove stopwords + short words
    tokens = [
        word for word in text.split()
        if word not in STOPWORDS and len(word) > 2
    ]
    
    # 4. Join cleaned tokens
    return " ".join(tokens)

def build_text_for_matching(researcher):
    """
    Build the text representation for a researcher based on their type.
    
    For internal researchers: combine expertise, summary, and sectors
    For external researchers: combine expertise sought, sector, and challenge
    """
    if researcher.researcher_type == 'internal':
        # Internal: focus on what they can offer
        parts = [
            researcher.primary_areas or '',
            researcher.experience_summary or '',
            researcher.sectors_interested or ''
        ]
    else:
        # External: focus on what they need
        parts = [
            researcher.expertise_sought or '',
            researcher.organization_focus or '',
            researcher.challenge_description or ''
        ]
    
    # Combine and preprocess
    combined = ". ".join(parts)
    return preprocess_text(combined)

def extract_clean_keywords(text, max_words=2):
    """
    Extract clean 1-2 word keywords from text.
    
    Args:
        text: Text to extract keywords from
        max_words: Maximum words per keyword (default: 2)
    
    Returns:
        List of clean keyword phrases
    """
    if not text:
        return []
    
    # Preprocess the text
    cleaned = preprocess_text(text)
    
    # Split into words
    words = cleaned.split()
    
    keywords = []
    
    # Extract single words (minimum 3 characters)
    for word in words:
        if len(word) >= 3:
            keywords.append(word)
    
    # Extract 2-word phrases
    if max_words >= 2:
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            keywords.append(phrase)
    
    return keywords

def find_relevant_keywords(internal_researcher, external_researcher, top_n=7):
    """
    Find most relevant keywords between internal and external researchers.
    Uses semantic similarity to find the most meaningful overlapping terms.
    
    Args:
        internal_researcher: Internal Researcher object
        external_researcher: External Researcher object
        top_n: Number of top keywords to return (default: 7)
    
    Returns:
        List of relevant keyword strings (1-2 words each)
    """
    # Extract keywords from both researchers
    internal_text = (internal_researcher.primary_areas or '') + ' ' + \
                   (internal_researcher.experience_summary or '') + ' ' + \
                   (internal_researcher.sectors_interested or '')
    
    external_text = (external_researcher.expertise_sought or '') + ' ' + \
                   (external_researcher.organization_focus or '') + ' ' + \
                   (external_researcher.challenge_description or '')
    
    # Get clean keywords from both
    internal_keywords = extract_clean_keywords(internal_text, max_words=2)
    external_keywords = extract_clean_keywords(external_text, max_words=2)
    
    if not internal_keywords and not external_keywords:
        return []
    
    # Combine all keywords
    all_keywords = list(set(internal_keywords + external_keywords))
    
    # If we have too many, use frequency to prioritize
    if len(all_keywords) > top_n:
        # Count frequency of each keyword
        keyword_freq = {}
        for kw in internal_keywords + external_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
        
        # Sort by frequency (descending)
        sorted_keywords = sorted(all_keywords, key=lambda k: keyword_freq.get(k, 0), reverse=True)
        
        # Return top N
        return sorted_keywords[:top_n]
    
    return all_keywords[:top_n]

def find_matches(researcher, top_n=5):
    """
    Find top N matches for a researcher object.
    
    Args:
        researcher: Researcher object to find matches for
        top_n: Number of top matches to return (default: 5)
    
    Returns:
        List of dictionaries containing match information with similarity scores
    """
    if not researcher:
        return []
    
    # Determine which type to match against
    if researcher.researcher_type == 'internal':
        # Internal researcher: match with external researchers
        candidates = Researcher.query.filter_by(researcher_type='external').all()
    else:
        # External researcher: match with internal researchers
        candidates = Researcher.query.filter_by(researcher_type='internal').all()
    
    if not candidates:
        return []
    
    # Build text representations (with proper preprocessing)
    target_text = build_text_for_matching(researcher)
    candidate_texts = [build_text_for_matching(c) for c in candidates]
    
    # Check if target text is empty
    if not target_text.strip():
        print(f"Warning: No text content for {researcher.email}")
        return []
    
    # Get the model
    model = get_model()
    
    # Generate embeddings
    target_embedding = model.encode([target_text], normalize_embeddings=True)
    candidate_embeddings = model.encode(candidate_texts, normalize_embeddings=True)
    
    # Calculate cosine similarities
    similarities = cosine_similarity(target_embedding, candidate_embeddings)[0]
    
    # Get top N matches
    top_indices = np.argsort(-similarities)[:top_n]
    
    # Build results
    matches = []
    for rank, idx in enumerate(top_indices, start=1):
        candidate = candidates[idx]
        similarity_score = float(similarities[idx])
        
        # Only include matches with meaningful similarity (> 0.1)
        if similarity_score > 0.1:
            match_info = {
                'rank': rank,
                'name': candidate.name,
                'email': candidate.email,
                'organization': candidate.organization,
                'researcher_type': candidate.researcher_type,
                'similarity_score': round(similarity_score, 4),
                'similarity_percentage': round(similarity_score * 100, 2)
            }
            
            # Add matching keywords
            if researcher.researcher_type == 'internal':
                # Internal searching for external
                match_info['matching_keywords'] = find_relevant_keywords(researcher, candidate)
            else:
                # External searching for internal
                match_info['matching_keywords'] = find_relevant_keywords(candidate, researcher)
            
            # Add type-specific information
            if candidate.researcher_type == 'internal':
                match_info['faculty_department'] = candidate.faculty_department
                match_info['primary_areas'] = candidate.primary_areas
                match_info['experience_summary'] = candidate.experience_summary
            else:
                match_info['organization_focus'] = candidate.organization_focus
                match_info['expertise_sought'] = candidate.expertise_sought
                match_info['challenge_description'] = candidate.challenge_description
            
            matches.append(match_info)
    
    return matches

def find_matches_for_researcher(email, top_n=5):
    """
    Find top N matches for a researcher by email.
    
    Args:
        email: Email of the researcher to find matches for
        top_n: Number of top matches to return (default: 5)
    
    Returns:
        List of dictionaries containing match information with similarity scores
    """
    # Get the target researcher
    target = Researcher.query.filter_by(email=email).first()
    if not target:
        return []
    
    return find_matches(target, top_n)

def compute_all_matches_batch(batch_size=19):
    """
    Compute matches for all external researchers in batches.
    Stores results in the Match table.
    
    Args:
        batch_size: Number of researchers to process per batch (default: 10)
    
    Returns:
        Number of matches computed
    """
    from app import db, Match
    
    # Get all external researchers
    external_researchers = Researcher.query.filter_by(researcher_type='external').all()
    
    if not external_researchers:
        print("No external researchers found")
        return 0
    
    # Get all internal researchers
    internal_researchers = Researcher.query.filter_by(researcher_type='internal').all()
    
    if not internal_researchers:
        print("No internal researchers found")
        return 0
    
    print(f"Computing matches for {len(external_researchers)} external researchers...")
    print(f"Against {len(internal_researchers)} internal researchers")
    print(f"Using batch size: {batch_size}")
    
    # Clear existing matches
    Match.query.delete()
    db.session.commit()
    
    # Get the model once
    model = get_model()
    
    # Precompute all internal embeddings (with proper preprocessing)
    print("Precomputing internal researcher embeddings...")
    internal_texts = [build_text_for_matching(r) for r in internal_researchers]
    internal_embeddings = model.encode(internal_texts, normalize_embeddings=True, batch_size=batch_size)
    print(f"✓ Computed {len(internal_embeddings)} internal embeddings")
    
    # Process external researchers in batches
    total_matches = 0
    num_batches = (len(external_researchers) + batch_size - 1) // batch_size
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(external_researchers))
        batch = external_researchers[start_idx:end_idx]
        
        print(f"Processing batch {batch_idx + 1}/{num_batches} ({len(batch)} researchers)...")
        
        # Compute embeddings for this batch (with proper preprocessing)
        batch_texts = [build_text_for_matching(r) for r in batch]
        batch_embeddings = model.encode(batch_texts, normalize_embeddings=True)
        
        # Compute similarities for this batch
        similarities = cosine_similarity(batch_embeddings, internal_embeddings)
        
        # Store matches for each external researcher in this batch
        for i, external in enumerate(batch):
            sims = similarities[i]
            
            # Get top 20 matches per external researcher
            top_indices = np.argsort(-sims)[:20]
            
            for rank, idx in enumerate(top_indices, start=1):
                internal = internal_researchers[idx]
                similarity_score = float(sims[idx])
                
                # Only store meaningful matches (> 0.1)
                if similarity_score > 0.1:
                    match = Match(
                        external_email=external.email,
                        internal_email=internal.email,
                        similarity_score=similarity_score,
                        match_rank=rank
                    )
                    db.session.add(match)
                    total_matches += 1
        
        # Commit after each batch
        db.session.commit()
        print(f"✓ Batch {batch_idx + 1} complete")
    
    print(f"✓ Computed {total_matches} total matches")
    return total_matches
