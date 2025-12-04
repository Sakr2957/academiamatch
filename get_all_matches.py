"""
Helper function to get all matches between internal and external researchers.
This is imported by app.py for the match list page.
"""

def get_all_matches(top_n=1):
    """
    Get all matches between internal and external researchers.
    
    Args:
        top_n: Number of top matches per internal researcher (default: 1 for best match only)
        
    Returns:
        List of match dictionaries
    """
    from app import Researcher
    from matching import find_matches
    
    # Get all internal researchers
    internal_researchers = Researcher.query.filter_by(researcher_type='internal').all()
    
    all_matches = []
    
    for internal in internal_researchers:
        # Get top matches for this internal researcher
        matches = find_matches(internal, top_n=top_n)
        
        for idx, match in enumerate(matches, 1):
            all_matches.append({
                'internal_name': internal.name,
                'internal_email': internal.email,
                'faculty_department': internal.faculty_department or 'N/A',
                'external_name': match['name'],
                'external_email': match['email'],
                'organization': match['organization'],
                'similarity_percentage': match['similarity_percentage'],
                'match_rank': idx
            })
    
    # Sort by similarity score (highest first)
    all_matches.sort(key=lambda x: x['similarity_percentage'], reverse=True)
    
    return all_matches
