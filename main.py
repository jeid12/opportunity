import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timezone
import re
import time
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import ssl
import urllib3
from google.auth.transport.urllib3 import AuthorizedHttp

def categorize_opportunity(text):
    """Categorize the type of opportunity based on text content"""
    text_lower = text.lower()
    
    categories = []
    
    # Job-related keywords
    job_keywords = ['job', 'career', 'employment', 'hiring', 'vacancy', 'position', 'recruit', 'work', 'intern']
    if any(keyword in text_lower for keyword in job_keywords):
        categories.append('Job')
    
    # Scholarship keywords
    scholarship_keywords = ['scholarship', 'financial aid', 'grant', 'funding', 'bursary', 'fellowship']
    if any(keyword in text_lower for keyword in scholarship_keywords):
        categories.append('Scholarship')
    
    # Training/Education keywords
    training_keywords = ['training', 'course', 'education', 'learn', 'bootcamp', 'workshop', 'skill', 'certification']
    if any(keyword in text_lower for keyword in training_keywords):
        categories.append('Training')
    
    # Competition/Challenge keywords
    competition_keywords = ['competition', 'challenge', 'hackathon', 'contest', 'prize']
    if any(keyword in text_lower for keyword in competition_keywords):
        categories.append('Competition')
    
    # Entrepreneurship keywords
    entrepreneur_keywords = ['entrepreneur', 'startup', 'business', 'innovation', 'venture']
    if any(keyword in text_lower for keyword in entrepreneur_keywords):
        categories.append('Entrepreneurship')
    
    return ', '.join(categories) if categories else 'Other'

