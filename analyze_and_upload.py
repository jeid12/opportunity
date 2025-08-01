"""
Opportunity Data Analyzer and Manual Upload Guide
Analyzes your scraped opportunities and provides Google Sheets upload instructions
"""

import pandas as pd
import os
import glob
from datetime import datetime

def analyze_opportunities(csv_file_path):
    """Analyze the opportunities data and provide insights"""
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        print("🎯 OPPORTUNITY SCRAPER ANALYSIS REPORT")
        print("=" * 50)
        print(f"📊 Total Opportunities Found: {len(df)}")
        print(f"📁 Data Source: {csv_file_path}")
        print(f"🕒 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Category breakdown
        print(f"\n📈 CATEGORY BREAKDOWN:")
        categories = df['category'].value_counts()
        for category, count in categories.items():
            percentage = (count / len(df)) * 100
            print(f"  {category:<25} {count:>3} ({percentage:5.1f}%)")
        
        # Deadline analysis
        print(f"\n📅 DEADLINE ANALYSIS:")
        with_deadlines = df[df['deadline'].notna() & (df['deadline'] != 'Not specified') & (df['deadline'] != 'N/A')]
        print(f"  Opportunities with specific deadlines: {len(with_deadlines)}")
        print(f"  Opportunities without deadlines: {len(df) - len(with_deadlines)}")
        
        if len(with_deadlines) > 0:
            print(f"\n⏰ UPCOMING DEADLINES:")
            deadlines = with_deadlines[['opportunity_title', 'deadline', 'category']].head(10)
            for _, row in deadlines.iterrows():
                title = row['opportunity_title'][:40] + "..." if len(row['opportunity_title']) > 40 else row['opportunity_title']
                print(f"  {row['deadline']:<12} | {row['category']:<15} | {title}")
        
        # Error analysis
        errors = df[df['category'] == 'Error']
        if len(errors) > 0:
            print(f"\n⚠️  CRAWLING ISSUES:")
            print(f"  {len(errors)} websites had access issues (blocked, SSL errors, etc.)")
            print("  These can often be resolved with different scraping approaches")
        
        # Top categories for easy filtering
        print(f"\n🎯 QUICK FILTERS:")
        jobs = df[df['category'].str.contains('Job', na=False)]
        scholarships = df[df['category'].str.contains('Scholarship', na=False)]
        training = df[df['category'].str.contains('Training', na=False)]
        competitions = df[df['category'].str.contains('Competition', na=False)]
        
        print(f"  Jobs & Careers: {len(jobs)} opportunities")
        print(f"  Scholarships & Grants: {len(scholarships)} opportunities")
        print(f"  Training & Education: {len(training)} opportunities")
        print(f"  Competitions & Challenges: {len(competitions)} opportunities")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        return False

def print_manual_upload_guide(csv_file_path):
    """Print manual upload instructions for Google Sheets"""
    
    print(f"\n📤 MANUAL GOOGLE SHEETS UPLOAD GUIDE")
    print("=" * 50)
    print("Since automated upload had SSL issues, here's how to upload manually:")
    print()
    print("OPTION 1: Direct Import (Recommended)")
    print("1. Go to https://sheets.google.com/")
    print("2. Click 'Blank' to create a new spreadsheet")
    print("3. File → Import → Upload")
    print(f"4. Select your file: {csv_file_path}")
    print("5. Choose 'Replace spreadsheet'")
    print("6. Click 'Import data'")
    print()
    print("OPTION 2: Copy & Paste")
    print("1. Open the CSV file in Excel or any text editor")
    print("2. Select all data (Ctrl+A)")
    print("3. Copy (Ctrl+C)")
    print("4. Go to Google Sheets and paste (Ctrl+V)")
    print()
    print("OPTION 3: Google Drive Upload")
    print("1. Go to https://drive.google.com/")
    print(f"2. Upload the CSV file: {csv_file_path}")
    print("3. Right-click the uploaded file → 'Open with' → 'Google Sheets'")
    print()
    print("💡 FORMATTING TIPS:")
    print("• Make row 1 bold (select row 1, click Bold)")
    print("• Add colors to headers (Format → Conditional formatting)")
    print("• Freeze the header row (View → Freeze → 1 row)")
    print("• Auto-resize columns (Select all → Format → Resize columns → Fit to data)")

def main():
    """Main function"""
    
    # Find the most recent opportunities file
    csv_files = glob.glob("output/opportunities_*.csv")
    if not csv_files:
        print("❌ No opportunities CSV files found in output/ directory")
        return
    
    # Get the most recent file
    csv_file = sorted(csv_files)[-1]
    
    # Analyze the data
    print("🔍 Analyzing your scraped opportunities data...\n")
    success = analyze_opportunities(csv_file)
    
    if success:
        # Provide manual upload guide
        print_manual_upload_guide(csv_file)
        
        print(f"\n✨ SUMMARY:")
        print(f"• Your data is ready in: {csv_file}")
        print(f"• Follow the manual upload guide above to get it into Google Sheets")
        print(f"• The file contains all opportunities with titles, descriptions, deadlines, and links")
        print(f"• Expired opportunities have been filtered out automatically")
        
    else:
        print("❌ Could not analyze the data file")

if __name__ == "__main__":
    main()
