# AcademiaMatch Deployment Instructions

## Overview
This guide will help you update your AcademiaMatch application with the new Sentence Transformers matching algorithm and updated Excel data files.

---

## Files to Update in GitHub Repository

### 1. **Code Files** (Copy/Paste the new versions)
- `load_data.py` - Updated to handle new Excel file structure
- `matching.py` - Complete rewrite with Sentence Transformers + Cosine Similarity
- `requirements.txt` - Added sentence-transformers and dependencies

### 2. **Excel Data Files** (Replace old files)
**REMOVE these old files:**
- `Humber Internal Research - Faculty.xlsx`
- `Humber Internal Research - Staff.xlsx`
- `External Research.xlsx` (old version)

**ADD these new files:**
- `HumberInternalResearch.xlsx` (merged internal researchers)
- `ExternalResearch.xlsx` (new cleaned version)

### 3. **Optional: Update app.py** (if you want model preloading)
Add this import at the top:
```python
from matching import preload_model
```

Add this line in the `create_tables()` function, AFTER the `db.create_all()` line:
```python
# Preload the Sentence Transformer model
preload_model()
```

---

## Step-by-Step Deployment Process

### Step 1: Update Files in GitHub

1. **Navigate to your GitHub repository** (academiamatch or whatever it's named)

2. **Update code files:**
   - Click on `load_data.py` → Edit → Replace entire content with new version → Commit
   - Click on `matching.py` → Edit → Replace entire content with new version → Commit
   - Click on `requirements.txt` → Edit → Replace entire content with new version → Commit

3. **Delete old Excel files:**
   - Click on `Humber Internal Research - Faculty.xlsx` → Delete file → Commit
   - Click on `Humber Internal Research - Staff.xlsx` → Delete file → Commit
   - Click on `External Research.xlsx` → Delete file → Commit

4. **Upload new Excel files:**
   - Click "Add file" → "Upload files"
   - Upload `HumberInternalResearch.xlsx`
   - Upload `ExternalResearch.xlsx`
   - Commit changes

### Step 2: Deploy on Render

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Find your web service** (`academiamatch`)

3. **Trigger manual deploy:**
   - Click on your service
   - Click "Manual Deploy" → "Deploy latest commit"
   - Wait for deployment to complete (this may take 5-10 minutes due to installing sentence-transformers)

4. **Monitor the deployment logs:**
   - Watch for any errors
   - Look for "Build successful" and "Service is live"

### Step 3: Clear Database and Reload Data

1. **Navigate to your app**: https://academiamatch.onrender.com

2. **Load new data:**
   - Go to: https://academiamatch.onrender.com/admin/load-data
   - This will:
     - Clear all existing data
     - Load researchers from `HumberInternalResearch.xlsx`
     - Load researchers from `ExternalResearch.xlsx`
   - You should see a success message with counts

3. **Verify data loaded:**
   - Go to homepage: https://academiamatch.onrender.com
   - Check that researcher counts are displayed correctly

### Step 4: Test Matching Functionality

1. **Test with an internal researcher email:**
   - Go to: https://academiamatch.onrender.com/match?email=<internal-email>
   - Example: `https://academiamatch.onrender.com/match?email=serguei.mokhov@humber.ca`
   - You should see top 5 external researchers with similarity scores

2. **Test with an external researcher email:**
   - Go to: https://academiamatch.onrender.com/match?email=<external-email>
   - Example: `https://academiamatch.onrender.com/match?email=info@moricat.com`
   - You should see top 5 internal researchers with similarity scores

3. **View all matches:**
   - Go to: https://academiamatch.onrender.com/all-matches
   - This shows all external researchers matched with top 3 internal researchers each

---

## What Changed?

### 1. **Data Loading (`load_data.py`)**
- Now loads from 2 files instead of 3 (internal researchers merged into one file)
- Correctly maps column names from new Excel files
- Handles long column names properly
- Cleans and preprocesses text data

### 2. **Matching Algorithm (`matching.py`)**
- **Complete rewrite** using Sentence Transformers
- Uses `all-MiniLM-L6-v2` model for semantic embeddings
- Calculates cosine similarity between embeddings
- Returns similarity scores (0-1 scale, also shown as percentage)
- Much more accurate than keyword-based matching
- Preloads model to avoid delays on first request

### 3. **Dependencies (`requirements.txt`)**
- Added `sentence-transformers==2.2.2`
- Added `scikit-learn==1.3.2` (for cosine similarity)
- Added `torch==2.1.2` (required by sentence-transformers)
- Updated numpy version for compatibility

---

## Troubleshooting

### Issue: Deployment takes a long time
**Solution:** This is normal. Installing sentence-transformers and PyTorch can take 5-10 minutes on Render's free tier.

### Issue: "No matches found"
**Possible causes:**
1. Data not loaded - visit `/admin/load-data` first
2. Email not in database - check email spelling
3. Empty text fields - verify Excel files have content

### Issue: Build fails on Render
**Possible causes:**
1. requirements.txt not updated correctly
2. Syntax error in Python files
3. Check Render logs for specific error message

### Issue: Model loading is slow
**Solution:** The first request after deployment will be slow (10-30 seconds) as the model downloads and loads. Subsequent requests will be fast. Consider adding model preloading to app.py as mentioned above.

---

## Expected Performance

- **First request after deployment:** 10-30 seconds (model loading)
- **Subsequent requests:** 1-3 seconds
- **Accuracy:** Much better than keyword matching, uses semantic understanding
- **Similarity scores:** Typically range from 0.2 to 0.8 for good matches

---

## Database Information

- **Platform:** Render PostgreSQL
- **Database name:** academiamatch-db
- **Connection:** Already configured in Render environment variables
- **Data persistence:** Data persists across deployments unless you run `/admin/load-data`

---

## Support

If you encounter issues:
1. Check Render deployment logs
2. Check browser console for JavaScript errors
3. Verify Excel files are uploaded correctly to GitHub
4. Ensure all code files are updated with new versions

---

## Summary Checklist

- [ ] Updated `load_data.py` in GitHub
- [ ] Updated `matching.py` in GitHub
- [ ] Updated `requirements.txt` in GitHub
- [ ] Deleted old Excel files from GitHub
- [ ] Uploaded new Excel files to GitHub
- [ ] Triggered manual deploy on Render
- [ ] Waited for deployment to complete
- [ ] Visited `/admin/load-data` to reload data
- [ ] Tested matching with sample emails
- [ ] Verified similarity scores are displayed
- [ ] Confirmed matches make sense semantically

---

**Your app should now be using AI-powered semantic matching with Sentence Transformers! 🎉**
