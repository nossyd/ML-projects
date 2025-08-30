#!/usr/bin/env python3
"""
United Airlines Flight Scraper
Scrapes flight information for SFO to LAX round trips from United.com
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

class UnitedFlightScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome WebDriver"""
        self.setup_driver(headless)
        self.base_url = "https://www.united.com"
        
    def setup_driver(self, headless=True):
        """Set up Chrome WebDriver with stealth options to avoid detection"""
        chrome_options = Options()
        
        # Basic stealth options
        if headless:
            chrome_options.add_argument("--headless=new")  # Use new headless mode
        
        # Anti-detection arguments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_argument("--disable-javascript")  # May help avoid detection
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # Randomize window size to look more human
        import random
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        # User agent rotation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional prefs to avoid detection
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,  # Block images for speed
        })
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Make sure ChromeDriver is installed and in PATH")
            raise
        
        # Execute stealth scripts to hide automation
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        window.chrome = {
            runtime: {},
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({state: 'granted'}),
            }),
        });
        """
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_js
        })
        
        # Set additional headers to look more like a real browser
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(user_agents),
            "acceptLanguage": "en-US,en;q=0.9",
            "platform": "Win32"
        })
        
    def search_flights(self, departure_date, return_date, adults=1):
        """
        Search for round-trip flights from SFO to LAX using direct URL
        
        Args:
            departure_date (str): Departure date in YYYY-MM-DD format
            return_date (str): Return date in YYYY-MM-DD format
            adults (int): Number of adult passengers
            
        Returns:
            dict: Flight information including prices and schedules
        """
        try:
            # Construct the direct search URL
            search_url = self._build_search_url("SFO", "LAX", departure_date, return_date, adults)
            print(f"Navigating directly to search URL: {search_url}")
            
            # Add some random delay to look more human
            import random
            time.sleep(random.uniform(2, 5))
            
            # Navigate directly to search results
            self.driver.get(search_url)
            
            # Wait for page to load with human-like behavior
            time.sleep(random.uniform(8, 15))
            
            # Simulate human behavior - scroll a bit
            self.driver.execute_script("window.scrollTo(0, 300);")
            time.sleep(random.uniform(1, 3))
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
            
            # Check if we got blocked
            page_source = self.driver.page_source.lower()
            if any(block_text in page_source for block_text in [
                "sorry", "unable to complete", "blocked", "access denied", 
                "please try again", "security", "robot", "captcha"
            ]):
                print("⚠️  Detected potential blocking. Page content:")
                print(self.driver.page_source[:1000])
                print("\n💡 Trying with different approach...")
                
                # Try refreshing with different user agent
                self._rotate_user_agent()
                time.sleep(random.uniform(5, 10))
                self.driver.refresh()
                time.sleep(random.uniform(8, 12))
            
            # Handle any popups that might appear
            self._handle_popups()
            
            # Wait for search results to load
            self._wait_for_search_results()
            
            # Extract flight data
            flight_data = self._extract_flight_data()
            
            return flight_data
            
        except Exception as e:
            print(f"Error during flight search: {str(e)}")
            
            # Fallback: Try with requests session (no browser automation)
            print("\n🔄 Trying fallback method with requests session...")
            return self._fallback_requests_method(departure_date, return_date, adults)
    
    def _fallback_requests_method(self, departure_date, return_date, adults):
        """Fallback method using requests session instead of Selenium"""
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Create session with retries
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Set headers to look like a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            session.headers.update(headers)
            
            # Build the search URL
            search_url = self._build_search_url("SFO", "LAX", departure_date, return_date, adults)
            print(f"Requesting URL with requests session: {search_url}")
            
            # Make the request
            response = session.get(search_url, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Save the HTML content for parsing
                with open('debug_requests_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("Saved response to debug_requests_response.html")
                
                # Try to parse flight data from the HTML
                return self._parse_html_content(response.text)
            else:
                print(f"Failed to get data: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Fallback requests method failed: {str(e)}")
            return None
    
    def _parse_html_content(self, html_content):
        """Parse flight data from raw HTML content"""
        try:
            flights = {
                'outbound': [],
                'return': [],
                'search_date': datetime.now().isoformat(),
                'route': 'SFO-LAX',
                'method': 'requests_fallback'
            }
            
            # Use BeautifulSoup to parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for flight data in various formats
            # This is a basic implementation - would need refinement based on actual HTML structure
            
            # Look for price information
            price_elements = soup.find_all(text=re.compile(r'\$\d+'))
            if price_elements:
                print(f"Found {len(price_elements)} price elements")
                flights['raw_prices'] = price_elements[:10]  # First 10 prices
            
            # Look for time information
            time_elements = soup.find_all(text=re.compile(r'\d{1,2}:\d{2}'))
            if time_elements:
                print(f"Found {len(time_elements)} time elements")
                flights['raw_times'] = time_elements[:20]  # First 20 times
            
            # Look for flight numbers
            flight_numbers = soup.find_all(text=re.compile(r'UA\s?\d+'))
            if flight_numbers:
                print(f"Found {len(flight_numbers)} flight numbers")
                flights['raw_flight_numbers'] = flight_numbers
            
            # Basic flight construction (this would need more sophisticated parsing)
            if price_elements and time_elements:
                for i in range(min(len(price_elements), len(time_elements)//2)):
                    flight_info = {
                        'direction': 'outbound' if i < len(price_elements)//2 else 'return',
                        'airline': 'United Airlines',
                        'price_usd': price_elements[i] if i < len(price_elements) else None,
                        'departure_time': time_elements[i*2] if i*2 < len(time_elements) else None,
                        'arrival_time': time_elements[i*2+1] if i*2+1 < len(time_elements) else None,
                        'method': 'html_parsing'
                    }
                    
                    if i < len(price_elements)//2:
                        flights['outbound'].append(flight_info)
                    else:
                        flights['return'].append(flight_info)
            
            return flights if flights['outbound'] or flights['return'] else None
            
        except Exception as e:
            print(f"Error parsing HTML content: {str(e)}")
            return None
    
    def _build_search_url(self, origin, destination, departure_date, return_date, adults):
        """Build the United search URL with parameters"""
        base_url = "https://www.united.com/en/us/fsr/choose-flights"
        
        # URL parameters based on the example you provided
        params = {
            'f': origin,           # From (origin)
            't': destination,      # To (destination) 
            'd': departure_date,   # Departure date (YYYY-MM-DD)
            'r': return_date,      # Return date (YYYY-MM-DD)
            'sc': '7,7',          # Service class (7,7 seems to be economy)
            'px': str(adults),     # Number of passengers
            'taxng': '1',         # Tax and fees included
            'newHP': 'True',      # New homepage flag
            'clm': '7',           # Class of service
            'st': 'bestmatches',  # Sort type
            'tqp': 'R'           # Trip type (R = Round trip)
        }
        
        # Build URL with parameters
        param_string = '&'.join([f"{key}={value}" for key, value in params.items()])
        full_url = f"{base_url}?{param_string}"
        
        return full_url
    
    def _rotate_user_agent(self):
        """Rotate to a different user agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        
        import random
        new_ua = random.choice(user_agents)
        try:
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": new_ua,
                "acceptLanguage": "en-US,en;q=0.9",
                "platform": "Win32" if "Windows" in new_ua else "MacIntel" if "Mac" in new_ua else "Linux x86_64"
            })
            print(f"Rotated to new user agent: {new_ua[:50]}...")
        except Exception as e:
            print(f"Could not rotate user agent: {e}")
    
    def _handle_popups(self):
        """Handle any popups or overlays that might appear"""
        try:
            # Wait a moment for popups to appear
            time.sleep(3)
            
            # Try to close any cookie banners or popups
            popup_selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'OK')]", 
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'Dismiss')]",
                "//button[contains(text(), 'Continue')]"
            ]
            
            css_selectors = [
                ".cookie-accept",
                ".modal-close", 
                "[data-testid*='close']",
                ".close-button",
                ".dismiss-button",
                "[aria-label*='close']",
                ".overlay-close"
            ]
            
            # Try XPath selectors first
            for xpath in popup_selectors:
                try:
                    button = self.driver.find_element(By.XPATH, xpath)
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        print("Closed popup with XPath")
                        break
                except:
                    continue
            
            # Try CSS selectors
            for selector in css_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        print("Closed popup with CSS")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"No popups to handle: {str(e)}")
    
    def _wait_for_search_results(self):
        """Wait for search results to load"""
        print("Waiting for search results to load...")
        
        # Check if we're on the right page
        current_url = self.driver.current_url
        page_title = self.driver.title
        print(f"Current URL: {current_url}")
        print(f"Page title: {page_title}")
        
        # Wait for results with multiple possible selectors
        result_selectors = [
            ".flight-results",
            "[data-testid*='flight']",
            ".search-results", 
            ".flights-container",
            ".flight-card",
            ".flight-list",
            ".results-container",
            "[class*='result']",
            "[class*='flight']",
            ".flight-option",
            ".trip-option"
        ]
        
        results_loaded = False
        for selector in result_selectors:
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"Found results with selector: {selector}")
                results_loaded = True
                break
            except:
                continue
        
        if not results_loaded:
            print("Warning: Could not detect search results with standard selectors")
            # Wait longer and analyze page content
            time.sleep(15)
            
            try:
                page_text = self.driver.page_source.lower()
                if any(keyword in page_text for keyword in ['flight', 'departure', 'arrival', 'price', 'duration', 'sfo', 'lax']):
                    print("Page contains flight-related content, proceeding with extraction")
                    results_loaded = True
                else:
                    print("Page doesn't seem to contain flight results")
                    # Save page source for debugging
                    with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print("Saved page source to debug_page_source.html for inspection")
            except Exception as e:
                print(f"Error analyzing page content: {str(e)}")
        
        return results_loaded
    
    def _extract_flight_data(self):
        """Extract flight information from search results"""
        print("Extracting flight data...")
        
        flights = {
            'outbound': [],
            'return': [],
            'search_date': datetime.now().isoformat(),
            'route': 'SFO-LAX'
        }
        
        try:
            # Wait a bit for JavaScript to render
            time.sleep(5)
            
            # Try multiple selectors for flight cards
            flight_card_selectors = [
                "[data-testid='flight-card']",
                ".flight-card",
                ".flight-result",
                ".flight-option",
                ".search-result-item",
                ".flight-details",
                "[class*='flight'][class*='card']",
                "[class*='flight-row']"
            ]
            
            flight_cards_found = False
            flight_elements = []
            
            for selector in flight_card_selectors:
                try:
                    elements = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if elements:
                        flight_elements = elements
                        flight_cards_found = True
                        print(f"Found {len(flight_elements)} flight cards with selector: {selector}")
                        break
                except:
                    continue
            
            if not flight_cards_found:
                # Fallback: just get any divs that might contain flight info
                print("No flight cards found with standard selectors, trying generic approach...")
                try:
                    # Look for elements containing flight-related text
                    all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'SFO') or contains(text(), 'LAX') or contains(text(), '$') or contains(text(), 'miles')]")
                    print(f"Found {len(all_elements)} elements with flight-related content")
                    
                    # Print page source for debugging (first 2000 chars)
                    page_source = self.driver.page_source[:2000]
                    print("Page source preview:")
                    print(page_source)
                    
                except Exception as e:
                    print(f"Error in fallback search: {str(e)}")
            
            # If we found flight elements, try to parse them
            if flight_elements:
                for i, flight in enumerate(flight_elements[:20]):  # Limit to first 20
                    try:
                        flight_info = self._parse_flight_card_flexible(flight, 'outbound' if i < 10 else 'return')
                        if flight_info:
                            if i < 10:
                                flights['outbound'].append(flight_info)
                            else:
                                flights['return'].append(flight_info)
                    except Exception as e:
                        print(f"Error parsing flight {i}: {str(e)}")
                        continue
            else:
                print("No flight data could be extracted")
                
        except TimeoutException:
            print("Timeout waiting for flight results")
        except Exception as e:
            print(f"Error extracting flight data: {str(e)}")
            
        return flights
    
    def _parse_flight_card_flexible(self, flight_element, direction):
        """Parse individual flight card information with flexible selectors"""
        try:
            flight_info = {
                'direction': direction,
                'airline': 'United Airlines',
                'departure_time': None,
                'arrival_time': None,
                'duration': None,
                'stops': None,
                'price_usd': None,
                'price_miles': None,
                'cabin_class': None,
                'flight_number': None,
                'raw_text': flight_element.text  # Capture all text for debugging
            }
            
            # Get all text content for pattern matching
            element_text = flight_element.text
            
            # Extract times (looking for patterns like "6:00 AM", "18:30", etc.)
            time_pattern = r'(\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?)'
            times = re.findall(time_pattern, element_text)
            if len(times) >= 2:
                flight_info['departure_time'] = times[0]
                flight_info['arrival_time'] = times[1]
            
            # Extract prices (looking for $ or miles patterns)  
            price_usd_pattern = r'\$[\d,]+(?:\.\d{2})?'
            price_miles_pattern = r'[\d,]+\s?(?:miles|points|pts)'
            
            usd_prices = re.findall(price_usd_pattern, element_text)
            if usd_prices:
                flight_info['price_usd'] = usd_prices[0]
            
            miles_prices = re.findall(price_miles_pattern, element_text, re.IGNORECASE)
            if miles_prices:
                flight_info['price_miles'] = miles_prices[0]
            
            # Extract duration (patterns like "1h 25m", "2:30", etc.)
            duration_pattern = r'(\d+h\s?\d*m?|\d+:\d+)'
            duration_match = re.search(duration_pattern, element_text)
            if duration_match:
                flight_info['duration'] = duration_match.group(1)
            
            # Extract flight numbers (patterns like "UA 123", "United 456")
            flight_num_pattern = r'(?:UA|United)\s?(\d+)'
            flight_match = re.search(flight_num_pattern, element_text, re.IGNORECASE)
            if flight_match:
                flight_info['flight_number'] = f"UA {flight_match.group(1)}"
            
            # Determine stops (look for "nonstop", "1 stop", etc.)
            if 'nonstop' in element_text.lower() or 'non-stop' in element_text.lower():
                flight_info['stops'] = 'Nonstop'
            elif '1 stop' in element_text.lower():
                flight_info['stops'] = '1 stop'
            elif '2 stop' in element_text.lower():
                flight_info['stops'] = '2 stops'
            
            # Try specific selectors within this element
            try:
                # Look for time elements
                time_selectors = [
                    "[data-testid*='time']",
                    ".time",
                    ".departure-time",
                    ".arrival-time"
                ]
                
                for selector in time_selectors:
                    try:
                        time_elements = flight_element.find_elements(By.CSS_SELECTOR, selector)
                        if len(time_elements) >= 2:
                            flight_info['departure_time'] = time_elements[0].text.strip()
                            flight_info['arrival_time'] = time_elements[1].text.strip()
                            break
                    except:
                        continue
                
                # Look for price elements
                price_selectors = [
                    "[data-testid*='price']",
                    ".price",
                    ".fare",
                    ".cost"
                ]
                
                for selector in price_selectors:
                    try:
                        price_elements = flight_element.find_elements(By.CSS_SELECTOR, selector)
                        for price_elem in price_elements:
                            price_text = price_elem.text.strip()
                            if '$' in price_text and not flight_info['price_usd']:
                                flight_info['price_usd'] = price_text
                            elif ('miles' in price_text.lower() or 'points' in price_text.lower()) and not flight_info['price_miles']:
                                flight_info['price_miles'] = price_text
                    except:
                        continue
                        
            except Exception as e:
                print(f"Error in detailed parsing: {str(e)}")
            
            return flight_info
            
        except Exception as e:
            print(f"Error parsing flight card: {str(e)}")
            return None
    
    def save_results(self, flight_data, filename=None):
        """Save flight results to JSON and CSV files"""
        if not flight_data:
            print("No flight data to save")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_filename = filename or f"united_flights_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(flight_data, f, indent=2)
        print(f"Flight data saved to {json_filename}")
        
        # Convert to DataFrame and save as CSV
        all_flights = flight_data['outbound'] + flight_data['return']
        if all_flights:
            df = pd.DataFrame(all_flights)
            csv_filename = json_filename.replace('.json', '.csv')
            df.to_csv(csv_filename, index=False)
            print(f"Flight data saved to {csv_filename}")
    
    def close(self):
        """Close the web driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Main function to demonstrate the scraper"""
    # Example usage
    departure_date = input("Enter departure date (YYYY-MM-DD): ").strip()
    return_date = input("Enter return date (YYYY-MM-DD): ").strip()
    
    if not departure_date or not return_date:
        print("Using default dates (tomorrow and day after)")
        departure_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        return_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    
    print(f"Searching flights from SFO to LAX")
    print(f"Departure: {departure_date}")
    print(f"Return: {return_date}")
    
    scraper = UnitedFlightScraper(headless=False)  # Set to True for headless mode
    
    try:
        flight_data = scraper.search_flights(departure_date, return_date)
        
        if flight_data:
            print("\n=== SEARCH RESULTS ===")
            print(f"Found {len(flight_data['outbound'])} outbound flights")
            print(f"Found {len(flight_data['return'])} return flights")
            
            # Display sample results
            if flight_data['outbound']:
                print("\nSample Outbound Flight:")
                sample_flight = flight_data['outbound'][0]
                for key, value in sample_flight.items():
                    if value:
                        print(f"  {key}: {value}")
            
            # Save results
            scraper.save_results(flight_data)
        else:
            print("No flight data retrieved")
            
    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    # Install required packages
    print("Required packages: selenium, beautifulsoup4, pandas, requests")
    print("Install with: pip install selenium beautifulsoup4 pandas requests")
    print("Also need ChromeDriver: https://chromedriver.chromium.org/\n")
    
    main()
