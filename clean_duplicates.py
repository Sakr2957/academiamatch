#!/usr/bin/env python3
"""
Excel Data Cleaning Script - Remove Duplicate Emails
====================================================

This script removes duplicate email addresses from the Excel files,
keeping only the first occurrence of each email.

Usage:
    python3 clean_duplicates.py

Files processed:
    - HumberInternalResearch.xlsx
    - ExternalResearch.xlsx

Output:
    - HumberInternalResearch_cleaned.xlsx
    - ExternalResearch_cleaned.xlsx
"""

import pandas as pd
import sys

def clean_excel_file(input_file, output_file, email_column='Email Address'):
    """
    Remove duplicate emails from an Excel file.
    
    Args:
        input_file: Path to input Excel file
        output_file: Path to output Excel file
        email_column: Name of the email column
    """
    try:
        print(f"\n{'='*60}")
        print(f"Processing: {input_file}")
        print(f"{'='*60}")
        
        # Read Excel file
        df = pd.read_excel(input_file)
        original_count = len(df)
        print(f"✓ Loaded {original_count} rows")
        
        # Check if email column exists
        if email_column not in df.columns:
            print(f"❌ Error: Column '{email_column}' not found!")
            print(f"Available columns: {', '.join(df.columns)}")
            return False
        
        # Normalize emails (lowercase, strip whitespace)
        df[email_column] = df[email_column].astype(str).str.lower().str.strip()
        
        # Find duplicates
        duplicates = df[df.duplicated(subset=[email_column], keep='first')]
        duplicate_count = len(duplicates)
        
        if duplicate_count > 0:
            print(f"\n⚠️  Found {duplicate_count} duplicate email(s):")
            for idx, row in duplicates.iterrows():
                print(f"   - {row[email_column]} (row {idx + 2})")  # +2 because Excel is 1-indexed and has header
        else:
            print(f"\n✅ No duplicates found!")
        
        # Remove duplicates (keep first occurrence)
        df_cleaned = df.drop_duplicates(subset=[email_column], keep='first')
        cleaned_count = len(df_cleaned)
        
        # Save cleaned data
        df_cleaned.to_excel(output_file, index=False)
        print(f"\n✓ Saved cleaned data to: {output_file}")
        print(f"✓ Original rows: {original_count}")
        print(f"✓ Cleaned rows: {cleaned_count}")
        print(f"✓ Removed: {duplicate_count} duplicate(s)")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found!")
        return False
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to clean both Excel files."""
    print("\n" + "="*60)
    print("Excel Data Cleaning Script")
    print("Removing Duplicate Email Addresses")
    print("="*60)
    
    # Clean internal researchers file
    success1 = clean_excel_file(
        'HumberInternalResearch.xlsx',
        'HumberInternalResearch_cleaned.xlsx',
        'Email Address'
    )
    
    # Clean external researchers file
    success2 = clean_excel_file(
        'ExternalResearch.xlsx',
        'ExternalResearch_cleaned.xlsx',
        'Email Address'
    )
    
    # Summary
    print("\n" + "="*60)
    if success1 and success2:
        print("✅ All files cleaned successfully!")
        print("\nNext steps:")
        print("1. Review the cleaned files:")
        print("   - HumberInternalResearch_cleaned.xlsx")
        print("   - ExternalResearch_cleaned.xlsx")
        print("2. If satisfied, replace the original files:")
        print("   mv HumberInternalResearch_cleaned.xlsx HumberInternalResearch.xlsx")
        print("   mv ExternalResearch_cleaned.xlsx ExternalResearch.xlsx")
        print("3. Commit and push to GitHub")
    else:
        print("❌ Some files failed to process. Check errors above.")
        sys.exit(1)
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
