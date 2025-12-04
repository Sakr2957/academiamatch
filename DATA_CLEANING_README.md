# Data Cleaning Guide

## Removing Duplicate Emails from Excel Files

### Quick Start

```bash
python3 clean_duplicates.py
```

### What It Does

The `clean_duplicates.py` script:

1. **Reads** both Excel files:
   - `HumberInternalResearch.xlsx`
   - `ExternalResearch.xlsx`

2. **Identifies** duplicate email addresses (case-insensitive)

3. **Removes** duplicates, keeping only the **first occurrence**

4. **Saves** cleaned data to new files:
   - `HumberInternalResearch_cleaned.xlsx`
   - `ExternalResearch_cleaned.xlsx`

### Example Output

```
============================================================
Processing: HumberInternalResearch.xlsx
============================================================
✓ Loaded 97 rows

⚠️  Found 5 duplicate email(s):
   - lakshmi.rajan@humber.ca (row 45)
   - lakshmi.rajan@humber.ca (row 67)
   - john.doe@humber.ca (row 78)
   - jane.smith@humber.ca (row 82)
   - bob.jones@humber.ca (row 91)

✓ Saved cleaned data to: HumberInternalResearch_cleaned.xlsx
✓ Original rows: 97
✓ Cleaned rows: 92
✓ Removed: 5 duplicate(s)
```

### After Cleaning

1. **Review** the cleaned files to ensure correctness

2. **Replace** the original files (if satisfied):
   ```bash
   mv HumberInternalResearch_cleaned.xlsx HumberInternalResearch.xlsx
   mv ExternalResearch_cleaned.xlsx ExternalResearch.xlsx
   ```

3. **Commit and push** to GitHub:
   ```bash
   git add *.xlsx
   git commit -m "Clean duplicate emails from Excel files"
   git push origin main
   ```

4. **Reload data** on Render:
   - Visit: `https://academiamatch.onrender.com/admin/nuclear-reset`
   - This will reload the cleaned data

### Important Notes

- ⚠️ **Backup your files** before replacing originals
- ✅ The script keeps the **first occurrence** of each email
- ✅ Email comparison is **case-insensitive**
- ✅ Whitespace is automatically trimmed

### Troubleshooting

**Error: File not found**
- Make sure you're in the repository root directory
- Check that the Excel files exist

**Error: Column not found**
- The script expects a column named "Email Address"
- Check your Excel file column names

**Need help?**
- Check the error message and traceback
- Verify Excel files are not corrupted
- Ensure pandas and openpyxl are installed: `pip3 install pandas openpyxl`
