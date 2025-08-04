import os
import re
import json
import time
import platform
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from langchain_google_vertexai import VertexAI
import googlemaps
from dotenv import load_dotenv
import vertexai 
from vertexai import agent_engines 

load_dotenv()

class EventAgent:
    """
    An intelligent agent that extracts event information from URLs,
    finds nearby restaurants, and drafts booking emails.
    """
    
    def __init__(self, 
                 vertex_project_id: str = None,
                 vertex_location: str = None,
                 bucket_name: str = None,
                 google_maps_api_key: str = None):
        """
        Initialize the EventAgent with required API credentials.
        
        Args:
            vertex_project_id: Google Cloud project ID for Vertex AI
            vertex_location: Vertex AI location (must be a supported region)
            google_maps_api_key: Google Maps API key for restaurant search
        """
        self.vertex_project_id = vertex_project_id or os.getenv('VERTEX_PROJECT_ID')
        # Use a supported Vertex AI region - us-east1 is widely available
        self.vertex_location = vertex_location or os.getenv('VERTEX_LOCATION', 'us-east1')
        self.bucket_name = bucket_name or os.getenv('BUCKET_NAME')

        self.google_maps_api_key = google_maps_api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Initialize Vertex AI
        if self.vertex_project_id:
            try:
                # Explicitly set project for Google Cloud libraries
                os.environ["GOOGLE_CLOUD_PROJECT"] = self.vertex_project_id
                
                # Initialize with just project and location - staging bucket is optional
                if self.bucket_name:
                    vertexai.init(project=self.vertex_project_id, location=self.vertex_location, staging_bucket=f"gs://{self.bucket_name}")
                else:
                    vertexai.init(project=self.vertex_project_id, location=self.vertex_location)
                # Try different model names in order of preference
                model_names = [
                    "gemini-2.0-flash",
                ]
                
                self.llm = None
                for model_name in model_names:
                    try:
                        self.llm = VertexAI(
                            model_name=model_name,
                            project=self.vertex_project_id,
                            location=self.vertex_location,
                            temperature=0.3
                        )
                        print(f"✅ Successfully initialized Vertex AI with model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"⚠️ Model {model_name} not available: {model_error}")
                        # Try to handle auth issues specifically
                        if "metadata" in str(model_error).lower() or "503" in str(model_error):
                            print("🔧 Detected metadata service issue, trying alternative auth...")
                            try:
                                # Force no credentials to use environment variable approach
                                original_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
                                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""
                                self.llm = VertexAI(
                                    model_name=model_name,
                                    project=self.vertex_project_id,
                                    location=self.vertex_location,
                                    temperature=0.3
                                )
                                print(f"✅ Successfully initialized Vertex AI with alternative auth: {model_name}")
                                break
                            except Exception as alt_error:
                                print(f"❌ Alternative auth also failed: {alt_error}")
                                # Restore original credentials
                                if original_creds:
                                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_creds
                        continue
                
                if self.llm is None:
                    print("⚠️ No Vertex AI models available. Agent will work with basic extraction only.")
            except Exception as e:
                print(f"Warning: Vertex AI initialization failed: {e}")
                self.llm = None
        
        # Initialize Google Maps client
        if self.google_maps_api_key:
            self.gmaps = googlemaps.Client(key=self.google_maps_api_key)
        else:
            self.gmaps = None

        # Set up Chrome driver for web scraping
        self.driver = None
        
        # Email configuration defaults
        self.email_config = {
            'gmail': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'use_tls': True
            },
            'outlook': {
                'smtp_server': 'smtp.office365.com',
                'smtp_port': 587,
                'use_tls': True
            },
            'yahoo': {
                'smtp_server': 'smtp.mail.yahoo.com',
                'smtp_port': 587,
                'use_tls': True
            }
        }
    
    def _sanitize_email_input(self, text: str) -> str:
        """
        Sanitize email input by removing non-ASCII characters and normalizing whitespace.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove non-breaking spaces and other problematic Unicode characters
        text = text.replace('\xa0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\u200c', '')  # Zero-width non-joiner
        text = text.replace('\u200d', '')  # Zero-width joiner
        text = text.replace('\ufeff', '')  # Byte order mark
        
        # Convert to ASCII, ignoring non-ASCII characters
        try:
            text = text.encode('ascii', 'ignore').decode('ascii')
        except Exception:
            # If encoding fails, manually filter to ASCII
            text = ''.join(char for char in text if ord(char) < 128)
        
        # Strip whitespace and normalize
        text = text.strip()
        
        return text
    
    def send_email(self, 
                   sender_email: str, 
                   sender_password: str,
                   recipient_email: str,
                   subject: str,
                   body: str,
                   email_provider: str = 'gmail') -> Dict[str, any]:
        """
        Send an email using SMTP.
        
        Args:
            sender_email: Sender's email address
            sender_password: Sender's email password or app password
            recipient_email: Recipient's email address
            subject: Email subject
            body: Email body content
            email_provider: Email provider ('gmail', 'outlook', 'yahoo')
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Sanitize inputs to remove problematic characters
            sender_email = self._sanitize_email_input(sender_email)
            sender_password = self._sanitize_email_input(sender_password)
            recipient_email = self._sanitize_email_input(recipient_email)
            subject = self._sanitize_email_input(subject)
            
            # Validate inputs
            if not sender_email or not sender_password or not recipient_email:
                return {
                    'success': False,
                    'error': "Email, password, and recipient are required"
                }
            
            # Basic email validation
            if '@' not in sender_email or '@' not in recipient_email:
                return {
                    'success': False,
                    'error': "Invalid email address format"
                }
            
            # Get SMTP configuration
            if email_provider not in self.email_config:
                return {
                    'success': False,
                    'error': f"Unsupported email provider: {email_provider}. Supported: {list(self.email_config.keys())}"
                }
            
            config = self.email_config[email_provider]
            
            # Create message with proper encoding
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add body to email with UTF-8 encoding
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Create SMTP session with timeout
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30)
            
            if config['use_tls']:
                server.starttls()  # Enable security
            
            # Login with sender's credentials
            server.login(sender_email, sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            
            return {
                'success': True,
                'message': f"Email sent successfully to {recipient_email}"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            return {
                'success': False,
                'error': f"Authentication failed. Please check your email and password/app password. Details: {str(e)}"
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                'success': False,
                'error': f"Recipient email address '{recipient_email}' was refused by the server. Details: {str(e)}"
            }
        except smtplib.SMTPServerDisconnected as e:
            return {
                'success': False,
                'error': f"SMTP server disconnected. Please try again. Details: {str(e)}"
            }
        except UnicodeEncodeError as e:
            return {
                'success': False,
                'error': f"Character encoding error. Please check for special characters in your email or password. Details: {str(e)}"
            }
        except Exception as e:
            error_msg = str(e)
            
            # Provide more helpful error messages for common issues
            if 'ascii' in error_msg.lower() or 'encode' in error_msg.lower():
                return {
                    'success': False,
                    'error': "Character encoding error detected. Try retyping your email and password manually (don't copy-paste) to avoid hidden characters."
                }
            elif 'timeout' in error_msg.lower():
                return {
                    'success': False,
                    'error': "Connection timeout. Please check your internet connection and try again."
                }
            elif 'authentication' in error_msg.lower():
                return {
                    'success': False,
                    'error': "Authentication failed. For Gmail, make sure you're using an App Password, not your regular password."
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to send email: {error_msg}"
                }
    
    def send_booking_emails(self,
                           sender_email: str,
                           sender_password: str,
                           draft_emails: List[Dict],
                           email_provider: str = 'gmail') -> List[Dict[str, any]]:
        """
        Send multiple booking emails to restaurants.
        
        Args:
            sender_email: Sender's email address
            sender_password: Sender's email password or app password
            draft_emails: List of draft email dictionaries
            email_provider: Email provider ('gmail', 'outlook', 'yahoo')
            
        Returns:
            List of results for each email sent
        """
        results = []
        
        for i, draft in enumerate(draft_emails):
            restaurant = draft['restaurant']
            email_content = draft['email']
            
            # Extract subject and body from email content
            lines = email_content.split('\n')
            subject_line = None
            body_lines = []
            
            for line in lines:
                if line.startswith('Subject:'):
                    subject_line = line.replace('Subject:', '').strip()
                elif subject_line is not None:  # Only add to body after subject is found
                    body_lines.append(line)
            
            if not subject_line:
                subject_line = f"Table Reservation Request - {restaurant.get('name', 'Restaurant')}"
            
            body = '\n'.join(body_lines).strip()
            
            # Try to find restaurant email
            restaurant_email = self._find_restaurant_email(restaurant)
            
            if not restaurant_email:
                results.append({
                    'restaurant': restaurant.get('name', f'Restaurant {i+1}'),
                    'success': False,
                    'error': 'No email address found for restaurant. Please contact them directly.',
                    'phone': restaurant.get('phone'),
                    'website': restaurant.get('website')
                })
                continue
            
            # Send email
            result = self.send_email(
                sender_email=sender_email,
                sender_password=sender_password,
                recipient_email=restaurant_email,
                subject=subject_line,
                body=body,
                email_provider=email_provider
            )
            
            results.append({
                'restaurant': restaurant.get('name', f'Restaurant {i+1}'),
                'recipient_email': restaurant_email,
                'success': result['success'],
                'message': result.get('message'),
                'error': result.get('error')
            })
        
        return results
    
    def _find_restaurant_email(self, restaurant: Dict[str, any]) -> Optional[str]:
        """
        Try to find a restaurant's email address from various sources.
        
        Args:
            restaurant: Restaurant information dictionary
            
        Returns:
            Restaurant email if found, None otherwise
        """
        # Method 1: Check if email is already in restaurant data
        if restaurant.get('email'):
            return restaurant['email']
        
        # Method 2: Try to get more details from Google Places if we have place_id
        place_id = restaurant.get('place_id')
        if place_id and hasattr(self, 'gmaps') and self.gmaps:
            try:
                details = self.gmaps.place(
                    place_id=place_id,
                    fields=['formatted_phone_number', 'website', 'opening_hours', 'formatted_address', 'url']
                )
                
                result = details.get('result', {})
                
                # Sometimes Google Places returns contact info in additional fields
                if result.get('email'):
                    return result['email']
                
                # Try to scrape email from restaurant website
                website = result.get('website')
                if website:
                    email = self._extract_email_from_website(website)
                    if email:
                        return email
                        
            except Exception as e:
                print(f"Error getting restaurant details: {str(e)}")
        
        # Method 3: Try to scrape email from existing website URL
        website = restaurant.get('website')
        if website:
            email = self._extract_email_from_website(website)
            if email:
                return email
        
        # Method 4: Generate likely email addresses based on restaurant name and try common patterns
        restaurant_name = restaurant.get('name')
        if restaurant_name:
            return self._generate_likely_email(restaurant_name, restaurant)
        
        return None
    
    def _extract_email_from_website(self, website_url: str) -> Optional[str]:
        """
        Try to extract email address from restaurant website.
        
        Args:
            website_url: Restaurant website URL
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Don't spend too much time on this - set short timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(website_url, headers=headers, timeout=5)
            if response.status_code == 200:
                content = response.text.lower()
                
                # Look for email patterns
                import re
                email_patterns = [
                    r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
                    r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                ]
                
                for pattern in email_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Filter out common non-restaurant emails
                        excluded_domains = ['example.com', 'test.com', 'gmail.com', 'yahoo.com', 'hotmail.com']
                        excluded_prefixes = ['noreply', 'no-reply', 'admin', 'webmaster', 'info@facebook', 'info@twitter']
                        
                        for match in matches:
                            email = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else str(match)
                            email = email.lower().strip()
                            
                            # Skip common non-restaurant emails
                            if any(domain in email for domain in excluded_domains):
                                continue
                            if any(prefix in email for prefix in excluded_prefixes):
                                continue
                            if len(email) > 50:  # Probably not a real email
                                continue
                                
                            return email
                            
        except Exception as e:
            print(f"Error extracting email from website {website_url}: {str(e)}")
        
        return None
    
    def _generate_likely_email(self, restaurant_name: str, restaurant: Dict[str, any]) -> Optional[str]:
        """
        Generate likely email addresses based on restaurant name and location.
        
        Args:
            restaurant_name: Name of the restaurant
            restaurant: Restaurant information dictionary
            
        Returns:
            Most likely email address or None
        """
        try:
            # Clean restaurant name for email generation
            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', restaurant_name.lower())
            clean_name = re.sub(r'\s+', '', clean_name)  # Remove spaces
            
            # Try to extract domain from website if available
            website = restaurant.get('website')
            domain = None
            
            if website:
                # Extract domain from website URL
                import urllib.parse
                parsed = urllib.parse.urlparse(website)
                if parsed.netloc:
                    domain = parsed.netloc.replace('www.', '')
            
            if domain:
                # Generate likely emails using the website domain
                likely_emails = [
                    f"info@{domain}",
                    f"contact@{domain}",
                    f"reservations@{domain}",
                    f"booking@{domain}",
                    f"{clean_name}@{domain}",
                ]
                
                # Return the most likely one (info@ is most common)
                return likely_emails[0]
            
        except Exception as e:
            print(f"Error generating likely email: {str(e)}")
        
        return None
    
    def get_email_providers(self) -> List[str]:
        """Get list of supported email providers."""
        return list(self.email_config.keys())
    
    def validate_email_config(self, 
                             sender_email: str, 
                             sender_password: str, 
                             email_provider: str) -> Dict[str, any]:
        """
        Validate email configuration by attempting to connect to SMTP server.
        
        Args:
            sender_email: Sender's email address
            sender_password: Sender's email password or app password
            email_provider: Email provider
            
        Returns:
            Validation result
        """
        try:
            # Sanitize inputs
            sender_email = self._sanitize_email_input(sender_email)
            sender_password = self._sanitize_email_input(sender_password)
            
            # Validate inputs
            if not sender_email or not sender_password:
                return {
                    'valid': False,
                    'error': "Email and password are required"
                }
            
            # Basic email validation
            if '@' not in sender_email:
                return {
                    'valid': False,
                    'error': "Invalid email address format"
                }
            
            if email_provider not in self.email_config:
                return {
                    'valid': False,
                    'error': f"Unsupported email provider: {email_provider}"
                }
            
            config = self.email_config[email_provider]
            
            # Test SMTP connection with timeout
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=30)
            
            if config['use_tls']:
                server.starttls()
            
            server.login(sender_email, sender_password)
            server.quit()
            
            return {
                'valid': True,
                'message': "Email configuration is valid!"
            }
            
        except smtplib.SMTPAuthenticationError as e:
            error_details = str(e)
            if email_provider == 'gmail':
                return {
                    'valid': False,
                    'error': f"Gmail authentication failed. Make sure you're using an App Password (not your regular password). Enable 2FA first, then generate an App Password at: https://myaccount.google.com/apppasswords"
                }
            else:
                return {
                    'valid': False,
                    'error': f"Authentication failed for {email_provider}. Please check your credentials. Details: {error_details}"
                }
        except UnicodeEncodeError as e:
            return {
                'valid': False,
                'error': "Character encoding error detected. Please retype your email and password manually (don't copy-paste) to avoid hidden characters."
            }
        except Exception as e:
            error_msg = str(e)
            
            # Provide helpful error messages
            if 'ascii' in error_msg.lower() or 'encode' in error_msg.lower():
                return {
                    'valid': False,
                    'error': "Character encoding error. Try retyping your credentials manually instead of copy-pasting."
                }
            elif 'timeout' in error_msg.lower():
                return {
                    'valid': False,
                    'error': "Connection timeout. Please check your internet connection."
                }
            elif 'name resolution' in error_msg.lower() or 'getaddrinfo' in error_msg.lower():
                return {
                    'valid': False,
                    'error': "Network error. Please check your internet connection."
                }
            else:
                return {
                    'valid': False,
                    'error': f"Connection failed: {error_msg}"
                }
    
    def setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        # Essential options for headless mode
        chrome_options.add_argument("--headless=new")  # Use new headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        
        # Window and display options
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Security and performance options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        chrome_options.add_argument("--ignore-certificate-errors-spki-list")
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # macOS specific options
        if os.name == 'posix':  # Unix/Linux/macOS
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
        
        try:
            # Try to use ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except Exception as e:
            print(f"Warning: Failed to setup Chrome driver with ChromeDriverManager: {e}")
            
            try:
                # Fallback: try without service (system PATH)
                driver = webdriver.Chrome(options=chrome_options)
                return driver
            except Exception as e2:
                print(f"Error: Failed to setup Chrome driver: {e2}")
                raise Exception(f"Cannot initialize Chrome driver. Please ensure Chrome is installed and try: 'brew install chromedriver' on macOS or visit https://chromedriver.chromium.org/")
    
    def extract_event_info(self, url: str) -> Dict[str, any]:
        """
        Extract event information from the given URL.
        
        Args:
            url: The event URL to scrape
            
        Returns:
            Dictionary containing extracted event information
        """
        # Enhanced cloud environment detection
        
        # Multiple ways to detect cloud/containerized environments
        cloud_indicators = [
            'STREAMLIT_SHARING_MODE' in os.environ,
            'STREAMLIT_CLOUD' in os.environ,
            'share.streamlit.io' in os.environ.get('HTTP_HOST', ''),
            '/app' in os.getcwd(),
            platform.system() == 'Linux' and not os.path.exists('/usr/bin/google-chrome'),
            'KUBERNETES_SERVICE_HOST' in os.environ,
            'DYNO' in os.environ,  # Heroku
            'RENDER' in os.environ,  # Render
        ]
        
        is_cloud = any(cloud_indicators)
        
        print(f"🔍 Environment check:")
        print(f"   Platform: {platform.system()}")
        print(f"   CWD: {os.getcwd()}")
        print(f"   Cloud indicators: {sum(cloud_indicators)}/8")
        print(f"   Is cloud: {is_cloud}")
        
        # Always try requests first in cloud environments, or if Chrome is not available
        if is_cloud:
            print("☁️ Cloud environment detected - using requests-only extraction")
            try:
                return self._extract_with_requests(url)
            except Exception as requests_error:
                print(f"❌ Requests extraction failed: {requests_error}")
                return {"error": f"Content extraction failed in cloud environment: {requests_error}"}
        else:
            print("💻 Local environment - trying Selenium first")
            # First try with Selenium (for dynamic content)  
            try:
                # Quick Chrome availability check
                import shutil
                if not shutil.which('google-chrome') and not shutil.which('chromium'):
                    print("⚠️ Chrome not found, falling back to requests")
                    return self._extract_with_requests(url)
                
                return self._extract_with_selenium(url)
            except Exception as selenium_error:
                print(f"❌ Selenium extraction failed: {selenium_error}")
                print("🔄 Falling back to HTTP requests...")
                
                # Fallback to simple requests
                try:
                    return self._extract_with_requests(url)
                except Exception as requests_error:
                    print(f"❌ Requests extraction also failed: {requests_error}")
                    return {"error": f"All extraction methods failed. Selenium: {selenium_error}, Requests: {requests_error}"}
    
    def _extract_with_selenium(self, url: str) -> Dict[str, any]:
        """Extract using Selenium WebDriver."""
        self.driver = None
        try:
            # Normalize URL
            url = self._normalize_url(url)
            self.driver = self.setup_driver()
            print(f"Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get initial page content
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract text content for analysis
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Look for common event information patterns
            event_info = self._extract_basic_info(soup, text_content)
            
            # Try to find additional information by clicking links/tabs
            additional_info = self._explore_additional_content()
            
            # Merge information
            event_info.update(additional_info)
            
            # Use Vertex AI to process and structure the information
            structured_info = self._process_with_ai(text_content, event_info)
            
            return structured_info
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
    
    def _extract_with_requests(self, url: str) -> Dict[str, any]:
        """Fallback extraction using simple HTTP requests."""
        print(f"🌐 Starting HTTP extraction for: {url}")
        
        # Normalize URL
        url = self._normalize_url(url)
        print(f"🔗 Normalized URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        try:
            print("📡 Sending HTTP request...")
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            print(f"✅ HTTP response: {response.status_code}")
            response.raise_for_status()
            
            print("🔍 Parsing HTML content...")
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text(separator=' ', strip=True)
            print(f"📄 Content length: {len(text_content)} characters")
            
            if len(text_content) < 100:
                print("⚠️ Very short content - might be blocked or empty")
                return {"error": "Retrieved content is too short - possible blocking or empty page"}
            
            # Extract basic info
            print("🔍 Extracting basic information...")
            event_info = self._extract_basic_info(soup, text_content)
            
            # Use AI to process if available
            if hasattr(self, 'llm') and self.llm:
                print("🤖 Processing with AI...")
                structured_info = self._process_with_ai(text_content, event_info)
                print("✅ AI processing completed")
                return structured_info
            else:
                print("⚠️ AI not available, returning basic extraction")
                return event_info
                
        except requests.exceptions.Timeout:
            return {"error": "Request timed out - website took too long to respond"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection failed - check internet connection or website availability"}
        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP error {e.response.status_code}: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error during HTTP extraction: {str(e)}"}
    
    def _extract_basic_info(self, soup: BeautifulSoup, text_content: str) -> Dict[str, any]:
        """Extract basic event information using CSS selectors and text patterns."""
        info = {}
        
        # Try to find event title
        title_selectors = ['h1', '.event-title', '.title', '[class*="title"]', '[class*="event"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                info['title'] = title_elem.get_text(strip=True)
                break
        
        # Look for date/time patterns
        date_patterns = [
            r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                info['dates'] = matches
                break
        
        # Look for time patterns
        time_patterns = [
            r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b',
            r'\b\d{1,2}:\d{2}\b'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                info['times'] = matches
                break
        
        # Look for location/address patterns
        location_patterns = [
            r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b',
            r'\b[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                info['addresses'] = matches
                break
        
        return info
    
    def _explore_additional_content(self) -> Dict[str, any]:
        """Explore additional tabs/links to find more event information."""
        additional_info = {}
        
        # Only try this if we have a driver available
        if not hasattr(self, 'driver') or self.driver is None:
            return additional_info
        
        try:
            # Look for common navigation elements
            nav_selectors = [
                'a[href*="agenda"]', 'a[href*="schedule"]', 'a[href*="program"]',
                'a[href*="location"]', 'a[href*="venue"]', 'a[href*="address"]',
                '[class*="tab"]', '[class*="menu"]', 'nav a'
            ]
            
            for selector in nav_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links[:4]:  # Limit to first 2 links to avoid too much exploration
                        try:
                            link_text = link.text.lower()
                            if any(keyword in link_text for keyword in ['agenda', 'schedule', 'location', 'venue', 'details']):
                                original_url = self.driver.current_url
                                
                                # Get the link URL instead of clicking (safer)
                                link_url = link.get_attribute('href')
                                if link_url and link_url.startswith('http'):
                                    self.driver.get(link_url)
                                else:
                                    link.click()
                                
                                time.sleep(3)  # Wait for page to load
                                
                                # Extract information from new page
                                page_source = self.driver.page_source
                                soup = BeautifulSoup(page_source, 'html.parser')
                                text_content = soup.get_text(separator=' ', strip=True)
                                
                                if 'agenda' in link_text or 'schedule' in link_text:
                                    additional_info['agenda_content'] = text_content[:20000]  # Limit content
                                elif 'location' in link_text or 'venue' in link_text:
                                    additional_info['location_content'] = text_content[:20000]
                                
                                # Go back to original page
                                self.driver.get(original_url)
                                time.sleep(2)
                                break  # Only explore one additional page per selector
                                
                        except Exception as e:
                            print(f"Error exploring individual link: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Error finding links with selector {selector}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error in additional content exploration: {str(e)}")
        
        return additional_info
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by adding scheme if missing."""
        url = url.strip()
        
        # If no scheme, add https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def _build_full_address(self, event_info: Dict) -> str:
        """Build a complete address from components."""
        components = []
        
        if event_info.get('address'):
            components.append(event_info['address'])
        if event_info.get('city'):
            components.append(event_info['city'])
        if event_info.get('state'):
            components.append(event_info['state'])
        if event_info.get('zip_code'):
            components.append(event_info['zip_code'])
        if event_info.get('country') and event_info['country'].upper() != 'USA':
            components.append(event_info['country'])
        
        return ', '.join(components) if components else None
    
    def _build_venue_location(self, event_info: Dict) -> str:
        """Build venue with location context."""
        venue = event_info.get('venue_name')
        if not venue:
            return None
        
        location_parts = []
        if event_info.get('city'):
            location_parts.append(event_info['city'])
        if event_info.get('state'):
            location_parts.append(event_info['state'])
        
        if location_parts:
            return f"{venue}, {', '.join(location_parts)}"
        return venue
    
    def _build_city_state(self, event_info: Dict) -> str:
        """Build city, state combination."""
        city = event_info.get('city')
        state = event_info.get('state')
        
        if city and state:
            return f"{city}, {state}"
        elif city:
            return city
        return None
    
    def _process_with_ai(self, text_content: str, basic_info: Dict) -> Dict[str, any]:
        """Use Vertex AI to intelligently extract and structure event information."""
        if not hasattr(self, 'llm') or self.llm is None:
            print("⚠️ AI processing not available - using basic extraction only")
            return basic_info
        
        print("🤖 Using AI to extract comprehensive event information...")
        
        # Create a comprehensive prompt for better extraction
        prompt = f"""
        You are an expert event information extraction system. Analyze the following web page content and extract ALL available event information with high accuracy.

        CRITICAL: Focus especially on LOCATION information as this is essential for finding nearby restaurants.

        Web page content:
        {text_content}

        Previously extracted basic info:
        {json.dumps(basic_info, indent=2)}

        EXTRACT AND STRUCTURE the following information:

        1. EVENT DETAILS:
           - Title/Name of the event
           - Date(s) in YYYY-MM-DD format
           - Start time and end time in HH:MM format
           - Duration or multiple days
           - Event type (conference, festival, workshop, etc.)
           - Description/summary

        2. LOCATION INFORMATION (CRITICAL - extract every location detail you can find):
           - Venue/facility name
           - Complete street address (number, street, city, state, zip)
           - Building name or room number
           - City and state/province
           - Country
           - Nearby landmarks or cross streets
           - Campus or complex name

        3. ADDITIONAL DETAILS:
           - Agenda/schedule items with times
           - Speakers or performers
           - Registration/ticket information
           - Contact details
           - Parking information
           - Public transportation access

        SEARCH STRATEGY:
        - Look for addresses in various formats (123 Main St, 123 Main Street, etc.)
        - Check for venue names (Convention Center, Hotel, University, etc.)
        - Find city/state combinations
        - Look for zip codes and postal codes
        - Search for campus or building names
        - Check contact sections for addresses
        - Look in footer information
        - Check "location", "venue", "address", "directions" sections

        OUTPUT FORMAT:
        Return a valid JSON object with this exact structure:
        {{
            "title": "Complete event title",
            "date": "YYYY-MM-DD or date range",
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "venue_name": "Full venue/facility name",
            "address": "Complete street address",
            "city": "City name",
            "state": "State/Province",
            "country": "Country",
            "zip_code": "Postal code",
            "building": "Building or room details",
            "campus": "Campus or complex name",
            "landmarks": "Nearby landmarks or cross streets",
            "full_location": "Most complete location string for mapping",
            "agenda": ["List of agenda items with times"],
            "description": "Event description",
            "event_type": "Type of event",
            "speakers": ["Speaker names"],
            "contact_email": "Contact email",
            "contact_phone": "Contact phone",
            "website": "Event website",
            "parking_info": "Parking details",
            "transportation": "Public transport info"
        }}

        IMPORTANT RULES:
        1. If a field cannot be determined, use null (not empty string)
        2. For location, be as specific as possible - include all address components
        3. Create a "full_location" field with the most complete location string for mapping
        4. Look carefully for ANY location information, even if scattered across the page
        5. Return valid JSON only - no extra text or explanations
        6. If multiple events are listed, focus on the main/featured event
        """
        print(prompt)
        try:
            print("🔍 Sending content to AI for analysis...")
            response = self.llm.invoke(prompt)
            print(response)
            print(f"🤖 AI response received ({len(response)} characters)")
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    ai_extracted = json.loads(json_match.group())
                    print("✅ AI extraction successful!")
                    
                    # Log what location info was found
                    location_fields = ['venue_name', 'address', 'city', 'state', 'full_location']
                    found_locations = []
                    for field in location_fields:
                        if ai_extracted.get(field):
                            found_locations.append(f"{field}: {ai_extracted[field]}")
                    
                    if found_locations:
                        print(f"📍 AI found location info: {', '.join(found_locations)}")
                    else:
                        print("⚠️ AI could not find location information")
                    
                    return ai_extracted
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"🔍 Raw AI response: {response[:500]}...")
                    return {"ai_response": response, **basic_info}
            else:
                print("❌ No JSON found in AI response")
                print(f"🔍 Raw AI response: {response[:500]}...")
                return {"ai_response": response, **basic_info}
                
        except Exception as e:
            print(f"❌ AI processing failed: {str(e)}")
            return basic_info
    
    def search_restaurants(self, event_info: Dict[str, any], 
                          radius: int = 2000,
                          meal_time: str = "dinner") -> List[Dict[str, any]]:
        """
        Search for restaurants near the event location.
        
        Args:
            event_info: Event information containing location
            radius: Search radius in meters
            meal_time: Type of meal (breakfast, lunch, dinner)
            
        Returns:
            List of restaurant information
        """
        print(f"🔍 Searching for restaurants...")
        print(f"📍 Event info available: {list(event_info.keys())}")
        
        # Check if Google Maps API is configured
        if not hasattr(self, 'gmaps') or self.gmaps is None:
            print("❌ Google Maps API not configured. Please set GOOGLE_MAPS_API_KEY environment variable.")
            return []
        
        # Extract location information with priority order
        location_candidates = [
            # AI-extracted comprehensive location (highest priority)
            event_info.get('full_location'),
            # Complete address combinations
            self._build_full_address(event_info),
            # Individual address components
            event_info.get('address'),
            event_info.get('full_address'),
            # Venue with location context
            self._build_venue_location(event_info),
            event_info.get('venue_name'),
            # City/state combinations
            self._build_city_state(event_info),
            event_info.get('city'),
            # Fallback to any address-like data
            event_info.get('addresses', [None])[0] if event_info.get('addresses') else None,
            event_info.get('campus'),
            event_info.get('building')
        ]
        
        location = None
        for candidate in location_candidates:
            if candidate and len(str(candidate).strip()) > 3:
                location = str(candidate).strip()
                break
        
        if not location:
            print("❌ No location information found in event data.")
            print(f"📋 Available event data: {event_info}")
            return []
        
        print(f"📍 Using location: '{location}'")
        print(f"🔍 Search radius: {radius} meters")
        
        try:
            # Try different search approaches
            restaurants = []
            
            # Method 1: Places nearby search
            try:
                print("🔍 Trying Places nearby search...")
                places_result = self.gmaps.places_nearby(
                    location=location,
                    radius=radius,
                    type='restaurant',
                    language='en'
                )
                
                status = places_result.get('status', 'UNKNOWN')
                print(f"📊 Places API status: {status}")
                
                if status == 'OK':
                    results = places_result.get('results', [])
                    print(f"✅ Found {len(results)} restaurants via nearby search")
                    restaurants.extend(results[:10])
                elif status == 'ZERO_RESULTS':
                    print("⚠️ No restaurants found in the specified area")
                elif status == 'INVALID_REQUEST':
                    print("❌ Invalid request - possibly bad location format")
                else:
                    print(f"⚠️ Places API returned status: {status}")
                    
            except Exception as e:
                print(f"❌ Places nearby search failed: {e}")
            
            # Method 2: Text search if nearby search failed
            if not restaurants:
                try:
                    print("🔍 Trying text search...")
                    query = f"restaurants near {location}"
                    places_result = self.gmaps.places(
                        query=query,
                        language='en'
                    )
                    
                    status = places_result.get('status', 'UNKNOWN')
                    print(f"📊 Text search status: {status}")
                    
                    if status == 'OK':
                        results = places_result.get('results', [])
                        print(f"✅ Found {len(results)} restaurants via text search")
                        restaurants.extend(results[:10])
                        
                except Exception as e:
                    print(f"❌ Text search failed: {e}")
            
            # Method 3: Try geocoding the location first
            if not restaurants:
                try:
                    print("🔍 Trying geocoding + nearby search...")
                    geocode_result = self.gmaps.geocode(location)
                    
                    if geocode_result:
                        lat_lng = geocode_result[0]['geometry']['location']
                        print(f"📍 Geocoded to: {lat_lng}")
                        
                        places_result = self.gmaps.places_nearby(
                            location=lat_lng,
                            radius=radius,
                            type='restaurant',
                            language='en'
                        )
                        
                        if places_result.get('status') == 'OK':
                            results = places_result.get('results', [])
                            print(f"✅ Found {len(results)} restaurants via geocoded search")
                            restaurants.extend(results[:10])
                    else:
                        print("❌ Could not geocode the location")
                        
                except Exception as e:
                    print(f"❌ Geocoding search failed: {e}")
            
            # Process results
            if not restaurants:
                print("❌ No restaurants found with any method")
                print("💡 Suggestions:")
                print("   - Check if Google Places API is enabled in your project")
                print("   - Verify your API key has proper permissions")
                print("   - Try a more specific location (include city/state)")
                print("   - Increase search radius")
                return []
            
            print(f"✅ Processing {len(restaurants)} restaurant results...")
            
            processed_restaurants = []
            for place in restaurants[:10]:  # Limit to 10 restaurants
                restaurant_info = {
                    'name': place.get('name'),
                    'rating': place.get('rating'),
                    'price_level': place.get('price_level'),
                    'address': place.get('vicinity') or place.get('formatted_address'),
                    'place_id': place.get('place_id'),
                    'types': place.get('types', [])
                }
                
                # Get additional details
                details = self._get_restaurant_details(place.get('place_id'))
                restaurant_info.update(details)
                
                processed_restaurants.append(restaurant_info)
            
            print(f"🍽️ Successfully found {len(processed_restaurants)} restaurants")
            return processed_restaurants
            
        except Exception as e:
            print(f"❌ Restaurant search failed with error: {str(e)}")
            print(f"🔍 Error type: {type(e).__name__}")
            
            # Check for common API issues
            if 'API_KEY' in str(e).upper():
                print("💡 This looks like an API key issue. Please check:")
                print("   - Your Google Maps API key is correct")
                print("   - Places API is enabled in your Google Cloud project")
                print("   - Billing is set up for your project")
            elif 'QUOTA' in str(e).upper():
                print("💡 This looks like a quota issue. You may have exceeded your API limits.")
            elif 'PERMISSION' in str(e).upper():
                print("💡 This looks like a permission issue. Check your API key permissions.")
            
            return []
    
    def _get_restaurant_details(self, place_id: str) -> Dict[str, any]:
        """Get additional restaurant details using Google Places API."""
        try:
            details = self.gmaps.place(
                place_id=place_id,
                fields=['formatted_phone_number', 'website', 'opening_hours', 'formatted_address', 'url', 'editorial_summary']
            )
            
            result = details.get('result', {})
            restaurant_details = {
                'phone': result.get('formatted_phone_number'),
                'website': result.get('website'),
                'full_address': result.get('formatted_address'),
                'opening_hours': result.get('opening_hours', {}).get('weekday_text', [])
            }
            
            # Try to find email from the website
            website = result.get('website')
            if website:
                email = self._extract_email_from_website(website)
                if email:
                    restaurant_details['email'] = email
            
            return restaurant_details
            
        except Exception as e:
            print(f"Error getting restaurant details: {str(e)}")
            return {}
    
    def draft_booking_email(self, event_info: Dict[str, any], 
                           restaurant_info: Dict[str, any],
                           party_size: int = 4) -> str:
        """
        Draft an email to book a table at a restaurant.
        
        Args:
            event_info: Event information
            restaurant_info: Restaurant information
            party_size: Number of people
            
        Returns:
            Drafted email content
        """
        if not hasattr(self, 'llm') or self.llm is None:
            return self._create_basic_email_template(event_info, restaurant_info, party_size)
        
        prompt = f"""
        Draft a professional and polite email to book a table at a restaurant for an event.
        
        Event Information:
        - Event: {event_info.get('title', 'Event')}
        - Date: {event_info.get('date', 'TBD')}
        - Time: {event_info.get('start_time', 'TBD')} - {event_info.get('end_time', 'TBD')}
        - Location: {event_info.get('venue_name', 'TBD')}
        
        Restaurant Information:
        - Name: {restaurant_info.get('name', 'Restaurant')}
        - Address: {restaurant_info.get('full_address', restaurant_info.get('address', 'TBD'))}
        
        Booking Details:
        - Party size: {party_size} people
        - Preferred time: Based on event schedule
        
        Please create an email with:
        1. Professional subject line
        2. Polite greeting
        3. Brief explanation of the event
        4. Specific booking request with preferred time
        5. Contact information request
        6. Professional closing
        
        Format as a complete email with Subject, Dear [Restaurant Name] Team, body, and signature.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            print(f"Error drafting email with AI: {str(e)}")
            return self._create_basic_email_template(event_info, restaurant_info, party_size)
    
    def _create_basic_email_template(self, event_info: Dict[str, any], 
                                   restaurant_info: Dict[str, any],
                                   party_size: int) -> str:
        """Create a basic email template without AI."""
        subject = f"Table Reservation Request for {party_size} - {event_info.get('date', 'TBD')}"
        
        body = f"""Subject: {subject}

Dear {restaurant_info.get('name', 'Restaurant')} Team,

I hope this email finds you well. I am writing to inquire about making a reservation at your restaurant.

Event Details:
- Event: {event_info.get('title', 'Special Event')}
- Date: {event_info.get('date', 'TBD')}
- Event Time: {event_info.get('start_time', 'TBD')} - {event_info.get('end_time', 'TBD')}
- Event Location: {event_info.get('venue_name', 'TBD')}

Reservation Request:
- Party size: {party_size} people
- Preferred dining time: [Please suggest based on event schedule]
- Date: {event_info.get('date', 'TBD')}

We are attending the above event and would love to dine at your establishment. Could you please let me know if you have availability and what times would work best?

Please feel free to contact me at your earliest convenience to confirm the reservation details.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your Phone Number]
[Your Email Address]
"""
        return body
    
    def process_event_url(self, url: str, party_size: int = 4) -> Dict[str, any]:
        """
        Complete workflow: extract event info, find restaurants, and draft emails.
        
        Args:
            url: Event URL to process
            party_size: Number of people for restaurant booking
            
        Returns:
            Complete results including event info, restaurants, and draft emails
        """
        print(f"Processing event URL: {url}")
        
        # Step 1: Extract event information
        print("Extracting event information...")
        event_info = self.extract_event_info(url)
        
        if 'error' in event_info:
            return {"error": f"Failed to extract event info: {event_info['error']}"}
        
        # Step 2: Search for nearby restaurants
        print("Searching for nearby restaurants...")
        restaurants = self.search_restaurants(event_info)
        
        # Step 3: Draft booking emails
        print("Drafting booking emails...")
        draft_emails = []
        for restaurant in restaurants[:5]:  # Limit to top 5 restaurants
            email = self.draft_booking_email(event_info, restaurant, party_size)
            draft_emails.append({
                'restaurant': restaurant,
                'email': email
            })
        
        return {
            'event_info': event_info,
            'restaurants': restaurants,
            'draft_emails': draft_emails,
            'summary': {
                'event_title': event_info.get('title', 'Unknown Event'),
                'event_date': event_info.get('date', 'TBD'),
                'restaurants_found': len(restaurants),
                'emails_drafted': len(draft_emails)
            }
        } 