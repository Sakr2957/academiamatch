"""
Compute ALL matches between internal and external researchers.
Uses the improved matching algorithm with stopword removal.
Exports results to Excel file sorted by match score.
"""

import pandas as pd
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# English stopwords (same as in matching.py)
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

def preprocess_text(text):
    """Preprocess text with stopword removal"""
    if not text or pd.isna(text):
        return ""
    
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [word for word in text.split() if word not in STOPWORDS and len(word) > 2]
    return " ".join(tokens)

def extract_clean_keywords(text, max_words=2):
    """Extract clean 1-2 word keywords"""
    if not text or pd.isna(text):
        return []
    
    cleaned = preprocess_text(text)
    words = cleaned.split()
    
    keywords = []
    
    # Single words
    for word in words:
        if len(word) >= 3:
            keywords.append(word)
    
    # 2-word phrases
    if max_words >= 2:
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            keywords.append(phrase)
    
    return keywords

def find_relevant_keywords(internal_text, external_text, top_n=7):
    """Find most relevant keywords between internal and external"""
    internal_keywords = extract_clean_keywords(internal_text, max_words=2)
    external_keywords = extract_clean_keywords(external_text, max_words=2)
    
    if not internal_keywords and not external_keywords:
        return []
    
    all_keywords = list(set(internal_keywords + external_keywords))
    
    if len(all_keywords) > top_n:
        keyword_freq = {}
        for kw in internal_keywords + external_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
        
        sorted_keywords = sorted(all_keywords, key=lambda k: keyword_freq.get(k, 0), reverse=True)
        return sorted_keywords[:top_n]
    
    return all_keywords[:top_n]

print("=" * 80)
print("COMPUTING ALL MATCHES WITH IMPROVED ALGORITHM")
print("=" * 80)

# Load data
print("\n1. Loading data from Excel files...")
internal_df = pd.read_excel('HumberInternalResearch.xlsx')
external_df = pd.read_excel('ExternalResearch.xlsx')

print(f"   ✓ Loaded {len(internal_df)} internal researchers")
print(f"   ✓ Loaded {len(external_df)} external researchers")
print(f"   ✓ Total matches to compute: {len(internal_df)} × {len(external_df)} = {len(internal_df) * len(external_df)}")

# Rename columns
internal_df = internal_df.rename(columns={
    "Your Name": "name",
    "Email Address": "email",
    "Your Faculty/Department": "faculty_department",
    internal_df.columns[4]: "primary_areas",
    internal_df.columns[5]: "experience_summary",
    internal_df.columns[6]: "sectors_interested"
})

external_df = external_df.rename(columns={
    "Your Name": "name",
    "Email Address": "email",
    "Your Orgnization": "organization",
    external_df.columns[4]: "organization_focus",
    external_df.columns[5]: "challenge_description",
    external_df.columns[6]: "expertise_sought",
    external_df.columns[7]: "lab_tours_interested"
})

# Build text for matching
print("\n2. Preprocessing text (removing stopwords, tokenizing)...")

internal_df['text_for_match'] = (
    internal_df['primary_areas'].fillna('') + '. ' +
    internal_df['experience_summary'].fillna('') + '. ' +
    internal_df['sectors_interested'].fillna('')
).apply(preprocess_text)

external_df['text_for_match'] = (
    external_df['expertise_sought'].fillna('') + '. ' +
    external_df['organization_focus'].fillna('') + '. ' +
    external_df['challenge_description'].fillna('')
).apply(preprocess_text)

print("   ✓ Text preprocessing complete")

# Load model
print("\n3. Loading Sentence Transformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
print("   ✓ Model loaded")

# Generate embeddings
print("\n4. Generating embeddings...")
internal_embeddings = model.encode(
    internal_df['text_for_match'].tolist(),
    normalize_embeddings=True,
    show_progress_bar=True
)
external_embeddings = model.encode(
    external_df['text_for_match'].tolist(),
    normalize_embeddings=True,
    show_progress_bar=True
)
print("   ✓ Embeddings generated")

# Compute similarity matrix
print("\n5. Computing similarity matrix...")
similarity_matrix = cosine_similarity(external_embeddings, internal_embeddings)
print(f"   ✓ Similarity matrix shape: {similarity_matrix.shape}")

# Build matches list
print("\n6. Building matches list with keywords...")
all_matches = []

for ext_idx, ext_row in external_df.iterrows():
    for int_idx, int_row in internal_df.iterrows():
        similarity_score = float(similarity_matrix[ext_idx, int_idx])
        
        # Only include meaningful matches
        if similarity_score > 0.1:
            # Get keywords
            internal_text = (int_row['primary_areas'] or '') + ' ' + \
                          (int_row['experience_summary'] or '') + ' ' + \
                          (int_row['sectors_interested'] or '')
            
            external_text = (ext_row['expertise_sought'] or '') + ' ' + \
                          (ext_row['organization_focus'] or '') + ' ' + \
                          (ext_row['challenge_description'] or '')
            
            keywords = find_relevant_keywords(internal_text, external_text, top_n=7)
            keywords_str = ', '.join(keywords[:7])
            
            all_matches.append({
                'internal_name': int_row['name'],
                'internal_email': int_row['email'],
                'faculty_department': int_row['faculty_department'],
                'external_name': ext_row['name'],
                'external_email': ext_row['email'],
                'organization': ext_row['organization'],
                'similarity_score': similarity_score,
                'similarity_percentage': round(similarity_score * 100, 2),
                'matching_keywords': keywords_str
            })
    
    if (ext_idx + 1) % 10 == 0:
        print(f"   ✓ Processed {ext_idx + 1}/{len(external_df)} external researchers")

print(f"   ✓ Total matches found: {len(all_matches)}")

# Sort by similarity score
print("\n7. Sorting matches by score...")
matches_df = pd.DataFrame(all_matches)
matches_df = matches_df.sort_values('similarity_percentage', ascending=False).reset_index(drop=True)
matches_df['rank'] = range(1, len(matches_df) + 1)

# Reorder columns
matches_df = matches_df[[
    'rank',
    'internal_name',
    'internal_email',
    'faculty_department',
    'external_name',
    'external_email',
    'organization',
    'similarity_percentage',
    'matching_keywords'
]]

print(f"   ✓ Matches sorted (highest score: {matches_df['similarity_percentage'].max():.2f}%)")

# Save to Excel
print("\n8. Saving to Excel files...")

# All matches
all_matches_file = 'all_matches_sorted.xlsx'
matches_df.to_excel(all_matches_file, index=False, sheet_name='All Matches')
print(f"   ✓ Saved all {len(matches_df)} matches to: {all_matches_file}")

# Top 20
top20_df = matches_df.head(20).copy()
top20_file = 'top20_matches.xlsx'
top20_df.to_excel(top20_file, index=False, sheet_name='Top 20')
print(f"   ✓ Saved top 20 matches to: {top20_file}")

# Display top 20
print("\n" + "=" * 80)
print("TOP 20 HIGHEST-SCORING MATCHES")
print("=" * 80)
print(top20_df[['rank', 'internal_name', 'external_name', 'organization', 'similarity_percentage']].to_string(index=False))

print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
print(f"\nFiles created:")
print(f"  1. {all_matches_file} - All {len(matches_df)} matches sorted by score")
print(f"  2. {top20_file} - Top 20 matches ready for upload")
print("\nNext steps:")
print("  1. Review top20_matches.xlsx")
print("  2. Upload it via /admin/load-top20 route")
print("=" * 80)
