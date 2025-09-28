import requests
from bs4 import BeautifulSoup
import time
import json
import os
from urllib.parse import urljoin
import random
from typing import Dict, List, Optional
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RigVedaScraper:
    def __init__(self, base_url: str = "https://sacred-texts.com/hin/rigveda/index.htm"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = {
            'books': {},
            'total_hymns': 0,
            'scraping_metadata': {
                'start_time': None,
                'end_time': None,
                'total_requests': 0,
                'errors': []
            }
        }
        
    def AddDelay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay between requests to avoid rate limiting"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def MakeRequest(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Make HTTP request with retry logic and error handling"""
        for attempt in range(max_retries):
            try:
                self.AddDelay()
                response = self.session.get(url, timeout=30)
                self.scraped_data['scraping_metadata']['total_requests'] += 1
                
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt * 5  # Exponential backoff
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP {response.status_code} for URL: {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    
        error_msg = f"Failed to fetch {url} after {max_retries} attempts"
        logger.error(error_msg)
        self.scraped_data['scraping_metadata']['errors'].append(error_msg)
        return None
        
    def GetBookLinks(self) -> List[Dict[str, str]]:
        """Extract all Rig-Veda book links from the main page"""
        logger.info("Fetching book links from main page...")
        soup = self.MakeRequest(self.base_url)
        if not soup:
            return []
            
        book_links = []
        # Look for links that contain 'rigveda' and book numbers
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Check if this looks like a book link
            if href and ('rvi' in href.lower()):
                full_url = urljoin(self.base_url, href)
                book_links.append({
                    'title': text,
                    'url': full_url,
                    'book_number': self.ExtractBookNumber(text, href)
                })
                
        # Sort by book number
        book_links.sort(key=lambda x: x['book_number'])
        logger.info(f"Found {len(book_links)} book links")
        return book_links
        
    def ExtractBookNumber(self, text: str, href: str) -> int:
        """Extract book number from text or URL"""
        import re
        
        # Try to extract from text first
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
            
        # Try to extract from URL
        numbers = re.findall(r'rv(\d+)', href.lower())
        if numbers:
            return int(numbers[0])
            
        # Default fallback
        return 0
        
    def GetHymnLinks(self, book_url: str) -> List[Dict[str, str]]:
        """Extract all hymn links from a book page"""
        logger.info(f"Fetching hymn links from: {book_url}")
        soup = self.MakeRequest(book_url)
        if not soup:
            return []
            
        hymn_links = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Check if this looks like a hymn link
            if href and text and ('hymn' in text.lower()):
                full_url = urljoin(book_url, href)
                hymn_number = self.ExtractHymnNumber(href)
                
                hymn_links.append({
                    'title': text,
                    'url': full_url,
                    'hymn_number': hymn_number
                })
                
        # Sort by hymn number
        hymn_links.sort(key=lambda x: x['hymn_number'])
        logger.info(f"Found {len(hymn_links)} hymn links")
        return hymn_links
        
    def ExtractHymnNumber(self, href: str) -> int:
        """Extract hymn number from text or URL"""
        numbers = re.findall(r'rv(\d+)', href.lower())
        if numbers:
            return int(numbers[0])
        return 0
        
    def ScrapeHymnText(self, hymn_url: str) -> Dict[str, str]:
        """Extract hymn text and metadata from a hymn page"""
        logger.info(f"Scraping hymn text from: {hymn_url}")
        soup = self.MakeRequest(hymn_url)
        if not soup:
            return {'text': '', 'title': '', 'error': 'Failed to fetch page'}
            
        # Extract title
        title = ''
        title_element = soup.find('h3')
        if title_element:
            title = title_element.get_text(strip=True)
            
        # Extract main text content - only paragraphs that are siblings of h3 elements
        text_content = ''
        
        # Find all h3 elements and get their following sibling paragraphs
        h3_elements = soup.find_all('h3')
        text_parts = []
        
        for h3 in h3_elements:
            # Get the next sibling paragraph
            next_p = h3.find_next_sibling('p')
            if next_p:
                text = next_p.get_text(strip=True)
                if text:  # Filter out short/empty content
                    text_parts.append(text)
        text_content=""
        if text_parts:
            for text_part in text_parts:
                split_parts = re.split(r'(\d)', text_part)
                filtered_parts = [f for f in split_parts if f.strip() and not f.isdigit()]
                for f in filtered_parts:
                    text_content += f
        return {
            'text': text_content,
            'title': title,
            'url': hymn_url
        }
        
    def ScrapeBook(self, book_info: Dict[str, str]) -> Dict:
        """Scrape all hymns from a single book"""
        book_number = book_info['book_number']
        book_url = book_info['url']
        
        logger.info(f"Starting to scrape Book {book_number}: {book_info['title']}")
        
        book_data = {
            'book_number': book_number,
            'title': book_info['title'],
            'url': book_url,
            'hymns': {},
            'total_hymns': 0
        }
        
        # Get all hymn links for this book
        hymn_links = self.GetHymnLinks(book_url)
        
        for hymn_info in hymn_links:
            hymn_number = hymn_info['hymn_number']
            hymn_url = hymn_info['url']
            
            logger.info(f"Scraping Book {book_number}, Hymn {hymn_number}")
            
            # Scrape the hymn text
            hymn_data = self.ScrapeHymnText(hymn_url)
            hymn_data['hymn_number'] = hymn_number
            
            book_data['hymns'][hymn_number] = hymn_data
            book_data['total_hymns'] += 1
            self.scraped_data['total_hymns'] += 1
            
            # Add extra delay for hymn scraping to be respectful
            self.AddDelay(2.0, 4.0)
            
        logger.info(f"Completed Book {book_number} with {book_data['total_hymns']} hymns")
        return book_data
        
    def ScrapeAllBooks(self) -> Dict:
        """Scrape all Rig-Veda books and hymns"""
        logger.info("Starting Rig-Veda scraping process...")
        self.scraped_data['scraping_metadata']['start_time'] = time.time()
        
        # Get all book links
        book_links = self.GetBookLinks()
        
        if not book_links:
            logger.error("No book links found!")
            return self.scraped_data
            
        logger.info(f"Found {len(book_links)} books to scrape")
        
        # Scrape each book
        for book_info in book_links:
            try:
                book_data = self.ScrapeBook(book_info)
                self.scraped_data['books'][book_data['book_number']] = book_data
                
                # Save progress after each book
                self.SaveProgress()
                self.SaveToTextFiles()
                
            except Exception as e:
                error_msg = f"Error scraping book {book_info['book_number']}: {str(e)}"
                logger.error(error_msg)
                self.scraped_data['scraping_metadata']['errors'].append(error_msg)
                
        self.scraped_data['scraping_metadata']['end_time'] = time.time()
        
        logger.info(f"Scraping completed! Total hymns scraped: {self.scraped_data['total_hymns']}")
        return self.scraped_data
        
    def SaveProgress(self):
        """Save current progress to JSON file"""
        output_file = 'rigveda_data.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Progress saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save progress: {str(e)}")
            
    def SaveToTextFiles(self, output_dir: str = 'rigveda_texts'):
        """Save scraped data to individual text files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for book_num, book_data in self.scraped_data['books'].items():
            book_dir = os.path.join(output_dir, f"book_{book_num}")
            os.makedirs(book_dir, exist_ok=True)
            
            for hymn_num, hymn_data in book_data['hymns'].items():
                filename = f"hymn_{hymn_num}.txt"
                filepath = os.path.join(book_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {hymn_data.get('title', 'Unknown')}\n")
                    f.write(f"URL: {hymn_data.get('url', '')}\n")
                    f.write(f"Book: {book_num}, Hymn: {hymn_num}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(hymn_data.get('text', ''))
                    
        logger.info(f"Text files saved to {output_dir}")

def main():
    """Main function to run the scraper"""
    scraper = RigVedaScraper()
    
    try:
        
        # Start scraping
        result = scraper.ScrapeAllBooks()
        print(result)
        
        # Print summary
        print("\nScraping Summary:")
        print(f"Total books scraped: {len(result['books'])}")
        print(f"Total hymns scraped: {result['total_hymns']}")
        print(f"Total requests made: {result['scraping_metadata']['total_requests']}")
        print(f"Errors encountered: {len(result['scraping_metadata']['errors'])}")
        
        if result['scraping_metadata']['errors']:
            print("\nErrors:")
            for error in result['scraping_metadata']['errors']:
                print(f"  - {error}")
                
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        scraper.SaveProgress()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        scraper.SaveProgress()

if __name__ == "__main__":
    main()
