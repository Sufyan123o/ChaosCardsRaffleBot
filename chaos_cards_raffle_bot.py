#!/usr/bin/env python3
"""
Chaos Cards Raffle Bot Template
Automatically fills out "Notify me" forms with multiple email addresses
"""

import logging
import time
import urllib.error
from typing import List, Optional
import secrets
import csv
import os

import chromedriver_autoinstaller
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARNING  # Only show warnings and errors
)
log = logging.getLogger(__name__)


class ChaosCardsRaffleBot:
    """Bot for automatically entering Chaos Cards raffles with multiple emails"""
    
    def __init__(self, emails: List[str], headless: bool = False):
        """
        Initialize the raffle bot
        
        Args:
            emails: List of email addresses to use for entries
            headless: Whether to run browser in headless mode
        """
        self.emails = emails
        self.headless = headless
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3",
        ]
        
        # Install Chrome driver automatically
        try:
            chromedriver_autoinstaller.install()
        except urllib.error.URLError as e:
            log.error(f"Error with chromedriver auto-installation - {e}")
            raise

    def enter_raffle(self, url: str, delay_between_entries: int = 2) -> dict:
        """
        Enter raffle for a specific product URL with all provided emails
        
        Args:
            url: Product URL to enter raffle for
            delay_between_entries: Seconds to wait between email entries
            
        Returns:
            Dictionary with results summary
        """
        # Start from the first email (index 0)
        start_index = 0
        emails_to_process = self.emails[start_index:]
        
        results = {
            "url": url,
            "total_emails": len(emails_to_process),
            "successful_entries": 0,
            "failed_entries": 0,
            "errors": [],
            "starting_at_email": start_index + 1
        }
        
        log.info(f"Starting raffle entries for: {url}")
        print(f"🚀 Starting from email {start_index + 1} out of {len(self.emails)} total emails")
        
        for i, email in enumerate(emails_to_process, start_index + 1):
            print(f"Processing email {i}/{len(self.emails)}: {email}")
            try:
                success = self._enter_single_email(url, email)
                if success:
                    results["successful_entries"] += 1
                else:
                    results["failed_entries"] += 1
                    
            except Exception as e:
                results["failed_entries"] += 1
                error_msg = f"Error entering {email}: {str(e)}"
                results["errors"].append(error_msg)
                log.error(error_msg)
            
            # Add delay between entries to avoid being flagged
            if i < len(self.emails):
                time.sleep(delay_between_entries)
        
        return results

    def _enter_single_email(self, url: str, email: str) -> bool:
        """
        Enter a single email address for the raffle
        
        Args:
            url: Product URL
            email: Email address to enter
            
        Returns:
            True if successful, False otherwise
        """
        # Get random user agent for this session
        user_agent = secrets.choice(self.user_agents)
        
        with SB(uc=True, headless=self.headless, agent=user_agent) as sb:
            try:
                # Navigate to the product page
                sb.uc_open_with_reconnect(url, reconnect_time=4)
                
                # Wait for Cloudflare and page to load completely
                self._wait_for_page_ready(sb)
                
                # Look for the email input field with retries
                email_field = self._find_email_field_with_wait(sb)
                if not email_field:
                    log.error("Could not find email input field")
                    print(f"Current page title: {sb.get_title()}")
                    print(f"Current URL: {sb.get_current_url()}")
                    return False
                
                # Wait for the field to be interactive
                sb.wait_for_element_visible(email_field, timeout=15)
                
                # Clear any existing text and enter the email
                sb.clear(email_field)
                sb.type(email_field, email)
                
                # Small delay before clicking submit
                time.sleep(1)
                
                # Find and click the submit button
                submit_button = self._find_submit_button_with_wait(sb)
                if not submit_button:
                    log.error("Could not find submit button")
                    return False
                
                # Ensure button is clickable
                sb.wait_for_element_clickable(submit_button, timeout=15)
                
                # Click the submit button
                sb.click(submit_button)
                
                # Wait for the submission to process and check result
                time.sleep(3)
                
                # Check if submission was successful or if email already registered
                submission_result = self._check_submission_success(sb)
                
                if submission_result == "already_registered":
                    print(f"⚠️ Email {email} is already registered for this product - skipping")
                    return True  # Consider this as success since email is already in the system
                elif submission_result == True:
                    print(f"✅ Successfully submitted {email}")
                    return True
                else:
                    print(f"❌ Failed to submit {email}")
                    return False
                
            except Exception as e:
                log.error(f"Error in _enter_single_email: {e}")
                return False

    def _wait_for_page_ready(self, sb, max_wait_time: int = 60):
        """
        Wait for page to be ready, handling Cloudflare and other loading states
        
        Args:
            sb: SeleniumBase driver instance
            max_wait_time: Maximum time to wait in seconds
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Wait for basic ready state
                sb.wait_for_ready_state_complete(timeout=5)
                
                # Check if we're on Cloudflare page
                page_text = sb.get_text("body").lower()
                
                if "cloudflare" in page_text or "checking your browser" in page_text:
                    print("🔄 Cloudflare detected, waiting...")
                    time.sleep(5)
                    continue
                
                # Check if the main product content is loaded
                if sb.is_element_present(".product__title") or sb.is_element_present("#prod_title"):
                    print("✅ Product page loaded successfully")
                    time.sleep(3)  # Extra time for any dynamic content
                    return
                
                # If no specific indicators, wait a bit more
                time.sleep(2)
                
            except Exception as e:
                print(f"⚠️ Waiting for page ready: {e}")
                time.sleep(3)
        
        print("⚠️ Maximum wait time reached, proceeding anyway")

    def _find_email_field_with_wait(self, sb, max_retries: int = 5) -> Optional[str]:
        """
        Find the email input field with retries and better waiting
        
        Args:
            sb: SeleniumBase driver instance
            max_retries: Maximum number of retry attempts
            
        Returns:
            Selector string if found, None otherwise
        """
        for attempt in range(max_retries):
            email_field = self._find_email_field(sb)
            if email_field:
                return email_field
            
            print(f"🔄 Email field not found, attempt {attempt + 1}/{max_retries}")
            
            # Wait for any dynamic content to load
            time.sleep(3)
            
            # Try scrolling down in case the form is below the fold
            if attempt > 1:
                try:
                    sb.scroll_to_bottom()
                    time.sleep(2)
                except Exception:
                    pass
        
        return None

    def _find_submit_button_with_wait(self, sb, max_retries: int = 5) -> Optional[str]:
        """
        Find the submit button with retries and better waiting
        
        Args:
            sb: SeleniumBase driver instance
            max_retries: Maximum number of retry attempts
            
        Returns:
            Selector string if found, None otherwise
        """
        for attempt in range(max_retries):
            submit_button = self._find_submit_button(sb)
            if submit_button:
                return submit_button
            
            print(f"🔄 Submit button not found, attempt {attempt + 1}/{max_retries}")
            
            # Wait for any dynamic content to load
            time.sleep(2)
            
            # Try scrolling to find the button
            if attempt > 1:
                try:
                    sb.scroll_to_bottom()
                    time.sleep(1)
                except Exception:
                    pass
        
        return None

    def _find_email_field(self, sb) -> Optional[str]:
        """
        Find the email input field using various selectors
        
        Args:
            sb: SeleniumBase driver instance
            
        Returns:
            Selector string if found, None otherwise
        """
        # Try different selectors based on the provided HTML structure
        selectors_to_try = [
            'input[name="email"]',
            'input[type="email"]',
            'input[placeholder*="email"]',
            'input[id*="email"]',
            'input.field_email',
            'input[id*="oos_notification"][name="email"]',  # More specific pattern
            '[id*="email_field"] input',  # Target input within email field container
        ]
        
        for selector in selectors_to_try:
            try:
                if sb.is_element_visible(selector):
                    return selector
            except Exception:
                continue
        
        # Try a more general approach - look for any visible email input
        try:
            email_inputs = sb.find_elements('input[type="email"]')
            for input_elem in email_inputs:
                if input_elem.is_displayed():
                    input_id = input_elem.get_attribute('id')
                    if input_id:
                        return f'#{input_id}'
        except Exception:
            pass
        
        return None

    def _find_submit_button(self, sb) -> Optional[str]:
        """
        Find the submit button using various selectors
        
        Args:
            sb: SeleniumBase driver instance
            
        Returns:
            Selector string if found, None otherwise
        """
        # Try specific selectors for the OOS notification form first
        specific_selectors = [
            '#oos_notification_381994_submit',  # Try the exact ID first
            '[id*="oos_notification"][id*="submit"]',  # Pattern matching for OOS notification buttons
            'a[href="#oos-form-submit"]',  # Exact href match
            '.oos_notification .submit_button',  # Submit button within OOS notification div
            '.form_submit a.submit_button',  # Submit button within form_submit class
            '.form_submit a[rel="next"]',  # Link with rel="next" within form_submit
            'fieldset a[rel="next"]',  # Button with rel="next" within fieldset
        ]
        
        # First, wait a moment for any dynamic content to load
        time.sleep(1)
        
        for selector in specific_selectors:
            try:
                # Wait for element to be present and visible
                sb.wait_for_element_present(selector, timeout=5)
                if sb.is_element_visible(selector):
                    # Verify this is actually a "Notify me" button
                    try:
                        button_text = sb.get_text(selector).strip().lower()
                        if "notify" in button_text or selector.startswith('#oos_notification') or selector.startswith('[id*="oos_notification"]'):
                            return selector
                    except Exception:
                        # If we can't get text but selector matches OOS pattern, use it
                        if "oos_notification" in selector or 'href="#oos-form-submit"' in selector:
                            return selector
            except Exception:
                continue
        
        # Try more general selectors but validate they contain "Notify me"
        general_selectors = [
            'a.submit_button',
            '[class*="submit"]',
            'a[id*="submit"]',
            'button[type="submit"]',
            'input[type="submit"]',
        ]
        
        for selector in general_selectors:
            try:
                if sb.is_element_visible(selector):
                    button_text = sb.get_text(selector).strip().lower()
                    if "notify" in button_text and "me" in button_text:
                        return selector
            except Exception:
                continue
        
        # Search for elements with 'oos_notification' in their ID
        try:
            all_oos_elements = sb.find_elements('[id*="oos_notification"]')
            for element in all_oos_elements:
                try:
                    if element.is_displayed():
                        element_id = element.get_attribute('id')
                        element_tag = element.tag_name
                        if element_tag == 'a' and element_id and 'submit' in element_id:
                            return f'#{element_id}'
                except Exception:
                    continue
        except Exception:
            pass
        
        # Find all links and check their text
        try:
            all_links = sb.find_elements('a')
            for link in all_links:
                try:
                    if link.is_displayed():
                        text = link.text.strip().lower()
                        link_id = link.get_attribute('id')
                        if "notify me" in text and link_id:
                            return f'#{link_id}'
                except Exception:
                    continue
        except Exception:
            pass
        
        return None

    def _check_submission_success(self, sb):
        """
        Check if the form submission was successful
        
        Args:
            sb: SeleniumBase driver instance
            
        Returns:
            True if successful, "already_registered" if email already exists, False if failed
        """
        # Wait a moment for any page changes
        time.sleep(2)
        
        # First check for "already registered" error
        try:
            # Look for the specific error message in the field
            error_field_selectors = [
                '.field_email.error',
                '[class*="error"]',
                '.required.error',
                '[data-error-message*="already registered"]'
            ]
            
            for selector in error_field_selectors:
                if sb.is_element_present(selector):
                    try:
                        error_element = sb.find_element(selector)
                        error_message = error_element.get_attribute('data-error-message')
                        if error_message and "already registered" in error_message.lower():
                            return "already_registered"
                    except Exception:
                        continue
            
            # Also check page text for already registered messages
            page_text = sb.get_text("body").lower()
            already_registered_indicators = [
                "already registered",
                "already subscribed",
                "already signed up",
                "email address is already registered",
                "already in our system"
            ]
            
            for indicator in already_registered_indicators:
                if indicator in page_text:
                    return "already_registered"
                    
        except Exception as e:
            print(f"Error checking for already registered: {e}")
        
        # Look for success indicators in page text
        success_indicators = [
            "successfully",
            "thank you",
            "notification added",
            "you will be notified",
            "added to waitlist",
            "email added",
            "subscribed",
            "signed up",
            "your details have been saved"
        ]
        
        try:
            page_text = sb.get_text("body").lower()
            for indicator in success_indicators:
                if indicator in page_text:
                    # Check for the specific success message
                    if "your details have been saved and you will be notified if you are the winner" in page_text:
                        print("✅ Success: Entry confirmed - you will be notified if you are the winner")
                    return True
        except Exception:
            pass
        
        # Check for other error messages that might indicate failure
        error_indicators = [
            "error occurred",
            "invalid email",
            "submission failed",
            "please try again"
        ]
        
        try:
            page_text = sb.get_text("body").lower()
            for indicator in error_indicators:
                if indicator in page_text:
                    return False
        except Exception:
            pass
        
        # Check if the form is still visible with the same email (might indicate failure)
        try:
            email_field = self._find_email_field(sb)
            if email_field and sb.is_element_visible(email_field):
                current_value = sb.get_value(email_field)
                if not current_value:  # Field was cleared, might indicate success
                    return True
        except Exception:
            pass
        
        # If we can't determine success/failure clearly, assume success
        return True

    def enter_multiple_raffles(self, urls: List[str], delay_between_urls: int = 5) -> List[dict]:
        """
        Enter raffles for multiple product URLs
        
        Args:
            urls: List of product URLs to enter
            delay_between_urls: Seconds to wait between different URLs
            
        Returns:
            List of result dictionaries for each URL
        """
        all_results = []
        
        for i, url in enumerate(urls, 1):
            results = self.enter_raffle(url)
            all_results.append(results)
            
            # Add delay between different URLs
            if i < len(urls):
                time.sleep(delay_between_urls)
        
        return all_results


def read_emails_from_csv(csv_file: str = "accountgen.csv") -> List[str]:
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
    """Example usage of the Chaos Cards Raffle Bot"""
    
    # Read emails from CSV file
    EMAIL_LIST = read_emails_from_csv("accountgen.csv")
    
    if not EMAIL_LIST:
        print("No emails to process. Exiting.")
        return
    
    # Example URLs (replace with actual product URLs)
    RAFFLE_URLS = [
        "https://www.chaoscards.co.uk/prod/other-pokemon/pokemon-mega-charizard-x-ex-ultra-premium-collection",
        # Add more URLs here
    ]
    
    # Create bot instance
    bot = ChaosCardsRaffleBot(
        emails=EMAIL_LIST,
        headless=True  # Set to True for headless mode
    )
    
    try:
        # Enter raffle for single or multiple URLs
        if len(RAFFLE_URLS) == 1:
            results = bot.enter_raffle(RAFFLE_URLS[0])
            print(f"Raffle completed: {results['successful_entries']}/{results['total_emails']} successful entries")
            if results['errors']:
                print(f"Errors encountered: {len(results['errors'])}")
        else:
            all_results = bot.enter_multiple_raffles(RAFFLE_URLS)
            total_success = sum(r['successful_entries'] for r in all_results)
            total_attempts = sum(r['total_emails'] for r in all_results)
            print(f"All raffles completed: {total_success}/{total_attempts} successful entries across {len(RAFFLE_URLS)} URLs")
    
    except Exception as e:
        print(f"Error running raffle bot: {e}")
        raise


if __name__ == "__main__":
    main()