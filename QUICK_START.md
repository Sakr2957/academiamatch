# Quick Start Guide - AcademiaMatch Update

## 🚀 Quick Deployment (5 Steps)

### Step 1: Update Code Files in GitHub
Go to your GitHub repository and replace these 3 files:

1. **load_data.py** → Copy content from the new `load_data.py`
2. **matching.py** → Copy content from the new `matching.py`
3. **requirements.txt** → Copy content from the new `requirements.txt`

### Step 2: Update Excel Files in GitHub

**Delete these old files:**
- `Humber Internal Research - Faculty.xlsx`
- `Humber Internal Research - Staff.xlsx`
- `External Research.xlsx` (old version)

**Upload these new files:**
- `HumberInternalResearch.xlsx`
- `ExternalResearch.xlsx`

### Step 3: Deploy on Render
1. Go to https://dashboard.render.com
2. Click on your `academiamatch` service
3. Click "Manual Deploy" → "Deploy latest commit"
4. Wait 5-10 minutes for deployment to complete

### Step 4: Load Data
Visit: https://academiamatch.onrender.com/admin/load-data

This will clear the database and reload all researchers from the new Excel files.

### Step 5: Test Matching
Visit: https://academiamatch.onrender.com/match?email=serguei.mokhov@humber.ca

You should see external researchers with similarity scores!

---

## ✅ What You Should See

### Homepage
```
Academia Match - Researcher Matching System

Total Researchers: 127
Internal Researchers: 89
External Researchers: 38
```

### Match Results
```
Matches for: Serguei Mokhov

Top 5 Matches:
1. Rebecca Li (Moricat) - 67.5% match
   Organization Focus: Ecommerce, AI content tools...
   Expertise Sought: Sewing and soft-goods prototyping...
   
2. [Next match...]
```

---

## 📁 Files Included

### Code Files
- `load_data.py` - Updated data loader for new Excel files
- `matching.py` - New AI-powered matching algorithm
- `requirements.txt` - Updated dependencies

### Data Files
- `HumberInternalResearch.xlsx` - 89 internal researchers
- `ExternalResearch.xlsx` - 38 external researchers

### Documentation
- `QUICK_START.md` - This file
- `DEPLOYMENT_INSTRUCTIONS.md` - Detailed deployment guide
- `CHANGES_SUMMARY.md` - Technical details of changes

---

## ⚠️ Important Notes

1. **First request will be slow (10-30 seconds)** - The AI model needs to load
2. **Subsequent requests will be fast (1-3 seconds)**
3. **Don't push to GitHub yourself** - Just copy/paste the code
4. **Make sure to delete old Excel files** - Otherwise you'll have duplicates

---

## 🧪 Test URLs

After deployment, test these URLs:

1. **Homepage:** https://academiamatch.onrender.com
2. **Load Data:** https://academiamatch.onrender.com/admin/load-data
3. **Match Internal:** https://academiamatch.onrender.com/match?email=serguei.mokhov@humber.ca
4. **Match External:** https://academiamatch.onrender.com/match?email=info@moricat.com
5. **All Matches:** https://academiamatch.onrender.com/all-matches

---

## 🆘 Troubleshooting

**Problem:** "No matches found"
- **Solution:** Visit `/admin/load-data` to reload data

**Problem:** Deployment takes forever
- **Solution:** Normal! Installing AI libraries takes 5-10 minutes

**Problem:** First request is very slow
- **Solution:** Normal! AI model is loading (only happens once)

---

## 📊 What Changed?

**Old System:**
- Simple keyword matching
- Returned no matches (broken column mapping)

**New System:**
- AI-powered semantic matching
- Understands meaning, not just keywords
- Returns similarity scores (0-100%)
- Much more accurate matches

---

## 🎯 Expected Results

**Good matches:** 40-80% similarity
**Great matches:** 60-80% similarity
**Perfect matches:** 80%+ similarity (rare)

Matches below 20% similarity are filtered out.

---

**Need more details? See DEPLOYMENT_INSTRUCTIONS.md**
