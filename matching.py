from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load model once (will be cached)
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

def get_researcher_text(researcher):
    """Extract text representation of researcher for matching"""
    if researcher.researcher_type == 'internal':
        return f"{researcher.primary_areas or ''} {researcher.experience_summary or ''} {researcher.sectors_interested or ''}"
    else:
        return f"{researcher.organization_focus or ''} {researcher.challenge_description or ''} {researcher.expertise_sought or ''}"

def find_matches(current_researcher, top_n=5):
    """Find top N matching researchers"""
    from app import Researcher
    
    # Get opposite type researchers
    opposite_type = 'external' if current_researcher.researcher_type == 'internal' else 'internal'
    candidates = Researcher.query.filter_by(researcher_type=opposite_type).all()
    
    if not candidates:
        return []
    
    # Get model
    model = get_model()
    
    # Encode current researcher
    current_text = get_researcher_text(current_researcher)
    current_embedding = model.encode([current_text])[0]
    
    # Encode all candidates
    candidate_texts = [get_researcher_text(c) for c in candidates]
    candidate_embeddings = model.encode(candidate_texts)
    
    # Calculate similarities
    similarities = cosine_similarity([current_embedding], candidate_embeddings)[0]
    
    # Get top N indices
    top_indices = np.argsort(similarities)[::-1][:top_n]
    
    # Prepare results
    results = []
    for idx in top_indices:
        candidate = candidates[idx]
        score = float(similarities[idx])
        
        # Get interests/areas
        if candidate.researcher_type == 'internal':
            interests = candidate.primary_areas or ''
        else:
            interests = candidate.expertise_sought or ''
        
        results.append({
            'id': candidate.id,
            'name': candidate.name,
            'email': candidate.email,
            'organization': candidate.organization,
            'department': candidate.faculty_department or '',
            'interests': interests,
            'score': score,
            'score_percent': int(score * 100)
        })
    
    return results
