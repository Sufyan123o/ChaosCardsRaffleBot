#!/usr/bin/env python3
"""
Chaos Cards Ac        # Capsolver configuration
        try:\n            from capsolver_config import CAPSOLVER_API_KEY, USE_CAPSOLVER\n            self.capsolver_api_key = CAPSOLVER_API_KEY\n            self.use_capsolver = USE_CAPSOLVER\n        except ImportError:\n            self.capsolver_api_key = \"YOUR_CAPSOLVER_API_KEY\"\n            self.use_capsolver = False\n            print(\"⚠️ capsolver_config.py not found - CAPTCHA solving disabled\")nt Generator
Automatically creates accounts using email addresses from CSV file
"""

import logging
import time
import urllib.error
from typing import List, Optional, Dict, Any
import secrets
import csv
import os
import random
import string
import requests

import chromedriver_autoinstaller
from seleniumbase import SB

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARNING  # Only show warnings and errors
)
log = logging.getLogger(__name__)


class ChaosCardsAccountGenerator:
    """Bot for automatically creating Chaos Cards accounts"""
    
    def __init__(self, account_info_list: List[Dict[str, str]], headless: bool = True):
        """
        Initialize the account generator
        
        Args:
            account_info_list: List of dictionaries with account info (name, email, address, city, postcode)
            headless: Whether to run browser in headless mode
        """
        self.account_info_list = account_info_list
        self.headless = headless
        
        # Capsolver configuration
        self.capsolver_api_key = "CAP-D2207C49885985C8FBCA86C5FFBC8D728FA2BC3DA753061B952F2A84C8B3AA2E"  # Replace with your actual API key
        self.use_capsolver = True  # Set to False to skip CAPTCHA solving
        
        # Chaos Cards specific Turnstile configuration
        self.chaos_cards_turnstile_key = "0x4AAAAAABggScS9EgpNO1pU"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3",
        ]
        
        # Sample data for generating fake accounts
        self.first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Charles", "Joseph", "Thomas",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
            "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua"
        ]
        
        self.last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
        ]
        
        self.uk_addresses = [
            {"add1": "123 High Street", "town": "London", "county": "Greater London", "postcode": "SW1A 1AA"},
            {"add1": "45 Church Lane", "town": "Manchester", "county": "Greater Manchester", "postcode": "M1 1AA"},
            {"add1": "78 Victoria Road", "town": "Birmingham", "county": "West Midlands", "postcode": "B1 1AA"},
            {"add1": "32 Queen Street", "town": "Liverpool", "county": "Merseyside", "postcode": "L1 1AA"},
            {"add1": "67 King's Road", "town": "Leeds", "county": "West Yorkshire", "postcode": "LS1 1AA"},
            {"add1": "89 Castle Street", "town": "Sheffield", "county": "South Yorkshire", "postcode": "S1 1AA"},
            {"add1": "54 Mill Lane", "town": "Bristol", "county": "Somerset", "postcode": "BS1 1AA"},
            {"add1": "21 Park Avenue", "town": "Newcastle", "county": "Tyne and Wear", "postcode": "NE1 1AA"},
            {"add1": "76 Oak Road", "town": "Cardiff", "county": "Cardiff", "postcode": "CF10 1AA"},
            {"add1": "43 Elm Street", "town": "Edinburgh", "county": "Edinburgh", "postcode": "EH1 1AA"}
        ]
        
        # Load proxies if available
        self.proxies = self.load_proxies_from_file("proxies.txt")
        self.current_proxy_index = 0
        
        # Install Chrome driver automatically
        try:
            chromedriver_autoinstaller.install()
        except urllib.error.URLError as e:
            log.error(f"Error with chromedriver auto-installation - {e}")
            raise

    def load_proxies_from_file(self, proxy_file: str = "proxies.txt") -> List[Dict[str, str]]:
        """
        Load proxies from text file in format ip:port:username:password
        
        Args:
            proxy_file: Path to proxy file
            
        Returns:
            List of proxy dictionaries
        """
        proxies = []
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            parts = line.split(':')
                            if len(parts) >= 4:
                                proxy = {
                                    'ip': parts[0],
                                    'port': parts[1],
                                    'username': parts[2],
                                    'password': parts[3],
                                    'proxy_string': f"{parts[0]}:{parts[1]}",
                                    'auth_string': f"{parts[2]}:{parts[3]}"
                                }
                                proxies.append(proxy)
                            else:
                                log.warning(f"Invalid proxy format on line {line_num}: {line}")
                        except Exception as e:
                            log.warning(f"Error parsing proxy on line {line_num}: {e}")
            
            if proxies:
                print(f"Loaded {len(proxies)} proxies from {proxy_file}")
            else:
                print(f"⚠️ {proxy_file} is empty - using local IP only")
        else:
            print(f"⚠️ Proxy file {proxy_file} not found - using local IP only")
        return proxies

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get the next proxy in rotation
        
        Returns:
            Proxy dictionary or None if no proxies available
        """
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def solve_turnstile_captcha(self, website_url: str, website_key: str) -> Optional[str]:
        """
        Solve Cloudflare Turnstile CAPTCHA using Capsolver
        
        Args:
            website_url: The URL where the CAPTCHA appears
            website_key: The Turnstile site key
            
        Returns:
            CAPTCHA token if successful, None if failed
        """
        if not self.use_capsolver or not self.capsolver_api_key or self.capsolver_api_key == "YOUR_CAPSOLVER_API_KEY":
            print("⚠️ Capsolver not configured - skipping CAPTCHA solving")
            return None
        
        try:
            print("🔄 Solving Turnstile CAPTCHA with Capsolver...")
            
            # Create task
            create_payload = {
                "clientKey": self.capsolver_api_key,
                "task": {
                    "type": "AntiTurnstileTaskProxyLess",
                    "websiteKey": website_key,
                    "websiteURL": website_url,
                    "metadata": {
                        "action": "register"  # Optional - indicates this is for registration
                    }
                }
            }
            
            response = requests.post("https://api.capsolver.com/createTask", json=create_payload, timeout=30)
            resp_data = response.json()
            
            task_id = resp_data.get("taskId")
            if not task_id:
                print(f"❌ Failed to create Capsolver task: {response.text}")
                return None
            
            print(f"✅ Created Capsolver task: {task_id}")
            
            # Poll for result
            max_attempts = 60  # Wait up to 60 seconds
            for attempt in range(max_attempts):
                time.sleep(2)  # Wait 2 seconds between checks
                
                result_payload = {
                    "clientKey": self.capsolver_api_key,
                    "taskId": task_id
                }
                
                result_response = requests.post("https://api.capsolver.com/getTaskResult", json=result_payload, timeout=10)
                result_data = result_response.json()
                
                status = result_data.get("status")
                
                if status == "ready":
                    token = result_data.get("solution", {}).get("token")
                    if token:
                        print("✅ CAPTCHA solved successfully!")
                        return token
                    else:
                        print("❌ No token in solution")
                        return None
                
                elif status == "failed" or result_data.get("errorId"):
                    print(f"❌ Capsolver task failed: {result_response.text}")
                    return None
                
                elif status == "processing":
                    print(f"⏳ Solving CAPTCHA... ({attempt + 1}/{max_attempts})")
                    continue
                
                else:
                    print(f"⏳ Task status: {status} ({attempt + 1}/{max_attempts})")
            
            print("⏰ CAPTCHA solving timeout")
            return None
            
        except Exception as e:
            print(f"❌ Error solving CAPTCHA: {e}")
            return None

    def inject_turnstile_token(self, sb, token: str) -> bool:
        """
        Inject the solved CAPTCHA token into the Turnstile field and trigger validation
        
        Args:
            sb: SeleniumBase driver instance
            token: The solved CAPTCHA token
            
        Returns:
            True if injection successful
        """
        try:
            print("🔧 Injecting CAPTCHA token and triggering validation...")
            
            # Wait for Turnstile widget to be fully loaded
            time.sleep(3)
            
            # Method 1: Find and set the hidden input field
            token_injected = False
            
            # Common Turnstile token field selectors
            token_selectors = [
                'input[name="cf-turnstile-response"]',
                'textarea[name="cf-turnstile-response"]',
                '#cf-turnstile-response',
                '[name*="turnstile"]',
                'input[data-callback]'
            ]
            
            for selector in token_selectors:
                try:
                    if sb.is_element_present(selector):
                        # Use JavaScript to set the value and trigger events
                        sb.execute_script(f"""
                            var element = document.querySelector('{selector}');
                            if (element) {{
                                element.value = '{token}';
                                
                                // Trigger input and change events
                                var inputEvent = new Event('input', {{ bubbles: true }});
                                var changeEvent = new Event('change', {{ bubbles: true }});
                                element.dispatchEvent(inputEvent);
                                element.dispatchEvent(changeEvent);
                                
                                console.log('Token set and events triggered on:', element.name);
                            }}
                        """)
                        token_injected = True
                        print(f"✅ Token injected into field: {selector}")
                        break
                except Exception as e:
                    print(f"⚠️ Failed to inject token into {selector}: {e}")
                    continue
            
            # Method 2: Alternative injection via JavaScript global search
            if not token_injected:
                try:
                    sb.execute_script(f"""
                        // Look for any hidden inputs that might be Turnstile related
                        var inputs = document.querySelectorAll('input[type="hidden"]');
                        var injected = false;
                        
                        for (var i = 0; i < inputs.length; i++) {{
                            var input = inputs[i];
                            if (input.name && (input.name.includes('turnstile') || 
                                             input.name.includes('cf-') || 
                                             input.name.includes('captcha'))) {{
                                input.value = '{token}';
                                
                                // Trigger events
                                var inputEvent = new Event('input', {{ bubbles: true }});
                                var changeEvent = new Event('change', {{ bubbles: true }});
                                input.dispatchEvent(inputEvent);
                                input.dispatchEvent(changeEvent);
                                
                                console.log('Token set on hidden field:', input.name);
                                injected = true;
                                break;
                            }}
                        }}
                        
                        return injected;
                    """)
                    token_injected = True
                    print("✅ Token injected via hidden field search")
                except Exception as e:
                    print(f"⚠️ Hidden field injection failed: {e}")
            
            # Method 3: Try to trigger Turnstile callback directly
            try:
                sb.execute_script(f"""
                    // Try to find and trigger Turnstile callback
                    if (window.turnstile && window.turnstile.render) {{
                        console.log('Turnstile API found');
                    }}
                    
                    // Look for Turnstile widgets
                    var widgets = document.querySelectorAll('.cf-turnstile, [data-sitekey]');
                    widgets.forEach(function(widget) {{
                        if (widget.dataset.callback) {{
                            var callbackName = widget.dataset.callback;
                            if (window[callbackName] && typeof window[callbackName] === 'function') {{
                                console.log('Triggering callback:', callbackName);
                                window[callbackName]('{token}');
                            }}
                        }}
                    }});
                    
                    // Set the token in any cf-turnstile-response fields
                    var responseFields = document.querySelectorAll('[name*="cf-turnstile"], [name*="turnstile"]');
                    responseFields.forEach(function(field) {{
                        field.value = '{token}';
                        console.log('Set token on field:', field.name);
                    }});
                """)
                print("✅ Triggered Turnstile callbacks and set response fields")
            except Exception as e:
                print(f"⚠️ Callback trigger failed: {e}")
            
            # Wait for validation to complete
            time.sleep(2)
            
            # Method 4: Check if token was accepted by looking for success indicators
            try:
                success_indicators = sb.execute_script("""
                    var indicators = [];
                    
                    // Check for Turnstile success state
                    var widgets = document.querySelectorAll('.cf-turnstile');
                    widgets.forEach(function(widget) {
                        var iframe = widget.querySelector('iframe');
                        if (iframe) {
                            indicators.push('iframe_found');
                        }
                    });
                    
                    // Check for filled response fields
                    var responseFields = document.querySelectorAll('[name*="cf-turnstile"], [name*="turnstile"]');
                    var filledFields = 0;
                    responseFields.forEach(function(field) {
                        if (field.value && field.value.length > 0) {
                            filledFields++;
                        }
                    });
                    
                    indicators.push('filled_fields_' + filledFields);
                    return indicators;
                """)
                print(f"🔍 CAPTCHA validation indicators: {success_indicators}")
            except Exception as e:
                print(f"⚠️ Could not check validation indicators: {e}")
            
            if token_injected:
                print("✅ CAPTCHA token injection completed")
                return True
            else:
                print("❌ Failed to inject CAPTCHA token")
                return False
                
        except Exception as e:
            print(f"❌ Error injecting CAPTCHA token: {e}")
            return False

    def generate_account_data(self, account_info: Dict[str, str]) -> Dict[str, str]:
        """
        Generate account data from CSV information
        
        Args:
            account_info: Dictionary with CSV data (name, email, address, city, postcode)
            
        Returns:
            Dictionary with account data formatted for registration
        """
        # Generate a random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Use a random county from our list since CSV doesn't have county
        random_county = random.choice([addr["county"] for addr in self.uk_addresses])
        
        return {
            "full_name": account_info["name"],
            "email": account_info["email"],
            "password": password,
            "address": {
                "add1": account_info["first_line_address"],
                "town": account_info["City"],
                "county": random_county,
                "postcode": account_info["PostalCode"]
            },
        }

    def create_accounts(self, delay_between_accounts: int = 3) -> Dict[str, Any]:
        """
        Create accounts for all provided account info
        
        Args:
            delay_between_accounts: Seconds to wait between account creations
            
        Returns:
            Dictionary with results summary
        """
        results = {
            "total_accounts": len(self.account_info_list),
            "successful_accounts": 0,
            "failed_accounts": 0,
            "errors": [],
            "created_accounts": []
        }
        
        log.info(f"Starting account creation for {len(self.account_info_list)} accounts")
        
        for i, account_info in enumerate(self.account_info_list, 1):
            email = account_info["email"]
            name = account_info["name"]
            print(f"Creating account {i}/{len(self.account_info_list)}: {name} ({email})")
            
            try:
                account_data = self.generate_account_data(account_info)
                success = self._create_single_account(account_data)
                
                if success:
                    results["successful_accounts"] += 1
                    results["created_accounts"].append({
                        "email": email,
                        "password": account_data["password"],
                        "full_name": account_data["full_name"],
                        "address": account_data["address"]
                    })
                    print("✅ Account created successfully")
                else:
                    results["failed_accounts"] += 1
                    print("❌ Account creation failed")
                    
            except Exception as e:
                results["failed_accounts"] += 1
                error_msg = f"Error creating account for {name} ({email}): {str(e)}"
                results["errors"].append(error_msg)
                log.error(error_msg)
                print("❌ Account creation failed with error")
            
            # Add delay between accounts
            if i < len(self.account_info_list):
                time.sleep(delay_between_accounts)
        
        return results

    def _create_single_account(self, account_data: Dict[str, str]) -> bool:
        """
        Create a single account
        
        Args:
            account_data: Dictionary with account information
            
        Returns:
            True if successful, False otherwise
        """
        user_agent = secrets.choice(self.user_agents)
        proxy = self.get_next_proxy()
        
        # Configure SeleniumBase with or without proxy
        sb_kwargs = {
            'uc': True,
            'headless': self.headless,
            'agent': user_agent
        }
        
        if proxy:
            # Configure proxy settings
            sb_kwargs['proxy'] = f"{proxy['username']}:{proxy['password']}@{proxy['ip']}:{proxy['port']}"
            print(f"Using proxy: {proxy['ip']}:{proxy['port']} (GB)")
        else:
            print("🌐 Using local IP - no proxies available")
        
        with SB(**sb_kwargs) as sb:
            try:
                # Navigate to the registration page
                sb.uc_open_with_reconnect("https://www.chaoscards.co.uk/account/register", reconnect_time=4)
                
                # Wait for page to load completely
                sb.wait_for_ready_state_complete()
                time.sleep(3)
                
                # Fill in the registration form
                if not self._fill_registration_form(sb, account_data):
                    return False
                
                # Submit the form
                if not self._submit_registration_form(sb):
                    return False
                
                # Check if registration was successful
                return self._check_registration_success(sb)
                
            except Exception as e:
                log.error(f"Error in _create_single_account: {e}")
                return False

    def _fill_registration_form(self, sb, account_data: Dict[str, str]) -> bool:
        """
        Fill in the registration form fields
        
        Args:
            sb: SeleniumBase driver instance
            account_data: Dictionary with account data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Wait for form to be ready
            sb.wait_for_element_visible("#registration_form_full_name", timeout=10)
            
            # Fill personal details
            sb.clear("#registration_form_full_name")
            sb.type("#registration_form_full_name", account_data["full_name"])
            
            sb.clear("#registration_form_email")
            sb.type("#registration_form_email", account_data["email"])
            
            sb.clear("#registration_form_pwd")
            sb.type("#registration_form_pwd", account_data["password"])
            
            sb.clear("#registration_form_confirm_password")
            sb.type("#registration_form_confirm_password", account_data["password"])
            
            # Fill address details
            address = account_data["address"]
            
            sb.clear("#registration_form_add1")
            sb.type("#registration_form_add1", address["add1"])
            
            sb.clear("#registration_form_towncity")
            sb.type("#registration_form_towncity", address["town"])
            
            sb.clear("#registration_form_county")
            sb.type("#registration_form_county", address["county"])
            
            # Country should already be set to UK (value="221")
            # But let's make sure
            sb.select_option_by_value("#registration_form_country", "221")
            
            sb.clear("#registration_form_pcode")
            sb.type("#registration_form_pcode", address["postcode"])
            
            # Wait a moment for all fields to be filled
            time.sleep(2)
            
            # Handle Cloudflare Turnstile CAPTCHA if present
            if self._handle_turnstile_captcha(sb):
                print("✅ CAPTCHA handling completed")
            else:
                print("⚠️ CAPTCHA handling failed or not needed")
            
            return True
            
        except Exception as e:
            log.error(f"Error filling registration form: {e}")
            return False

    def _handle_turnstile_captcha(self, sb) -> bool:
        """
        Detect and handle Cloudflare Turnstile CAPTCHA
        
        Args:
            sb: SeleniumBase driver instance
            
        Returns:
            True if CAPTCHA was handled (or not present), False if failed
        """
        try:
            current_url = sb.get_current_url()
            
            # Wait for page to fully load and any CAPTCHAs to appear
            print("⏳ Waiting for CAPTCHA widget to load...")
            time.sleep(5)
            
            # Check if Turnstile widget is present
            turnstile_present = False
            turnstile_selectors = [
                '.cf-turnstile',
                '[data-sitekey]',
                'iframe[src*="turnstile"]',
                'div[id*="turnstile"]'
            ]
            
            for selector in turnstile_selectors:
                if sb.is_element_present(selector):
                    turnstile_present = True
                    print(f"🔍 Found Turnstile widget: {selector}")
                    break
            
            if not turnstile_present:
                # Check page source for Turnstile references
                page_source = sb.get_page_source()
                if "turnstile" in page_source.lower() or "0x4AAAAAABggScS9EgpNO1pU" in page_source:
                    turnstile_present = True
                    print("🔍 Turnstile detected in page source")
            
            if turnstile_present:
                # If we're on Chaos Cards, use the known key
                if "chaoscards.co.uk" in current_url:
                    print(f"🎯 Using known Chaos Cards Turnstile key: {self.chaos_cards_turnstile_key}")
                    
                    # Wait a bit more for the CAPTCHA to be ready
                    print("⏳ Waiting for CAPTCHA to be ready for solving...")
                    time.sleep(3)
                    
                    token = self.solve_turnstile_captcha(current_url, self.chaos_cards_turnstile_key)
                    if token:
                        # Wait before injecting to ensure the form is ready
                        time.sleep(2)
                        success = self.inject_turnstile_token(sb, token)
                        
                        if success:
                            # Give extra time for validation
                            print("⏳ Waiting for CAPTCHA validation to complete...")
                            time.sleep(5)
                            return True
                        else:
                            print("❌ Failed to inject CAPTCHA token")
                            return False
                    else:
                        print("❌ Failed to solve CAPTCHA with known key")
                        return False
                else:
                    print("ℹ️ Not on Chaos Cards - trying auto-detection")
                    return True  # Skip CAPTCHA for other sites
            else:
                print("ℹ️ No Turnstile CAPTCHA detected")
                return True  # No CAPTCHA found is considered success
                
        except Exception as e:
            print(f"❌ Error handling CAPTCHA: {e}")
            return False

    def _submit_registration_form(self, sb) -> bool:
        """
        Submit the registration form
        
        Args:
            sb: SeleniumBase driver instance
            
        Returns:
            True if submission successful, False otherwise
        """
        try:
            # Wait for any CAPTCHA to load (Cloudflare Turnstile)
            time.sleep(3)
            
            # Look for the submit button
            submit_selectors = [
                "#registration_form_submit",
                'a[href="#form-submit-registration_form"]',
                '.submit_button[title="Register"]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if sb.is_element_visible(selector):
                        submit_button = selector
                        break
                except Exception:
                    continue
            
            if not submit_button:
                log.error("Could not find registration submit button")
                return False
            
            # Ensure button is clickable
            sb.wait_for_element_clickable(submit_button, timeout=10)
            
            # Click the submit button
            sb.click(submit_button)
            
            # Wait for submission to process
            time.sleep(5)
            
            return True
            
        except Exception as e:
            log.error(f"Error submitting registration form: {e}")
            return False

    def _check_registration_success(self, sb) -> bool:
        """
        Check if registration was successful by looking for account dashboard
        
        Args:
            sb: SeleniumBase driver instance
            
        Returns:
            True if registration appears successful
        """
        # Wait for page to process and redirect
        time.sleep(5)
        
        try:
            current_url = sb.get_current_url()
            page_title = sb.get_title()
            
            print(f"🔍 Current URL: {current_url}")
            print(f"🔍 Page title: {page_title}")
            
            # Primary success indicators
            success_indicators = [
                "/account/dashboard" in current_url,
                "Account Overview" in page_title,
                "dashboard" in current_url.lower()
            ]
            
            # Check if any primary indicator is present
            if any(success_indicators):
                print("✅ SUCCESS: Redirected to account dashboard!")
                
                # Additional verification - look for logged-in elements
                try:
                    logged_in_elements = [
                        '.header-account--logged-in',
                        '.header-account__name',
                        '[href="/account/dashboard"]'
                    ]
                    
                    for element in logged_in_elements:
                        if sb.is_element_present(element):
                            print(f"✅ Found logged-in indicator: {element}")
                            break
                    
                    # Look for user greeting
                    page_text = sb.get_text("body")
                    if "Hi " in page_text and ("Account" in page_text or "Dashboard" in page_text):
                        print("✅ Found user greeting - definitely logged in!")
                        return True
                        
                except Exception as e:
                    print(f"⚠️ Could not verify logged-in elements: {e}")
                
                return True
            
            # Check for error indicators
            error_indicators = [
                "register" in current_url.lower(),
                "error" in page_title.lower(),
                "invalid" in page_title.lower()
            ]
            
            if any(error_indicators):
                print(f"❌ FAILED: Still on registration page or error page")
                
                # Look for specific error messages
                try:
                    page_text = sb.get_text("body").lower()
                    
                    error_messages = [
                        "invalid captcha",
                        "email already exists", 
                        "already registered",
                        "please try again",
                        "cloudflare",
                        "verification failed"
                    ]
                    
                    for error_msg in error_messages:
                        if error_msg in page_text:
                            print(f"❌ Found error: {error_msg}")
                            break
                            
                except Exception:
                    pass
                
                return False
            
            # Ambiguous result - check page content more thoroughly
            try:
                page_text = sb.get_text("body").lower()
                
                # Look for positive keywords
                positive_keywords = ["welcome", "dashboard", "account overview", "successfully"]
                negative_keywords = ["register", "sign up", "create account", "captcha", "error"]
                
                positive_score = sum(1 for word in positive_keywords if word in page_text)
                negative_score = sum(1 for word in negative_keywords if word in page_text)
                
                print(f"📊 Content analysis - Positive: {positive_score}, Negative: {negative_score}")
                
                if positive_score > negative_score:
                    print("✅ Content suggests success")
                    return True
                else:
                    print("❌ Content suggests failure")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Could not analyze page content: {e}")
                
            # Default to failure if we can't determine
            print("❌ UNKNOWN: Could not determine registration status - assuming failure")
            return False
            
        except Exception as e:
            print(f"❌ Error checking registration success: {e}")
            return False


def read_emails_from_csv(csv_file: str = "iclouds.csv") -> List[str]:
    """
    Read email addresses from a CSV file
    
    Args:
        csv_file: Path to the CSV file containing emails
        
    Returns:
        List of email addresses
    """
    emails = []
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found. Please create the file with email addresses.")
        print("Format: One email per line or comma-separated emails.")
        return []
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as file:
            # Try to detect if it's a proper CSV or just line-separated
            content = file.read().strip()
            file.seek(0)
            
            if ',' in content:
                # Treat as CSV
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    for email in row:
                        email = email.strip()
                        if email and '@' in email:  # Basic email validation
                            emails.append(email)
            else:
                # Treat as line-separated
                for line in file:
                    email = line.strip()
                    if email and '@' in email:  # Basic email validation
                        emails.append(email)
    
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        return []
    
    if not emails:
        print(f"No valid emails found in {csv_file}")
    else:
        print(f"Loaded {len(emails)} emails from {csv_file}")
    
    return emails


def main():
    """Main function to analyze the registration page"""
    
    print("=== Chaos Cards Account Generator - Page Analysis ===")
    
    # Read a few emails from CSV for testing (we don't need all for analysis)
    email_list = read_emails_from_csv("iclouds.csv")
    if email_list:
        email_list = email_list[:5]  # Just use first 5 for analysis
    
    # Create generator instance
    generator = ChaosCardsAccountGenerator(
        emails=email_list,
        headless=True  # Keep visible for analysis
    )
    
    try:
        # Gather page information
        generator.gather_page_info()
        print("\n=== Analysis Complete ===")
        print("Check the following files for detailed analysis:")
        print("- chaos_cards_register_page.png (screenshot)")
        print("- chaos_cards_register_source.html (page source)")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()