# File Update Checklist

## Files to Update in GitHub Repository

### ✅ Code Files (Replace Entire Content)

#### 1. load_data.py
- [ ] Open `load_data.py` in GitHub
- [ ] Click "Edit" button
- [ ] Select all content (Ctrl+A / Cmd+A)
- [ ] Delete
- [ ] Copy entire content from new `load_data.py`
- [ ] Paste
- [ ] Commit changes with message: "Update load_data.py for new Excel structure"

**Key changes:**
- Now loads 2 files instead of 3
- Correct column name mapping
- Text preprocessing added

---

#### 2. matching.py
- [ ] Open `matching.py` in GitHub
- [ ] Click "Edit" button
- [ ] Select all content (Ctrl+A / Cmd+A)
- [ ] Delete
- [ ] Copy entire content from new `matching.py`
- [ ] Paste
- [ ] Commit changes with message: "Implement Sentence Transformers matching"

**Key changes:**
- Complete rewrite
- Uses AI-powered semantic matching
- Returns similarity scores

---

#### 3. requirements.txt
- [ ] Open `requirements.txt` in GitHub
- [ ] Click "Edit" button
- [ ] Select all content (Ctrl+A / Cmd+A)
- [ ] Delete
- [ ] Copy entire content from new `requirements.txt`
- [ ] Paste
- [ ] Commit changes with message: "Add sentence-transformers dependencies"

**Key changes:**
- Added sentence-transformers
- Added scikit-learn
- Added torch

---

### ❌ Excel Files to DELETE

#### Delete these 3 old files:
- [ ] Delete `Humber Internal Research - Faculty.xlsx`
  - Click on file → Click trash icon → Commit deletion
  
- [ ] Delete `Humber Internal Research - Staff.xlsx`
  - Click on file → Click trash icon → Commit deletion
  
- [ ] Delete `External Research.xlsx` (old version)
  - Click on file → Click trash icon → Commit deletion

---

### ➕ Excel Files to ADD

#### Upload these 2 new files:
- [ ] Upload `HumberInternalResearch.xlsx`
  - Click "Add file" → "Upload files"
  - Drag and drop file
  - Commit with message: "Add merged internal researchers file"

- [ ] Upload `ExternalResearch.xlsx`
  - Click "Add file" → "Upload files"
  - Drag and drop file
  - Commit with message: "Add updated external researchers file"

---

## Deployment Steps

### On Render.com
- [ ] Go to https://dashboard.render.com
- [ ] Click on `academiamatch` service
- [ ] Click "Manual Deploy" button
- [ ] Select "Deploy latest commit"
- [ ] Wait for deployment to complete (5-10 minutes)
- [ ] Check logs for "Build successful" message

---

## Post-Deployment Steps

### Load Data
- [ ] Visit: https://academiamatch.onrender.com/admin/load-data
- [ ] Wait for success message
- [ ] Verify counts: ~89 internal, ~38 external

### Test Matching
- [ ] Test internal researcher: https://academiamatch.onrender.com/match?email=serguei.mokhov@humber.ca
- [ ] Verify matches are returned with similarity scores
- [ ] Test external researcher: https://academiamatch.onrender.com/match?email=info@moricat.com
- [ ] Verify matches are returned with similarity scores

### Verify All Matches
- [ ] Visit: https://academiamatch.onrender.com/all-matches
- [ ] Verify all external researchers have matches
- [ ] Check similarity scores are reasonable (20-80%)

---

## Summary

**Total files to update:** 3 code files
**Total files to delete:** 3 old Excel files
**Total files to add:** 2 new Excel files

**Total time:** ~15-20 minutes (including deployment wait time)

---

## Quick Reference

### GitHub Repository Structure (After Update)
```
academiamatch/
├── app.py (no changes needed)
├── models.py (no changes needed)
├── load_data.py (✅ UPDATED)
├── matching.py (✅ UPDATED)
├── requirements.txt (✅ UPDATED)
├── runtime.txt (no changes needed)
├── HumberInternalResearch.xlsx (✅ NEW)
├── ExternalResearch.xlsx (✅ NEW)
└── templates/
    └── (no changes needed)
```

### Files Removed
```
❌ Humber Internal Research - Faculty.xlsx (DELETED)
❌ Humber Internal Research - Staff.xlsx (DELETED)
❌ External Research.xlsx (old version) (DELETED)
```

---

**Once all checkboxes are checked, your deployment is complete! 🎉**
