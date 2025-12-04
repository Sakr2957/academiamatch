# AcademiaMatch Update Summary

## What Was Fixed

### Problem
The matching algorithm was returning "No matches found" because:
1. Column names in `load_data.py` didn't match the actual Excel column names
2. This resulted in empty text fields for all researchers
3. The old matching algorithm couldn't match on empty fields

### Solution
1. **Updated data loading** to correctly map Excel columns
2. **Rewrote matching algorithm** to use Sentence Transformers (AI-powered semantic matching)
3. **Updated Excel files** with cleaned, merged data

---

## Technical Changes

### 1. New Matching Algorithm (matching.py)

**Old approach:**
- Simple keyword matching
- No semantic understanding
- Required exact word matches

**New approach:**
- Uses Sentence Transformers (`all-MiniLM-L6-v2` model)
- Converts text to semantic embeddings (384-dimensional vectors)
- Calculates cosine similarity between embeddings
- Understands meaning, not just keywords
- Returns similarity scores (0-1 scale)

**Example:**
- Old: "machine learning" only matches "machine learning"
- New: "machine learning" also matches "AI", "neural networks", "deep learning", etc.

### 2. Updated Data Loading (load_data.py)

**Changes:**
- Now loads 2 Excel files instead of 3
- Correctly maps long column names like:
  - "What are your primary areas of research or expertise?..."
  - "Please describe a challenge or business goal..."
- Preprocesses text data
- Handles missing values properly

**Column Mapping:**

**Internal Researchers (HumberInternalResearch.xlsx):**
- Column 1: Your Name → name
- Column 2: Email Address → email
- Column 3: Your Faculty/Department → faculty_department
- Column 4: What are your primary areas... → primary_areas
- Column 5: Please provide a brief summary... → experience_summary
- Column 6: What sectors or societal challenges... → sectors_interested

**External Researchers (ExternalResearch.xlsx):**
- Column 1: Your Name → name
- Column 2: Email Address → email
- Column 3: Your Orgnization → organization
- Column 4: What is your organization's primary area... → organization_focus
- Column 5: Please describe a challenge... → challenge_description
- Column 6: What type of expertise... → expertise_sought
- Column 7: Which lab tour(s)... → lab_tours_interested

### 3. Updated Dependencies (requirements.txt)

**Added:**
- `sentence-transformers==2.2.2` - For semantic embeddings
- `scikit-learn==1.3.2` - For cosine similarity calculation
- `torch==2.1.2` - Required by sentence-transformers
- `numpy==1.26.2` - Updated for compatibility

---

## How Matching Works Now

### For Internal Researchers:
1. **Input:** Internal researcher's email
2. **Process:**
   - Combines their expertise, experience summary, and sectors into one text
   - Converts to semantic embedding
   - Compares with all external researchers' embeddings
   - Calculates similarity scores
3. **Output:** Top 5 external researchers with similarity scores

### For External Researchers:
1. **Input:** External researcher's email
2. **Process:**
   - Combines their expertise sought, organization focus, and challenge into one text
   - Converts to semantic embedding
   - Compares with all internal researchers' embeddings
   - Calculates similarity scores
3. **Output:** Top 5 internal researchers with similarity scores

### Similarity Scores:
- **0.0 - 0.2:** Very low similarity (not shown)
- **0.2 - 0.4:** Low to moderate similarity
- **0.4 - 0.6:** Good similarity
- **0.6 - 0.8:** High similarity
- **0.8 - 1.0:** Very high similarity (rare, indicates very close match)

---

## Files You Need to Update

### 1. Code Files (in GitHub repository)
```
load_data.py          → Replace with new version
matching.py           → Replace with new version
requirements.txt      → Replace with new version
```

### 2. Excel Files (in GitHub repository)

**Delete:**
```
Humber Internal Research - Faculty.xlsx
Humber Internal Research - Staff.xlsx
External Research.xlsx (old version)
```

**Add:**
```
HumberInternalResearch.xlsx (new merged file)
ExternalResearch.xlsx (new cleaned file)
```

---

## Testing the New System

### Test 1: Internal Researcher Match
```
URL: https://academiamatch.onrender.com/match?email=serguei.mokhov@humber.ca
Expected: List of external researchers with similarity scores
```

### Test 2: External Researcher Match
```
URL: https://academiamatch.onrender.com/match?email=info@moricat.com
Expected: List of internal researchers with similarity scores
```

### Test 3: All Matches
```
URL: https://academiamatch.onrender.com/all-matches
Expected: All external researchers matched with top 3 internal researchers each
```

---

## Performance Notes

### First Request (after deployment)
- **Time:** 10-30 seconds
- **Reason:** Model needs to download and load (about 80MB)
- **Happens:** Only once per deployment

### Subsequent Requests
- **Time:** 1-3 seconds
- **Reason:** Model is cached in memory
- **Happens:** All requests after the first one

### Model Size
- **Model:** all-MiniLM-L6-v2
- **Size:** ~80MB
- **Speed:** Fast (optimized for production use)
- **Quality:** Good balance of speed and accuracy

---

## Why Sentence Transformers?

### Advantages:
1. **Semantic Understanding:** Understands meaning, not just keywords
2. **Robust:** Works even with typos, synonyms, different phrasings
3. **No Training Required:** Pre-trained model works out of the box
4. **Fast:** Optimized for production use
5. **Proven:** Used by major companies for semantic search

### Example Matches:
- "machine learning" matches "AI", "neural networks", "deep learning"
- "sustainable packaging" matches "eco-friendly materials", "green packaging"
- "healthcare innovation" matches "medical technology", "health tech"

---

## Architecture

```
User Request (email)
    ↓
Flask App (app.py)
    ↓
Matching Module (matching.py)
    ↓
Sentence Transformer Model
    ↓
Text → Embedding (384-dim vector)
    ↓
Cosine Similarity Calculation
    ↓
Top N Matches with Scores
    ↓
JSON Response
    ↓
Web Interface Display
```

---

## Database Schema (unchanged)

```python
Researcher:
  - id (primary key)
  - name
  - email (unique)
  - organization
  - researcher_type ('internal' or 'external')
  
  # Internal researcher fields:
  - faculty_department
  - primary_areas
  - experience_summary
  - sectors_interested
  
  # External researcher fields:
  - organization_focus
  - challenge_description
  - expertise_sought
  - lab_tours_interested
```

---

## Next Steps After Deployment

1. **Monitor first request:** It will be slow (model loading)
2. **Test with known emails:** Verify matches make sense
3. **Check similarity scores:** Should be in 0.2-0.8 range for good matches
4. **Gather feedback:** Ask users if matches are relevant
5. **Fine-tune if needed:** Can adjust top_n parameter or similarity threshold

---

## Maintenance

### Regular Tasks:
- No maintenance required for the model
- Reload data when Excel files are updated
- Monitor Render logs for errors

### Future Improvements:
- Add clustering for faster matching (already in reference code)
- Add filters (by faculty, sector, etc.)
- Export matches to Excel
- Email notifications for new matches

---

**The system is now ready for production use with AI-powered semantic matching! 🚀**
