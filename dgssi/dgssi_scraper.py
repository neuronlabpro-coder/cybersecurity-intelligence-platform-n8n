#!/usr/bin/env python3
"""
DGSSI Security Bulletins Scraper
Scrapes security bulletins from https://www.dgssi.gov.ma/fr/bulletins-securite
and returns JSON data for today's bulletins.
"""

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from datetime import datetime
import re
import logging
from typing import List, Dict, Optional
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Ensure proper unicode handling in JSON responses

class DGSSIScraper:
    def __init__(self):
        self.base_url = "https://www.dgssi.gov.ma"
        self.bulletins_url = "https://www.dgssi.gov.ma/fr/bulletins-securite"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # French month mapping for date conversion
        self.french_months = {
            'janvier': '01', 'février': '02', 'mars': '03', 'avril': '04',
            'mai': '05', 'juin': '06', 'juillet': '07', 'août': '08',
            'septembre': '09', 'octobre': '10', 'novembre': '11', 'décembre': '12'
        }
    
    def get_today_date_french(self) -> str:
        """Get today's date in French format as used by DGSSI"""
        today = datetime.now()
        months_fr = {
            1: "janvier", 2: "février", 3: "mars", 4: "avril",
            5: "mai", 6: "juin", 7: "juillet", 8: "août",
            9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
        }
        return f"{today.day} {months_fr[today.month]} {today.year}"

    def convert_french_date_to_formats(self, french_date: str) -> dict:
        """Convert French date format to both RFC 2822 and ISO formats"""
        try:
            # Handle unicode characters (like \u00fbt for û)
            french_date = french_date.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
        except:
            pass  # If conversion fails, use original string

        # Pattern to match French date format: "15 août 2025"
        pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(pattern, french_date)

        if match:
            day, month_name, year = match.groups()

            # Convert month name to number
            month_name_lower = month_name.lower()
            month_num = self.french_months.get(month_name_lower)

            if month_num:
                # Create datetime object
                from datetime import datetime
                try:
                    date_obj = datetime(int(year), int(month_num), int(day), 10, 0, 5)
                    # Return both formats
                    return {
                        'rfc2822': date_obj.strftime("%a, %d %b %Y %H:%M:%S +0000"),
                        'iso': date_obj.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    }
                except ValueError:
                    pass

        # If conversion fails, return original date in both formats
        return {
            'rfc2822': french_date,
            'iso': french_date
        }

    def clean_unicode_text(self, text: str) -> str:
        """Clean unicode escape sequences from text and handle French characters"""
        if not text:
            return text

        try:
            cleaned = text

            # Multiple passes to handle different encoding issues

            # Pass 1: Handle literal unicode escape sequences in strings
            import re
            unicode_pattern = r'\\u([0-9a-fA-F]{4})'

            def replace_unicode_escape(match):
                code = match.group(1)
                try:
                    return chr(int(code, 16))
                except:
                    return match.group(0)

            cleaned = re.sub(unicode_pattern, replace_unicode_escape, cleaned)

            # Pass 2: Handle raw unicode characters
            replacements = {
                # Common French characters
                '\u00e9': 'é', '\u00e8': 'è', '\u00ea': 'ê', '\u00eb': 'ë',
                '\u00e0': 'à', '\u00e2': 'â', '\u00e4': 'ä', '\u00e7': 'ç',
                '\u00f9': 'ù', '\u00fb': 'û', '\u00fc': 'ü', '\u00f4': 'ô',
                '\u00f6': 'ö', '\u00ee': 'î', '\u00ef': 'ï',
                '\u00c9': 'É', '\u00c8': 'È', '\u00ca': 'Ê', '\u00c0': 'À', '\u00c7': 'Ç',

                # Special punctuation
                '\u2019': "'",  # Right single quotation mark
                '\u2018': "'",  # Left single quotation mark
                '\u201c': '"',  # Left double quotation mark
                '\u201d': '"',  # Right double quotation mark
                '\u2013': '-',  # En dash
                '\u2014': '-',  # Em dash
                '\u00a0': ' ',  # Non-breaking space
                '\u00ab': '"',  # Left-pointing double angle quotation mark
                '\u00bb': '"',  # Right-pointing double angle quotation mark
            }

            for unicode_char, replacement in replacements.items():
                cleaned = cleaned.replace(unicode_char, replacement)

            # Pass 3: Handle any remaining problematic characters
            # Replace any remaining unicode control characters with spaces
            cleaned = re.sub(r'[\u0000-\u001f\u007f-\u009f]', ' ', cleaned)

            # Clean up multiple spaces
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            return cleaned

        except Exception as e:
            logger.warning(f"Unicode cleaning failed for text: {text[:50]}... Error: {e}")
            return text  # If conversion fails, return original
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_bulletin_links_from_main_page(self, filter_today_only: bool = False) -> List[Dict[str, str]]:
        """Extract bulletin links and basic info from the main bulletins page"""
        soup = self.fetch_page(self.bulletins_url)
        if not soup:
            return []

        bulletins = []
        today_date = self.get_today_date_french()

        # Find all bulletin cards
        bulletin_cards = soup.find_all('div', class_='single-blog-posts')

        for card in bulletin_cards:
            try:
                # Extract title and link
                title_link = card.find('h3').find('a')
                if not title_link:
                    continue

                title = self.clean_unicode_text(title_link.get_text(strip=True))
                link = title_link.get('href')

                # Make sure link is absolute
                if link and not link.startswith('http'):
                    link = self.base_url + link

                # Extract date
                date_element = card.find('li', class_='float')
                if not date_element:
                    continue

                date_text = date_element.get_text(strip=True)
                # Remove the calendar icon text
                date_text = re.sub(r'^\s*\s*', '', date_text).strip()

                # Extract description
                description_p = card.find('p')
                description = self.clean_unicode_text(description_p.get_text(strip=True)) if description_p else ""

                # Convert date to both formats
                date_formats = self.convert_french_date_to_formats(date_text)

                # Add bulletin (filter by today's date if requested)
                if not filter_today_only or today_date in date_text:
                    bulletins.append({
                        'title': title,
                        'link': link,
                        'date': date_formats['rfc2822'],
                        'isoDate': date_formats['iso'],
                        'date_original': date_text,
                        'description': description
                    })
                    if filter_today_only:
                        logger.info(f"Found today's bulletin: {title}")
                    else:
                        logger.info(f"Found bulletin: {title} - {date_text}")

            except Exception as e:
                logger.error(f"Error processing bulletin card: {e}")
                continue

        return bulletins
    
    def extract_bulletin_details(self, bulletin_url: str) -> Dict:
        """Extract detailed information from a bulletin page"""
        soup = self.fetch_page(bulletin_url)
        if not soup:
            return {}
        
        details = {}
        
        try:          
            # Extract table information
            table = soup.find('table', class_='table-bordered')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value_cell = cells[1]
                        
                        # Extract text, handling nested divs
                        field_item = value_cell.find('div', class_='field__item')
                        if field_item:
                            value = field_item.get_text(strip=True)
                        else:
                            value = value_cell.get_text(strip=True)

                        # Clean unicode from value
                        value = self.clean_unicode_text(value)
                        
                        # Clean unicode from key first
                        clean_key = self.clean_unicode_text(key)

                        # Map French keys to consistent field names
                        key_mapping = {
                            'Titre': 'title',
                            'Date de publication': 'date',
                            'Niveau de Risque': 'criticite'
                        }

                        # Skip excluded fields
                        excluded_fields = ['Numéro de Référence', 'Référence', 'Niveau d\'Impact']
                        if clean_key in excluded_fields:
                            continue

                        # Get mapped key or create clean version
                        mapped_key = key_mapping.get(clean_key)
                        if not mapped_key:
                            # Create clean field name from French text
                            mapped_key = (clean_key.lower()
                                        .replace(' de ', '_')  # Handle "de" connector
                                        .replace(' ', '_')
                                        .replace('é', 'e')
                                        .replace('è', 'e')
                                        .replace('à', 'a')
                                        .replace('ç', 'c')
                                        .replace('ù', 'u')
                                        .replace('ô', 'o')
                                        .replace('î', 'i')
                                        .replace('â', 'a')
                                        .replace('ê', 'e')
                                        .replace('û', 'u'))

                        # Convert date to both RFC 2822 and ISO formats
                        if mapped_key == 'date':
                            date_formats = self.convert_french_date_to_formats(value)
                            details['date'] = date_formats['rfc2822']
                            details['isoDate'] = date_formats['iso']
                            continue  # Skip the normal assignment since we handled both fields

                        details[mapped_key] = value
            
            # Extract sections with h4 headers
            sections = soup.find_all('h4')
            for section in sections:
                section_title = section.get_text(strip=True).rstrip(':')
                
                # Find the content after the h4
                content_div = section.find_next_sibling('div')
                if content_div:
                    field_item = content_div.find('div', class_='field__item')
                    if field_item:
                        # Handle lists
                        ul_elements = field_item.find_all('ul')
                        if ul_elements:
                            content = []
                            for ul in ul_elements:
                                items = [self.clean_unicode_text(li.get_text(strip=True)) for li in ul.find_all('li')]
                                content.extend(items)
                        else:
                            content = self.clean_unicode_text(field_item.get_text(strip=True))
                    else:
                        content = self.clean_unicode_text(content_div.get_text(strip=True))
                    
                    # Clean unicode from section title first
                    clean_section_title = self.clean_unicode_text(section_title)

                    # Skip excluded sections
                    excluded_sections = ['Référence']
                    if clean_section_title in excluded_sections:
                        continue

                    # Map section titles to field names
                    section_mapping = {
                        'Systèmes affectés': 'systemes_affectes',
                        'Identificateurs externes': 'identificateurs_externes',
                        'Bilan de la vulnérabilité': 'content',
                        'Solution': 'actions_recommandees',
                        'Risque': 'risque'
                    }

                    # Get mapped section or create clean version
                    mapped_section = section_mapping.get(clean_section_title)
                    if not mapped_section:
                        # Create clean field name from French text
                        mapped_section = (clean_section_title.lower()
                                        .replace(' de ', '_')  # Handle "de" connector
                                        .replace(' ', '_')
                                        .replace('é', 'e')
                                        .replace('è', 'e')
                                        .replace('à', 'a')
                                        .replace('ç', 'c')
                                        .replace('ù', 'u')
                                        .replace('ô', 'o')
                                        .replace('î', 'i')
                                        .replace('â', 'a')
                                        .replace('ê', 'e')
                                        .replace('û', 'u'))

                    # Special handling for identificateurs_externes to convert to array
                    if mapped_section == 'identificateurs_externes' and isinstance(content, str):
                        # Split CVE identifiers and clean them up
                        cve_pattern = r'CVE-\d{4}-\d+'
                        cve_matches = re.findall(cve_pattern, content)
                        details[mapped_section] = cve_matches if cve_matches else [content.strip()] if content.strip() else []
                    else:
                        details[mapped_section] = content
            
        except Exception as e:
            logger.error(f"Error extracting details from {bulletin_url}: {e}")
        
        return details
    
    def scrape_today_bulletins(self) -> List[Dict]:
        """Scrape all bulletins from today and return detailed information"""
        logger.info("Starting to scrape today's bulletins...")

        # Get today's bulletin links
        bulletin_links = self.extract_bulletin_links_from_main_page(filter_today_only=True)

        if not bulletin_links:
            logger.info("No bulletins found for today")
            return []

        logger.info(f"Found {len(bulletin_links)} bulletins for today")

        # Extract detailed information for each bulletin
        detailed_bulletins = []
        for bulletin in bulletin_links:
            logger.info(f"Extracting details for: {bulletin['title']}")

            details = self.extract_bulletin_details(bulletin['link'])

            # Combine basic info with detailed info
            full_bulletin = {
                'url': bulletin['link'],
                **details
            }

            detailed_bulletins.append(full_bulletin)

            # Add a small delay to be respectful to the server
            time.sleep(1)

        return detailed_bulletins

    def process_single_bulletin(self, bulletin: Dict[str, str]) -> Dict:
        """Process a single bulletin and return detailed information"""
        try:
            logger.info(f"Processing: {bulletin['title']}")

            details = self.extract_bulletin_details(bulletin['link'])

            # Combine basic info with detailed info
            full_bulletin = {
                'link': bulletin['link'],
                **details
            }

            return full_bulletin
        except Exception as e:
            logger.error(f"Error processing bulletin {bulletin.get('title', 'Unknown')}: {e}")
            return {
                'link': bulletin['link'],
                'error': str(e),
                'title': bulletin.get('title', 'Unknown')
            }

    def scrape_all_bulletins_threaded(self, max_workers: int = 5) -> List[Dict]:
        """Scrape all bulletins using threading for faster processing"""
        logger.info("Starting to scrape all bulletins with threading...")

        # Get all bulletin links
        bulletin_links = self.extract_bulletin_links_from_main_page(filter_today_only=False)

        if not bulletin_links:
            logger.info("No bulletins found")
            return []

        logger.info(f"Found {len(bulletin_links)} bulletins to process with {max_workers} threads")

        # Process bulletins concurrently
        detailed_bulletins = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_bulletin = {
                executor.submit(self.process_single_bulletin, bulletin): bulletin
                for bulletin in bulletin_links
            }

            # Collect results as they complete
            for future in as_completed(future_to_bulletin):
                bulletin = future_to_bulletin[future]
                try:
                    result = future.result()
                    detailed_bulletins.append(result)
                    logger.info(f"Completed: {bulletin['title']} ({len(detailed_bulletins)}/{len(bulletin_links)})")
                except Exception as e:
                    logger.error(f"Error processing {bulletin['title']}: {e}")
                    # Add error entry
                    detailed_bulletins.append({
                        'link': bulletin['link'],
                        'error': str(e),
                        'title': bulletin.get('title', 'Unknown')
                    })

        logger.info(f"Completed processing {len(detailed_bulletins)} bulletins")
        return detailed_bulletins

# Flask routes
@app.route('/')
def index():
    """Main endpoint that returns all bulletins as JSON using threading"""
    try:
        scraper = DGSSIScraper()

        bulletins = scraper.scrape_all_bulletins_threaded(max_workers=5)

        # Create response with proper unicode handling
        from flask import Response
        import json

        json_str = json.dumps(bulletins, ensure_ascii=False, indent=2)
        return Response(json_str, mimetype='application/json; charset=utf-8')

    except Exception as e:
        logger.error(f"Error in main endpoint: {e}")
        error_response = {
            'error': 'Une erreur est survenue lors du scraping',
            'details': str(e)
        }
        json_str = json.dumps(error_response, ensure_ascii=False, indent=2)
        return Response(json_str, mimetype='application/json; charset=utf-8', status=500)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
