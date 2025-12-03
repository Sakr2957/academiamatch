from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def get_text_for_matching(researcher):
    """Combine all relevant text fields for matching"""
    texts = []
    
    if researcher.primary_areas:
        texts.append(researcher.primary_areas)
    if researcher.experience_summary:
        texts.append(researcher.experience_summary)
    if researcher.sectors_interested:
        texts.append(researcher.sectors_interested)
    if researcher.organization_focus:
        texts.append(researcher.organization_focus)
    if researcher.challenge_description:
        texts.append(researcher.challenge_description)
    if researcher.expertise_sought:
        texts.append(researcher.expertise_sought)
    
    return ' '.join(texts) if texts else ''

def find_matches(researcher, top_n=5):
    """Find top N matching researchers using TF-IDF"""
    from app import Researcher
    
    # Determine opposite type
    if researcher.researcher_type == 'internal':
        target_type = 'external'
    else:
        target_type = 'internal'
    
    # Get all researchers of opposite type
    candidates = Researcher.query.filter_by(researcher_type=target_type).all()
    
    if not candidates:
        return []
    
    # Get text for query researcher
    query_text = get_text_for_matching(researcher)
    
    if not query_text.strip():
        return []
    
    # Get texts for all candidates
    candidate_texts = [get_text_for_matching(c) for c in candidates]
    
    # Filter out empty texts
    valid_candidates = [(c, t) for c, t in zip(candidates, candidate_texts) if t.strip()]
    
    if not valid_candidates:
        return []
    
    candidates, candidate_texts = zip(*valid_candidates)
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
    
    # Fit on all texts including query
    all_texts = [query_text] + list(candidate_texts)
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Calculate cosine similarity
    query_vector = tfidf_matrix[0:1]
    candidate_vectors = tfidf_matrix[1:]
    
    similarities = cosine_similarity(query_vector, candidate_vectors)[0]
    
    # Get top N matches
    top_indices = np.argsort(similarities)[::-1][:top_n]
    
    matches = []
    for idx in top_indices:
        score = float(similarities[idx])
        if score > 0:  # Only include matches with some similarity
            matches.append({
                'researcher': candidates[idx],
                'score': round(score * 100, 1)  # Convert to percentage
            })
    
    return matches