def extract_deadline(text):
    """Extract deadline from text using various patterns"""
    if not text:
        return None
        
    text_lower = text.lower()
    
    # Common deadline patterns
    deadline_patterns = [
        r'deadline[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'due[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'closes?[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'expires?[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'apply by[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'deadline[:\s]*(\d{1,2}\s+\w+\s+\d{2,4})',
        r'due[:\s]*(\d{1,2}\s+\w+\s+\d{2,4})',
        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2},?\s+\d{2,4}'
    ]
    
    for pattern in deadline_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    
    return None

def is_deadline_passed(deadline_str):
    """Check if a deadline has passed"""
    if not deadline_str:
        return False
        
    current_date = datetime.now()
    
    try:
        # Try different date formats
        date_formats = [
            '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
            '%d.%m.%Y', '%m.%d.%Y', '%Y-%m-%d', '%Y/%m/%d',
            '%d %B %Y', '%d %b %Y', '%B %d, %Y', '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                deadline_date = datetime.strptime(deadline_str, fmt)
                return deadline_date < current_date
            except ValueError:
                continue
                
        # If no format matches, assume it's not passed to be safe
        return False
        
    except:
        return False

def extract_detailed_opportunities(soup, base_url):
    """Extract detailed opportunity information from webpage"""
    opportunities = []
    
    # Look for opportunity containers with more detailed selectors
    opportunity_selectors = [
        '.job-listing', '.opportunity', '.vacancy', '.position',
        '.scholarship', '.grant', '.fellowship', '.training',
        '.course', '.program', '.competition', '.challenge',
        '.job-item', '.career-item', '.listing', '.post',
        'article', '.entry', '.content-item'
    ]
    
    # Also look for links that might lead to opportunities
    link_selectors = [
        'a[href*="job"]', 'a[href*="career"]', 'a[href*="vacancy"]',
        'a[href*="scholarship"]', 'a[href*="grant"]', 'a[href*="funding"]',
        'a[href*="training"]', 'a[href*="course"]', 'a[href*="program"]',
        'a[href*="competition"]', 'a[href*="challenge"]', 'a[href*="hackathon"]',
        'a[href*="apply"]', 'a[href*="opportunity"]'
    ]
    
    processed_urls = set()
    
    # First, try to find detailed opportunity containers
    for selector in opportunity_selectors:
        try:
            elements = soup.select(selector)
            for element in elements[:8]:
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href') if title_elem.name == 'a' else element.find('a')
                link_url = link.get('href') if link and hasattr(link, 'get') else None
                
                if not link_url:
                    continue
                    
                # Make URL absolute
                if link_url.startswith('/'):
                    link_url = base_url.rstrip('/') + link_url
                elif not link_url.startswith('http'):
                    continue
                
                if link_url in processed_urls:
                    continue
                    
                # Extract description
                desc_elem = element.find(['p', '.description', '.summary', '.excerpt'])
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Get all text for deadline extraction
                full_text = element.get_text()
                deadline = extract_deadline(full_text)
                
                # Skip if deadline has passed
                if deadline and is_deadline_passed(deadline):
                    continue
                
                category = categorize_opportunity(f"{title} {description}")
                if category != 'Other':
                    opportunities.append({
                        'title': title[:200],
                        'description': description[:500] if description else 'No description available',
                        'deadline': deadline or 'Not specified',
                        'url': link_url,
                        'category': category
                    })
                    processed_urls.add(link_url)
                    
        except Exception as e:
            continue
    
    # If we didn't find many detailed opportunities, fall back to link extraction
    if len(opportunities) < 5:
        for selector in link_selectors:
            try:
                elements = soup.select(selector)
                for element in elements[:10]:
                    link_text = element.get_text(strip=True)
                    link_url = element.get('href', '')
                    
                    if not link_url or link_url in processed_urls:
                        continue
                        
                    if len(link_text) < 5:
                        continue
                    
                    # Make URL absolute
                    if link_url.startswith('/'):
                        link_url = base_url.rstrip('/') + link_url
                    elif not link_url.startswith('http'):
                        continue
                    
                    # Try to find description from parent or sibling elements
                    description = ""
                    parent = element.parent
                    if parent:
                        desc_elem = parent.find(['p', '.description', '.summary'])
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                    
                    # Look for deadline in surrounding text
                    surrounding_text = ""
                    if parent:
                        surrounding_text = parent.get_text()
                    deadline = extract_deadline(surrounding_text)
                    
                    # Skip if deadline has passed
                    if deadline and is_deadline_passed(deadline):
                        continue
                    
                    category = categorize_opportunity(link_text)
                    if category != 'Other':
                        opportunities.append({
                            'title': link_text[:200],
                            'description': description[:500] if description else 'No description available',
                            'deadline': deadline or 'Not specified',
                            'url': link_url,
                            'category': category
                        })
                        processed_urls.add(link_url)
                        
            except Exception as e:
                continue
    
    # Remove duplicates and limit results
    unique_opportunities = []
    seen_urls = set()
    for opp in opportunities:
        if opp['url'] not in seen_urls:
            seen_urls.add(opp['url'])
            unique_opportunities.append(opp)
    
    return unique_opportunities[:12]

def setup_google_sheets_auth():
    """Setup Google Sheets authentication with SSL fix"""
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    service_account_file = 'google_credentials.json'
    
    if not os.path.exists(service_account_file):
        print("⚠️  Missing Google credentials file.")
        return None
    
    try:
        credentials = Credentials.from_service_account_file(service_account_file, scopes=scope)

        # 🔥 Disable SSL verification globally for AuthorizedHttp
        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        authed_http = AuthorizedHttp(credentials, http)

        # 🔧 Monkey-patch gspread's default transport to use our insecure one
        gspread.auth.DEFAULT_HTTP_CLIENT = authed_http

        gc = gspread.authorize(credentials)
        return gc

    except Exception as e:
        print(f"❌ Failed to authenticate with Google Sheets: {e}")
        return None

def upload_to_google_sheets(results, sheet_name="Opportunities"):
    """Upload results to Google Sheets"""
    try:
        gc = setup_google_sheets_auth()
        if not gc:
            return False
        
        # Try to open existing spreadsheet or create new one
        try:
            spreadsheet = gc.open("Opportunity Scraper Results")
            print(f"📊 Found existing spreadsheet: Opportunity Scraper Results")
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create("Opportunity Scraper Results")
            print(f"📊 Created new spreadsheet: Opportunity Scraper Results")
            # Make it shareable (optional)
            spreadsheet.share('', perm_type='anyone', role='reader')
        
        # Try to select existing worksheet or create new one
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()  # Clear existing data
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
        
        # Prepare data for upload
        if results:
            # Get headers from first result
            headers = list(results[0].keys())
            
            # Prepare all data
            data = [headers]
            for result in results:
                row = [result.get(header, '') for header in headers]
                data.append(row)
            
            # Upload data
            worksheet.update('A1', data)
            
            # Format headers
            worksheet.format('A1:F1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, len(headers))
            
            print(f"✅ Successfully uploaded {len(results)} opportunities to Google Sheets!")
            print(f"🔗 Spreadsheet URL: {spreadsheet.url}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error uploading to Google Sheets: {e}")
        return False

# Step 1: Read URLs
with open("urls.txt", "r") as f:
    urls = [line.strip() for line in f if line.strip()]

results = []

# Step 2: Crawl each URL
print(f"Starting to crawl {len(urls)} websites for opportunities...")

for i, url in enumerate(urls, 1):
    print(f"Crawling {i}/{len(urls)}: {url}")
    
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract detailed opportunities from the page
        opportunities = extract_detailed_opportunities(soup, url)
        
        if opportunities:
            # Add each opportunity as a separate row
            for opp in opportunities:
                results.append({
                    "opportunity_title": opp['title'],
                    "description": opp['description'],
                    "deadline": opp['deadline'],
                    "link": opp['url'],
                    "category": opp['category'],
                    "crawled_at": datetime.now(timezone.utc).isoformat()
                })
        else:
            # If no specific opportunities found, check the main page
            title = soup.title.string.strip() if soup.title else "No title"
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc["content"].strip() if meta_desc else "No description"
            
            # Check if main page itself is an opportunity
            main_category = categorize_opportunity(f"{title} {description} {url}")
            if main_category != 'Other':
                results.append({
                    "opportunity_title": title,
                    "description": description,
                    "deadline": "Not specified",
                    "link": url,
                    "category": main_category,
                    "crawled_at": datetime.now(timezone.utc).isoformat()
                })
            
    except Exception as e:
        print(f"Error crawling {url}: {str(e)}")
        results.append({
            "opportunity_title": "ERROR",
            "description": str(e),
            "deadline": "N/A",
            "link": url,
            "category": "Error",
            "crawled_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Add small delay to be respectful to servers
    time.sleep(1)

# Step 3: Save results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"output/opportunities_{timestamp}.csv"

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

fieldnames = [
    "opportunity_title", "description", "deadline", "link", "category", "crawled_at"
]

try:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"✅ Crawl complete! Found {len(results)} opportunities saved to {output_file}")
except PermissionError:
    # Try alternative filename if file is locked
    alternative_file = f"output/opportunities_backup_{timestamp}.csv"
    try:
        with open(alternative_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"✅ Original file was locked. Saved to {alternative_file}")
        output_file = alternative_file
    except Exception as e:
        print(f"❌ Error saving CSV file: {e}")
        print("📊 Data will still be uploaded to Google Sheets if configured.")
        output_file = None

# Print summary statistics
categories = {}
for result in results:
    cat = result['category']
    categories[cat] = categories.get(cat, 0) + 1

print("\n📊 Opportunity Categories Found:")
for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category}: {count}")

# Count opportunities with deadlines
with_deadlines = sum(1 for r in results if r['deadline'] != 'Not specified' and r['deadline'] != 'N/A')
print(f"\n📅 Opportunities with specified deadlines: {with_deadlines}")
print(f"🔗 Total websites crawled: {len(urls)}")
print(f"📝 Total opportunities extracted: {len(results)}")

# Upload to Google Sheets
print("\n🚀 Uploading to Google Sheets...")
upload_success = upload_to_google_sheets(results)
if upload_success:
    print("🎉 Data successfully uploaded to Google Sheets!")
elif output_file:
    print("💡 Data is available in the CSV file for manual upload.")
else:
    print("⚠️  CSV save failed and Google Sheets not configured.")
    print("📋 Data is available in memory but not saved. Please check file permissions.")
