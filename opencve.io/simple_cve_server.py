#!/usr/bin/env python3
"""
Simple CVE Server - Single endpoint that scrapes and returns today's CVEs
Enhanced with threading and connection loss prevention
"""

from flask import Flask, jsonify
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
from datetime import date, datetime
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global session with connection pooling and retry strategy
session = None
session_lock = threading.Lock()

def create_session():
    """Create a requests session with retry strategy and connection pooling"""
    s = requests.Session()

    # Retry strategy
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )

    # HTTP adapter with retry strategy
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )

    s.mount("http://", adapter)
    s.mount("https://", adapter)

    # Default headers
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })

    return s

def get_session():
    """Get or create the global session"""
    global session
    with session_lock:
        if session is None:
            session = create_session()
        return session

def get_today_date():
    """Get today's date in YYYY-MM-DD format"""
    return date.today().strftime('%Y-%m-%d')

def fetch_page(page_num, max_retries=3):
    """Fetch a specific page from OpenCVE with retry logic"""
    url = f"https://app.opencve.io/cve/?page={page_num}"

    for attempt in range(max_retries):
        try:
            session = get_session()
            logger.info(f"Fetching page {page_num} (attempt {attempt + 1}/{max_retries})")

            response = session.get(url, timeout=30)
            response.raise_for_status()

            logger.info(f"Successfully fetched page {page_num}")
            return BeautifulSoup(response.content, 'html.parser')

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on page {page_num}, attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch page {page_num} after {max_retries} attempts")

        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout error on page {page_num}, attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch page {page_num} after {max_retries} attempts due to timeout")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error on page {page_num}: {e}")
            if e.response.status_code == 429:  # Rate limited
                if attempt < max_retries - 1:
                    wait_time = 5 * (2 ** attempt)  # Longer wait for rate limiting
                    logger.info(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Rate limited on page {page_num} after {max_retries} attempts")
            else:
                break  # Don't retry for other HTTP errors

        except Exception as e:
            logger.error(f"Unexpected error fetching page {page_num}: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch page {page_num} after {max_retries} attempts")

    return None

def parse_cvss(cvss_text):
    """Parse CVSS score and severity"""
    if not cvss_text or 'N/A' in cvss_text:
        return None, None
    
    match = re.search(r'(\d+\.?\d*)\s+(\w+)', cvss_text.strip())
    if match:
        return float(match.group(1)), match.group(2)
    return None, cvss_text.strip()

def extract_cves_from_page(soup):
    """Extract CVE data from a page"""
    cves = []
    
    table = soup.find('table', {'id': 'cves'})
    if not table:
        return cves
    
    headers = table.find_all('tr', class_='cve-header')
    summaries = table.find_all('tr', class_='cve-summary')
    
    for i, header in enumerate(headers):
        try:
            cells = header.find_all('td')
            
            # Extract CVE ID and URL
            cve_link = cells[0].find('a')
            cve_id = cve_link.text.strip()
            cve_url = f"https://app.opencve.io{cve_link.get('href')}"
            
            # Extract vendors
            vendor_links = cells[1].find_all('a')
            vendors = [link.text.strip() for link in vendor_links]
            
            # Extract products
            product_links = cells[2].find_all('a')
            products = [link.text.strip() for link in product_links]
            
            # Extract date
            updated_date = cells[3].text.strip()
            
            # Extract CVSS
            cvss_span = cells[4].find('span')
            cvss_text = cvss_span.text.strip() if cvss_span else 'N/A'
            cvss_score, cvss_severity = parse_cvss(cvss_text)
            
            # Extract summary
            summary = ""
            if i < len(summaries):
                summary_cell = summaries[i].find('td')
                summary = summary_cell.text.strip() if summary_cell else ""
            
            cve_data = {
                'cve_id': cve_id,
                'cve_url': cve_url,
                'vendors': vendors,
                'products': products,
                'updated_date': updated_date,
                'cvss_score': cvss_score,
                'cvss_severity': cvss_severity,
                'summary': summary
            }
            
            cves.append(cve_data)
            
        except Exception as e:
            print(f"Error parsing CVE {i}: {e}")
            continue
    
    return cves

def fetch_page_worker(page_num):
    """Worker function for threaded page fetching"""
    soup = fetch_page(page_num)
    if soup:
        cves = extract_cves_from_page(soup)
        return page_num, cves
    return page_num, []

def scrape_today_cves_threaded(max_workers=3):
    """Scrape all CVEs from today using threading"""
    today = get_today_date()
    logger.info(f"Scraping CVEs for today: {today} (using {max_workers} threads)")

    all_cves = []
    max_pages = 100  # Safety limit
    consecutive_empty_pages = 0
    max_consecutive_empty = 3

    # First, check page 1 to see if there are any CVEs from today
    logger.info("Checking page 1 first to determine if today's CVEs exist...")
    page_1_result = fetch_page_worker(1)
    if not page_1_result[1]:  # No CVEs found on page 1
        logger.info("No CVEs found on page 1, stopping scrape")
        return all_cves

    # Check if page 1 has today's CVEs
    page_1_cves = page_1_result[1]
    today_cves_page_1 = [cve for cve in page_1_cves if cve['updated_date'] == today]

    if not today_cves_page_1:
        logger.info(f"Page 1 has no CVEs from today ({today}), stopping scrape")
        return all_cves

    # Page 1 has today's CVEs, add them and continue
    all_cves.extend(today_cves_page_1)
    logger.info(f"Page 1: Found {len(today_cves_page_1)} CVEs from today (out of {len(page_1_cves)} total)")

    # Now continue with threaded approach starting from page 2
    initial_pages = min(3, max_pages - 1)  # Start from page 2
    pages_to_check = list(range(2, initial_pages + 2))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit initial batch of pages
        future_to_page = {executor.submit(fetch_page_worker, page_num): page_num
                         for page_num in pages_to_check}

        processed_pages = set()
        should_continue = True

        while future_to_page and should_continue:
            # Process completed futures
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                processed_pages.add(page_num)

                try:
                    page_num, page_cves = future.result()

                    if not page_cves:
                        consecutive_empty_pages += 1
                        logger.info(f"No CVEs found on page {page_num}")

                        if consecutive_empty_pages >= max_consecutive_empty:
                            logger.info(f"Found {consecutive_empty_pages} consecutive empty pages, stopping")
                            should_continue = False
                            break
                    else:
                        consecutive_empty_pages = 0

                        # Filter only today's CVEs
                        today_cves = [cve for cve in page_cves if cve['updated_date'] == today]
                        all_cves.extend(today_cves)

                        logger.info(f"Page {page_num}: Found {len(today_cves)} CVEs from today (out of {len(page_cves)} total)")

                        # If we found CVEs that are not from today, we might be reaching older content
                        non_today_cves = [cve for cve in page_cves if cve['updated_date'] != today]
                        if non_today_cves and len(non_today_cves) == len(page_cves):
                            logger.info(f"Page {page_num} contains only non-today CVEs, might be reaching end")
                            consecutive_empty_pages += 1

                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {e}")
                    consecutive_empty_pages += 1

                # Remove completed future
                del future_to_page[future]

            # Submit next batch of pages if we should continue
            if should_continue:
                next_page = max(processed_pages) + 1 if processed_pages else 1
                next_batch_size = min(max_workers, max_pages - next_page + 1)

                if next_batch_size > 0 and next_page <= max_pages:
                    next_pages = list(range(next_page, next_page + next_batch_size))
                    for page_num in next_pages:
                        if page_num not in processed_pages:
                            future = executor.submit(fetch_page_worker, page_num)
                            future_to_page[future] = page_num
                else:
                    should_continue = False

    logger.info(f"Threaded scraping completed. Total today's CVEs: {len(all_cves)}")
    return all_cves

def scrape_today_cves():
    """Scrape all CVEs from today (fallback to sequential if threading fails)"""
    try:
        return scrape_today_cves_threaded()
    except Exception as e:
        logger.warning(f"Threaded scraping failed: {e}. Falling back to sequential scraping.")
        return scrape_today_cves_sequential()

def scrape_today_cves_sequential():
    """Sequential scraping as fallback"""
    today = get_today_date()
    logger.info(f"Scraping CVEs for today: {today} (sequential mode)")

    all_cves = []
    page = 1
    max_pages = 100  # Safety limit

    while page <= max_pages:
        logger.info(f"Scraping page {page}...")

        # Fetch page
        soup = fetch_page(page)
        if not soup:
            logger.warning(f"Failed to fetch page {page}")
            break

        # Extract CVEs
        page_cves = extract_cves_from_page(soup)
        if not page_cves:
            logger.info(f"No CVEs found on page {page}")
            break

        # Filter only today's CVEs
        today_cves = [cve for cve in page_cves if cve['updated_date'] == today]

        # Early termination: if page 1 has no today's CVEs, stop immediately
        if page == 1 and not today_cves:
            logger.info(f"Page 1 has no CVEs from today ({today}), stopping scrape")
            break

        all_cves.extend(today_cves)

        logger.info(f"Page {page}: Found {len(today_cves)} CVEs from today (out of {len(page_cves)} total)")

        # If we found CVEs that are not from today, we can stop
        non_today_cves = [cve for cve in page_cves if cve['updated_date'] != today]
        if non_today_cves:
            logger.info(f"Found {len(non_today_cves)} CVEs from other dates, stopping scrape")
            break

        # Be respectful - wait between requests
        time.sleep(1)
        page += 1

    logger.info(f"Sequential scraping completed. Total today's CVEs: {len(all_cves)}")
    return all_cves

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "message": "Simple CVE Server - Today's CVEs Only",
        "version": "2.0 - Enhanced with threading and connection resilience",
        "endpoints": {
            "/api/cves": "GET - Scrapes and returns all CVEs from today",
            "/health": "GET - Health check endpoint"
        },
        "features": [
            "Threaded page fetching",
            "Automatic retry with exponential backoff",
            "Connection pooling",
            "Graceful fallback to sequential scraping"
        ],
        "today_date": get_today_date(),
        "server_time": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    session_obj = None
    connectivity_status = "unknown"

    try:
        # Test session connectivity
        session_obj = get_session()
        test_response = session_obj.get("https://httpbin.org/status/200", timeout=5)
        connectivity_status = "ok" if test_response.status_code == 200 else "degraded"
    except Exception as e:
        connectivity_status = "error"
        logger.warning(f"Health check connectivity test failed: {e}")

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connectivity": connectivity_status,
        "session_initialized": session_obj is not None,
        "today_date": get_today_date()
    })

