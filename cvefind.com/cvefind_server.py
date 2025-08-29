#!/usr/bin/env python3
"""
CVEFind.com Server - Single endpoint that scrapes and returns today's CVEs from CVEFind.com
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import time
from datetime import date, datetime
import re
import json

app = Flask(__name__)
CORS(app)

def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    return date.today().strftime('%Y-%m-%d')

def get_csrf_token():
    """Get CSRF token from CVEFind.com CVE table page"""
    # Try multiple URLs where CSRF token might be present
    urls_to_try = [
        "https://www.cvefind.com/cve/",
        "https://www.cvefind.com/cve/table",
        "https://www.cvefind.com/",
        "https://www.cvefind.com/en/"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    for url in urls_to_try:
        try:
            print(f"Trying to fetch CSRF token from: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            print(f"Response status: {response.status_code}")
            print(f"Response content length: {len(response.content)}")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try multiple ways to find CSRF token
            csrf_input = soup.find('input', {'name': 'csrf'})
            if csrf_input and csrf_input.get('value'):
                csrf_token = csrf_input.get('value')
                print(f"CSRF token found via input[name='csrf']: {csrf_token[:20]}...")
                return csrf_token

            # Try finding by tw attribute
            csrf_input_tw = soup.find('input', {'tw': 'csrf'})
            if csrf_input_tw and csrf_input_tw.get('value'):
                csrf_token = csrf_input_tw.get('value')
                print(f"CSRF token found via input[tw='csrf']: {csrf_token[:20]}...")
                return csrf_token

            # Try finding any input with 'csrf' in value
            all_inputs = soup.find_all('input')
            for inp in all_inputs:
                if inp.get('name') and 'csrf' in inp.get('name', '').lower():
                    csrf_token = inp.get('value')
                    if csrf_token:
                        print(f"CSRF token found via name containing 'csrf': {csrf_token[:20]}...")
                        return csrf_token

            # Try to find in script tags or meta tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'csrf' in script.string.lower():
                    # Look for csrf token in JavaScript
                    csrf_match = re.search(r'csrf["\']?\s*[:=]\s*["\']([a-f0-9]{32,})["\']', script.string, re.IGNORECASE)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        print(f"CSRF token found in script: {csrf_token[:20]}...")
                        return csrf_token

            print(f"CSRF token not found on {url}")

        except Exception as e:
            print(f"Error fetching from {url}: {e}")
            continue

    # If no CSRF token found, try to proceed without it or use a dummy token
    print("No CSRF token found on any page. Trying to proceed without CSRF or with dummy token...")

    # Sometimes APIs work without CSRF or with empty CSRF
    return ""  # Return empty string instead of None

def fetch_cve_data(csrf_token, start=0, length=100, draw=1):
    """Fetch CVE data from CVEFind.com API"""
    url = "https://www.cvefind.com/api/cve/getCveDt"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.cvefind.com',
        'Connection': 'keep-alive',
        'Referer': 'https://www.cvefind.com/'
    }
    
    # Prepare the search value with CSRF token
    search_value = json.dumps({"csrf": csrf_token})
    
    # Prepare form data exactly like the browser request
    data = {
        'draw': str(draw),
        'columns[0][data]': 'id',
        'columns[0][name]': '',
        'columns[0][searchable]': 'true',
        'columns[0][orderable]': 'true',
        'columns[0][search][value]': '',
        'columns[0][search][regex]': 'false',
        'columns[1][data]': 'published',
        'columns[1][name]': '',
        'columns[1][searchable]': 'true',
        'columns[1][orderable]': 'true',
        'columns[1][search][value]': '',
        'columns[1][search][regex]': 'false',
        'columns[2][data]': 'description',
        'columns[2][name]': '',
        'columns[2][searchable]': 'true',
        'columns[2][orderable]': 'false',
        'columns[2][search][value]': '',
        'columns[2][search][regex]': 'false',
        'columns[3][data]': 'baseScore',
        'columns[3][name]': '',
        'columns[3][searchable]': 'true',
        'columns[3][orderable]': 'true',
        'columns[3][search][value]': '',
        'columns[3][search][regex]': 'false',
        'columns[4][data]': 'baseSeverity',
        'columns[4][name]': '',
        'columns[4][searchable]': 'true',
        'columns[4][orderable]': 'true',
        'columns[4][search][value]': '',
        'columns[4][search][regex]': 'false',
        'columns[5][data]': 'epss',
        'columns[5][name]': '',
        'columns[5][searchable]': 'true',
        'columns[5][orderable]': 'true',
        'columns[5][search][value]': '',
        'columns[5][search][regex]': 'false',
        'columns[6][data]': 'cisa',
        'columns[6][name]': '',
        'columns[6][searchable]': 'true',
        'columns[6][orderable]': 'true',
        'columns[6][search][value]': '',
        'columns[6][search][regex]': 'false',
        'order[0][column]': '0',
        'order[0][dir]': 'desc',
        'start': str(start),
        'length': str(length),
        'search[value]': search_value,
        'search[regex]': 'false'
    }
    
    try:
        print(f"Fetching CVE data: start={start}, length={length}")
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"Error fetching CVE data: {e}")
        return None

def clean_html_tags(text):
    """Remove HTML tags from text"""
    if not text:
        return text
    return re.sub(r'<[^>]+>', '', str(text))

def extract_date_from_published(published_text):
    """Extract date from published field (e.g., '2025-07-13<span...>' -> '2025-07-13')"""
    if not published_text:
        return None
    
    # Extract date part before any HTML tags
    match = re.match(r'(\d{4}-\d{2}-\d{2})', str(published_text))
    if match:
        return match.group(1)
    return None

def process_cve_data(raw_data):
    """Process and clean CVE data"""
    processed_cves = []
    
    for cve in raw_data.get('data', []):
        try:
            # Extract clean date
            published_date = extract_date_from_published(cve.get('published', ''))
            
            # Clean HTML from description
            description = clean_html_tags(cve.get('description', ''))
            
            # Process the CVE data
            processed_cve = {
                'id': cve.get('id', ''),
                'published': published_date,
                'published_raw': cve.get('published', ''),
                'lastModified': extract_date_from_published(cve.get('lastModified', '')),
                'description': description,
                'categories': cve.get('categories', ''),
                'owasp': cve.get('owasp', ''),
                'baseScore': cve.get('baseScore', ''),
                'baseSeverity': cve.get('baseSeverity', ''),
                'attackVector': cve.get('attackVector', ''),
                'attackComplexity': cve.get('attackComplexity', ''),
                'cvssVersion': cve.get('cvssVersion', ''),
                'epss': cve.get('epss', ''),
                'cisa': cve.get('cisa', '')
            }
            
            processed_cves.append(processed_cve)
            
        except Exception as e:
            print(f"Error processing CVE: {e}")
            continue
    
    return processed_cves

def scrape_today_cves():
    """Scrape all CVEs from today"""
    today = get_today_date()
    print(f"Scraping CVEs for today: {today}")

    # Get CSRF token (might be empty if not required)
    csrf_token = get_csrf_token()
    print(f"Using CSRF token: {'[EMPTY]' if not csrf_token else csrf_token[:20] + '...'}")
    
    all_cves = []
    start = 0
    length = 100
    draw = 1
    max_pages = 50  # Safety limit
    
    while draw <= max_pages:
        print(f"Fetching page {draw} (start={start})...")
        
        # Fetch data
        raw_data = fetch_cve_data(csrf_token, start=start, length=length, draw=draw)
        if not raw_data or 'data' not in raw_data:
            print("No data received or invalid response")
            break
        
        # Process CVEs
        page_cves = process_cve_data(raw_data)
        if not page_cves:
            print("No CVEs found in response")
            break
        
        # Filter only today's CVEs
        today_cves = [cve for cve in page_cves if cve['published'] == today]
        all_cves.extend(today_cves)
        
        print(f"Page {draw}: Found {len(today_cves)} CVEs from today (out of {len(page_cves)} total)")
        
        # Check if we found CVEs that are not from today
        non_today_cves = [cve for cve in page_cves if cve['published'] != today and cve['published'] is not None]
        if non_today_cves:
            print(f"Found {len(non_today_cves)} CVEs from other dates, stopping scrape")
            break
        
        # Check if we've reached the end
        if len(page_cves) < length:
            print("Reached end of data")
            break
        
        # Prepare for next page
        start += length
        draw += 1
        time.sleep(1)  # Be respectful
    
    print(f"Scraping completed. Total today's CVEs: {len(all_cves)}")
    return all_cves

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "message": "CVEFind.com Server - Today's CVEs Only",
        "endpoint": "/api/cves",
        "description": "GET /api/cves - Scrapes and returns all CVEs from today",
        "today_date": get_today_date(),
        "server_time": datetime.now().isoformat(),
        "source": "www.cvefind.com"
    })

@app.route('/api/test-csrf')
def test_csrf():
    """Test CSRF token extraction"""
    try:
        csrf_token = get_csrf_token()
        return jsonify({
            "success": csrf_token is not None,
            "csrf_token": csrf_token[:20] + "..." if csrf_token else None,
            "csrf_length": len(csrf_token) if csrf_token else 0,
            "message": "CSRF token extracted successfully" if csrf_token else "Failed to extract CSRF token"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Error during CSRF extraction"
        }), 500

@app.route('/api/cves')
def get_todays_cves():
    """Scrape and return all CVEs from today"""
    try:
        print("=== Starting CVEFind.com scrape ===")
        start_time = datetime.now()
        
        # Scrape today's CVEs
        todays_cves = scrape_today_cves()
        
        end_time = datetime.now()
        scrape_duration = (end_time - start_time).total_seconds()
        
        print(f"=== Scrape completed in {scrape_duration:.2f} seconds ===")
        
        # Prepare response
        response_data = {
            "success": True,
            "scraped_at": end_time.isoformat(),
            "scrape_duration_seconds": round(scrape_duration, 2),
            "today_date": get_today_date(),
            "total_cves": len(todays_cves),
            "source": "www.cvefind.com",
            "data": todays_cves
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error scraping CVEs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "scraped_at": datetime.now().isoformat(),
            "today_date": get_today_date(),
            "total_cves": 0,
            "source": "www.cvefind.com",
            "data": []
        }), 500

if __name__ == '__main__':
    print("=" * 50)
    print("CVEFind.com Server Starting...")
    print("=" * 50)
    print("Endpoint: http://localhost:5001/api/cves")
    print("Description: Scrapes and returns all CVEs from today")
    print(f"Today's date: {get_today_date()}")
    print("Source: www.cvefind.com")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
