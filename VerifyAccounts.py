#!/usr/bin/env python3
"""
Email Verification Script for Chaos Cards
Processes EML files and automatically verifies email addresses by visiting verification links.
"""

import os
import re
import email
import time
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
import urllib.error

import chromedriver_autoinstaller
from seleniumbase import SB

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARNING  # Only show warnings and errors
)
log = logging.getLogger(__name__)

class EmailVerifier:
    def __init__(self, eml_folder="exported_emails", headless: bool = True):
        self.eml_folder = eml_folder
        self.headless = headless
        self.results = []
        
        # Install Chrome driver automatically
        try:
            chromedriver_autoinstaller.install()
        except urllib.error.URLError as e:
            log.error(f"Error with chromedriver auto-installation - {e}")
            raise
        
    def parse_eml_file(self, file_path):
        """Parse EML file and extract verification info"""
        try:
            with open(file_path, 'rb') as f:
                msg = email.message_from_bytes(f.read())
            
            # Extract email address from various headers
            email_address = None
            for header in ['To', 'Delivered-To', 'X-Apple-Action']:
                if msg.get(header):
                    # Extract email from header
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', msg.get(header))
                    if email_match:
                        potential_email = email_match.group(0)
                        # Prefer non-gmail addresses (the actual account emails)
                        if not potential_email.endswith('@gmail.com') or email_address is None:
                            email_address = potential_email
                        break
            
            # Get email content
            content = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    elif part.get_content_type() == "text/plain" and not content:
                        content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Extract verification link
            verification_link = None
            # Look for the specific pattern in the content
            link_pattern = r'https://www\.chaoscards\.co\.uk/account/verifyemail\?token=[^"&\s]+'
            match = re.search(link_pattern, content)
            if match:
                verification_link = match.group(0)
                # Clean up HTML entities
                verification_link = verification_link.replace('&amp;', '&')
            
            return {
                'file_name': os.path.basename(file_path),
                'email_address': email_address,
                'verification_link': verification_link,
                'content_preview': content[:200] if content else None
            }
            
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return None
    
    def verify_email(self, verification_link, email_address):
        """Visit verification link and check for success using SeleniumBase"""
        try:
            print(f"🔗 Visiting verification link for {email_address}")
            
            with SB(uc=True, headless=self.headless) as sb:
                
                # Visit the verification link
                sb.uc_open_with_reconnect(verification_link, reconnect_time=4)
                time.sleep(3)  # Wait for page to load
                
                # Get page content
                current_url = sb.get_current_url()
                page_title = sb.get_title()
                
                try:
                    page_text = sb.get_text("body").lower()
                except Exception:
                    page_text = ""
                
                # Check for success message - look for the specific div
                is_success = False
                success_message = "Success indicator not found"
                
                try:
                    # Look for the account verification div
                    if sb.is_element_present("div.account-verify"):
                        success_element = sb.find_element("div.account-verify")
                        success_message = success_element.text.strip()
                        is_success = True
                        print(f"✅ Found success div: {success_message}")
                    elif "thank you for verifying your email" in page_text:
                        is_success = True
                        success_message = "Thank you for verifying your email found in page text"
                    elif "email has been verified" in page_text:
                        is_success = True  
                        success_message = "Email verified message found"
                    elif "verification successful" in page_text:
                        is_success = True
                        success_message = "Verification successful message found"
                    else:
                        # Check if already verified
                        if "already verified" in page_text:
                            is_success = True
                            success_message = "Email already verified"
                        else:
                            success_message = f"No success indicators found. Page text preview: {page_text[:200]}"
                except Exception as e:
                    success_message = f"Error checking for success elements: {e}"
                
                # Check for error messages
                error_indicators = [
                    'invalid token',
                    'expired',
                    'error occurred',
                    'not found',
                    'token not found'
                ]
                
                has_error = any(error.lower() in page_text for error in error_indicators)
                
                if has_error:
                    is_success = False
                    success_message = f"Error detected in page content: {page_text[:200]}"
                
                return {
                    'success': is_success,
                    'final_url': current_url,
                    'success_message': success_message,
                    'page_title': page_title,
                    'response_preview': page_text[:300] if page_text else "Could not extract page text"
                }
                
        except Exception as e:
            print(f"❌ Error verifying {email_address}: {e}")
            return {
                'success': False,
                'error': str(e),
                'final_url': None
            }
    
    def process_all_emails(self):
        """Process all EML files in the folder"""
        if not os.path.exists(self.eml_folder):
            print(f"❌ Folder '{self.eml_folder}' not found!")
            return
        
        eml_files = [f for f in os.listdir(self.eml_folder) if f.endswith('.eml')]
        
        if not eml_files:
            print(f"❌ No EML files found in '{self.eml_folder}'!")
            return
        
        print(f"🔍 Found {len(eml_files)} EML files to process")
        print("=" * 60)
        
        verified_count = 0
        failed_count = 0
        
        for i, eml_file in enumerate(eml_files, 1):
            print(f"\n📧 Processing {i}/{len(eml_files)}: {eml_file}")
            
            file_path = os.path.join(self.eml_folder, eml_file)
            parsed_data = self.parse_eml_file(file_path)
            
            if not parsed_data:
                failed_count += 1
                continue
            
            if not parsed_data['email_address']:
                print(f"⚠️  Could not extract email address from {eml_file}")
                failed_count += 1
                continue
            
            if not parsed_data['verification_link']:
                print(f"⚠️  Could not extract verification link from {eml_file}")
                failed_count += 1
                continue
            
            print(f"📧 Email: {parsed_data['email_address']}")
            
            # Verify the email
            verification_result = self.verify_email(
                parsed_data['verification_link'], 
                parsed_data['email_address']
            )
            
            # Combine results
            result = {
                **parsed_data,
                **verification_result,
                'processed_at': datetime.now().isoformat(),
                'file_index': i
            }
            
            self.results.append(result)
            
            if verification_result.get('success'):
                print(f"✅ Successfully verified: {parsed_data['email_address']}")
                verified_count += 1
            else:
                print(f"❌ Failed to verify: {parsed_data['email_address']}")
                if 'error' in verification_result:
                    print(f"   Error: {verification_result['error']}")
                failed_count += 1
            
            # Small delay to be respectful to the server
            time.sleep(2)  # Increased delay for SeleniumBase
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 VERIFICATION SUMMARY")
        print(f"✅ Successfully verified: {verified_count}")
        print(f"❌ Failed to verify: {failed_count}")
        print(f"📁 Total processed: {len(eml_files)}")
        print(f"📈 Success rate: {(verified_count/len(eml_files)*100):.1f}%")
        
        # Print verified emails
        if verified_count > 0:
            print(f"\n✅ SUCCESSFULLY VERIFIED EMAILS:")
            for result in self.results:
                if result.get('success'):
                    print(f"   📧 {result.get('email_address', 'N/A')}")
        
        # Save detailed results
        self.save_results()
    
    def save_results(self):
        """Save detailed results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"verification_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Detailed results saved to: {results_file}")
            
            # Also create a summary CSV-like report
            summary_file = f"verification_summary_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("Email Address\tStatus\tFile Name\tVerification Link\n")
                for result in self.results:
                    status = "SUCCESS" if result.get('success') else "FAILED"
                    f.write(f"{result.get('email_address', 'N/A')}\t{status}\t{result.get('file_name', 'N/A')}\t{result.get('verification_link', 'N/A')}\n")
            
            print(f"📄 Summary report saved to: {summary_file}")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")

def main():
    """Main function to run the email verifier"""
    import sys
    
    print("🚀 Chaos Cards Email Verification Script")
    print("=" * 60)
    
    # Check for headless mode argument
    headless = True
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['--visible', '-v', '--debug']:
        headless = False
        print("🖥️ Running in VISIBLE mode for debugging")
    else:
        print("👻 Running in HEADLESS mode")
    
    verifier = EmailVerifier(headless=headless)
    verifier.process_all_emails()
    
    print("\n🎉 Email verification process completed!")

if __name__ == "__main__":
    main()