@app.route('/api/cves')
def get_todays_cves():
    """Scrape and return all CVEs from today"""
    try:
        logger.info("=== Starting CVE scrape ===")
        start_time = datetime.now()

        # Scrape today's CVEs
        todays_cves = scrape_today_cves()

        end_time = datetime.now()
        scrape_duration = (end_time - start_time).total_seconds()

        logger.info(f"=== Scrape completed in {scrape_duration:.2f} seconds ===")

        # Prepare response
        response_data = {
            "success": True,
            "scraped_at": end_time.isoformat(),
            "scrape_duration_seconds": round(scrape_duration, 2),
            "today_date": get_today_date(),
            "total_cves": len(todays_cves),
            "cves": todays_cves,
            "scraping_method": "threaded" if len(todays_cves) > 0 else "sequential_fallback"
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error scraping CVEs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "scraped_at": datetime.now().isoformat(),
            "today_date": get_today_date(),
            "total_cves": 0,
            "cves": []
        }), 500

if __name__ == '__main__':
    print("Starting server...")  # Debug print
    logger.info("=" * 60)
    logger.info("Simple CVE Server Starting...")
    logger.info("Enhanced with threading and connection loss prevention")
    logger.info("Enhanced with early termination optimization")
    logger.info("=" * 60)
    logger.info("Endpoint: http://localhost:5000/api/cves")
    logger.info("Description: Scrapes and returns all CVEs from today")
    logger.info(f"Today's date: {get_today_date()}")
    logger.info("Features:")
    logger.info("  - Threaded page fetching for improved performance")
    logger.info("  - Automatic retry with exponential backoff")
    logger.info("  - Connection pooling and session management")
    logger.info("  - Graceful fallback to sequential scraping")
    logger.info("  - Early termination if page 1 has no today's CVEs")
    logger.info("=" * 60)

    # Initialize session on startup
    try:
        session = get_session()
        logger.info("Session initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize session: {e}")

    print("About to start Flask app...")  # Debug print
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
