"""
Researcher matching using Sentence Transformers and Cosine Similarity.
Matches internal Humber researchers with external researchers based on semantic similarity.
"""

import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app import Researcher

# Global model instance (loaded once and reused)
_model = None

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
    Basic preprocessing: lowercase, remove special chars.
    Note: We don't remove stopwords here as Sentence Transformers
    are trained to handle them appropriately.
    """
    if not text or text is None:
        return ""
    text = str(text).lower()
    # Remove special characters but keep spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Remove extra whitespace
    text = " ".join(text.split())
    return text

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

def extract_keywords(text):
    """
    Extract keywords from text by splitting on commas and cleaning.
    Returns a set of lowercase keywords.
    """
    if not text:
        return set()
    
    keywords = set()
    # Split by comma and clean each keyword
    for keyword in text.split(','):
        cleaned = keyword.strip().lower()
        if cleaned and len(cleaned) > 2:  # Ignore very short keywords
            keywords.add(cleaned)
    
    return keywords

def find_relevant_keywords(internal_researcher, external_researcher, top_n=7):
    """
    Find most relevant keywords between internal and external researchers.
    Uses both exact matching and semantic similarity.
    
    Args:
        internal_researcher: Internal Researcher object
        external_researcher: External Researcher object
        top_n: Number of top keywords to return (default: 7)
    
    Returns:
        List of relevant keywords (strings)
    """
    # Extract keywords from both researchers
    internal_keywords = extract_keywords(internal_researcher.primary_areas or '')
    
    external_keywords = set()
    external_keywords.update(extract_keywords(external_researcher.expertise_sought or ''))
    external_keywords.update(extract_keywords(external_researcher.organization_focus or ''))
    
    # First, find exact matches
    exact_matches = internal_keywords.intersection(external_keywords)
    
    # If we have exact matches, prioritize them
    if exact_matches:
        result = list(exact_matches)
        
        # Add more keywords from both sides if needed
        remaining_internal = internal_keywords - exact_matches
        remaining_external = external_keywords - exact_matches
        
        # Add remaining keywords alternating between internal and external
        all_remaining = list(remaining_internal) + list(remaining_external)
        result.extend(all_remaining[:top_n - len(result)])
        
        return sorted(result[:top_n])
    
    # If no exact matches, combine all keywords and return top N
    all_keywords = list(internal_keywords.union(external_keywords))
    
    # If still no keywords, try to extract from full text
    if not all_keywords:
        # Extract from any available text
        internal_text = (internal_researcher.primary_areas or '') + ' ' + \
                       (internal_researcher.experience_summary or '') + ' ' + \
                       (internal_researcher.sectors_interested or '')
        
        external_text = (external_researcher.expertise_sought or '') + ' ' + \
                       (external_researcher.organization_focus or '') + ' ' + \
                       (external_researcher.challenge_description or '')
        
        # Extract important words (simple approach: split and clean)
        for text in [internal_text, external_text]:
            words = text.lower().split()
            for word in words:
                cleaned = word.strip('.,;:!?()[]{}"\'')
                if len(cleaned) > 4 and cleaned not in ['their', 'there', 'these', 'those', 'would', 'could', 'should']:
                    all_keywords.append(cleaned)
        
        # Remove duplicates and limit
        all_keywords = list(set(all_keywords))
    
    return sorted(all_keywords[:top_n])

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
    
    # Build text representations
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
    
    # Determine which type to match against
    if target.researcher_type == 'internal':
        # Internal researcher: match with external researchers
        candidates = Researcher.query.filter_by(researcher_type='external').all()
    else:
        # External researcher: match with internal researchers
        candidates = Researcher.query.filter_by(researcher_type='internal').all()
    
    if not candidates:
        return []
    
    # Build text representations
    target_text = build_text_for_matching(target)
    candidate_texts = [build_text_for_matching(c) for c in candidates]
    
    # Check if target text is empty
    if not target_text.strip():
        print(f"Warning: No text content for {email}")
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

def get_all_matches(top_n=3):
    """
    Generate matches for all external researchers.
    Returns a list of all matches for display.
    
    Args:
        top_n: Number of top matches per external researcher
    
    Returns:
        List of match dictionaries
    """
    external_researchers = Researcher.query.filter_by(researcher_type='external').all()
    internal_researchers = Researcher.query.filter_by(researcher_type='internal').all()
    
    if not external_researchers or not internal_researchers:
        return []
    
    # Build text representations
    external_texts = [build_text_for_matching(r) for r in external_researchers]
    internal_texts = [build_text_for_matching(r) for r in internal_researchers]
    
    # Get the model
    model = get_model()
    
    # Generate embeddings
    external_embeddings = model.encode(external_texts, normalize_embeddings=True)
    internal_embeddings = model.encode(internal_texts, normalize_embeddings=True)
    
    # Calculate similarity matrix: [num_external x num_internal]
    similarity_matrix = cosine_similarity(external_embeddings, internal_embeddings)
    
    # Generate matches
    all_matches = []
    
    for ext_idx, external in enumerate(external_researchers):
        similarities = similarity_matrix[ext_idx]
        
        # Get top N matches
        top_indices = np.argsort(-similarities)[:top_n]
        
        for rank, int_idx in enumerate(top_indices, start=1):
            internal = internal_researchers[int_idx]
            similarity_score = float(similarities[int_idx])
            
            # Only include meaningful matches
            if similarity_score > 0.1:
                match = {
                    'external_name': external.name,
                    'external_email': external.email,
                    'organization': external.organization,
                    'organization_focus': external.organization_focus,
                    'expertise_sought': external.expertise_sought,
                    'internal_name': internal.name,
                    'internal_email': internal.email,
                    'faculty_department': internal.faculty_department,
                    'primary_areas': internal.primary_areas,
                    'match_rank': rank,
                    'similarity_score': round(similarity_score, 4),
                    'similarity_percentage': round(similarity_score * 100, 2)
                }
                all_matches.append(match)
    
    return all_matches

def preload_model():
    """
    Preload the model during app startup to avoid delays on first request.
    Call this from app.py after database initialization.
    """
    try:
        get_model()
        print("✓ Sentence Transformer model preloaded")
    except Exception as e:
        print(f"✗ Error preloading model: {str(e)}")
