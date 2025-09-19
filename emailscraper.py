from __future__ import print_function
import base64
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    """Exports emails with a specific subject within a date range as .eml files."""
    creds = None
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ Error: credentials.json file not found!")
        print("\n📋 To fix this issue:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API (APIs & Services → Library → Gmail API → Enable)")
        print("4. Create credentials (APIs & Services → Credentials → Create Credentials → OAuth client ID)")
        print("5. Choose 'Desktop application' as application type")
        print("6. Download the credentials file and save it as 'credentials.json' in this directory")
        print("\n📁 Make sure 'credentials.json' is in the same folder as this script.")
        return
    
    # Load saved credentials if available
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # Otherwise run login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Gmail query: subject and date range
    query = 'subject:"Please verify your email" after:2025/09/17 before:2025/09/20'

    print(f"🔍 Searching for emails with query: {query}")
    
    # Get ALL messages by handling pagination
    all_messages = []
    page_token = None
    page_count = 0
    
    while True:
        page_count += 1
        print(f"📄 Fetching page {page_count}...")
        
        # Request with pagination
        results = service.users().messages().list(
            userId='me', 
            q=query, 
            pageToken=page_token,
            maxResults=500  # Maximum allowed per page
        ).execute()
        
        messages = results.get('messages', [])
        all_messages.extend(messages)
        
        print(f"📬 Found {len(messages)} emails on page {page_count} (Total so far: {len(all_messages)})")
        
        # Check if there are more pages
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    
    print(f"✅ Total emails found: {len(all_messages)}")
    
    if not all_messages:
        print("No messages found.")
        return

    if not os.path.exists("exported_emails"):
        os.makedirs("exported_emails")

    print(f"💾 Downloading and saving {len(all_messages)} emails...")
    
    for i, msg in enumerate(all_messages, 1):
        msg_id = msg['id']
        print(f"📥 Downloading email {i}/{len(all_messages)} (ID: {msg_id})")
        
        raw_msg = service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
        raw_data = raw_msg['raw']

        # Decode base64url
        eml_data = base64.urlsafe_b64decode(raw_data.encode('UTF-8'))

        # Save as .eml
        filename = f"exported_emails/{msg_id}.eml"
        with open(filename, 'wb') as f:
            f.write(eml_data)
        
        # Progress indicator every 50 emails
        if i % 50 == 0 or i == len(all_messages):
            print(f"✅ Saved {i}/{len(all_messages)} emails")
    
    print(f"🎉 All {len(all_messages)} emails saved to 'exported_emails' folder!")

if __name__ == '__main__':
    main()
