# Chaos Cards Raffle Bot 

<p style="font-size: 24px;">A comprehensive toolkit to mass create mass entries for Chaos Cards raffles. This includes account creation, account verification, and raffle entries.</p>


## 📁 Project Overview

This project contains several Python scripts for automating various tasks related to Chaos Cards:

- **Account Generation** - Create multiple Chaos Cards accounts automatically
- **Email Verification** - Verify the accounts by scraping your gmail and visiting verification links
- **Raffle Bot** - Automatically enter raffles with multiple email addresses

## 🔧 Files Description

### Core Scripts

#### `chaos_cards_account_generator.py`
**Purpose**: Automatically generates Chaos Cards accounts using details in CSV.

**Features**:
- Mass account creation with random user data
- Cloudflare solving using Capsolver integration
- Proxy support for IP rotation
- Handles Cloudflare protection
- Utilises user-made profiles

**Usage**:
```bash
python chaos_cards_account_generator.py
```

#### `chaos_cards_raffle_bot.py`
**Purpose**: Automatically enters Chaos Cards raffles/notifications with multiple email addresses. To increase chances of winning.

**Features**:
- Processes emails from CSV file starting at a specified position
- Detects and skips already registered emails
- Handles Cloudflare protection and page loading
- Headless browser operation for stealth
- Smart element detection with retries

**Usage**:
```bash
python chaos_cards_raffle_bot.py
```

#### `emailscraper.py`
**Purpose**: Downloads verification emails from Gmail using Gmail API.

**Features**:
- Gmail API integration with OAuth2
- Downloads emails matching specific criteria
- Exports emails as .eml files
- Pagination support for large email volumes
- Searches for "Please verify your email" subject

**Usage**:
```bash
python emailscraper.py
```

#### `VerifyAccounts.py`
**Purpose**: Automatically verifies email addresses by visiting verification links in emails scraped using Google API.

**Features**:
- Processes all .eml files from email scraper
- Extracts verification links automatically
- Uses SeleniumBase with undetected Chrome driver.
- Detects success/failure of verification
- Comprehensive reporting and logging

**Usage**:
```bash
# Run in headless mode
python VerifyAccounts.py

# Run with visible browser for debugging
python VerifyAccounts.py --visible
```

#### `run_account_generator.py`
**Purpose**: Simplified runner script for the account generator.

### Supporting Files

#### `accountgen.csv`
**Purpose**: Contains email addresses and account information for automation.

**Required Format**:
```csv
email,password,firstname,lastname,address1,city,postcode
john.doe@example.com,password123,John,Doe,123 Main St,London,SW1A 1AA
jane.smith@example.com,password456,Jane,Smith,456 Oak Rd,Manchester,M1 1BB
```

**Field Descriptions**:
- `email`: Email address for the account
- `password`: Password for the account
- `firstname`: First name
- `lastname`: Last name  
- `address1`: Street address
- `city`: City name
- `postcode`: UK postcode

#### `proxies.txt`
**Purpose**: Contains proxy servers for IP rotation during account creation.

**Required Format**:
```
ip:port:username:password
192.168.1.1:8080:user1:pass1
10.0.0.1:3128:user2:pass2
```

#### `credentials.json`
**Purpose**: Google OAuth2 credentials for Gmail API access.

**How to Obtain**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop Application)
5. Download as `credentials.json`

#### `token.json`
**Purpose**: Automatically generated OAuth2 token file (created after first Gmail authentication).

## 📊 Data Files

### `exported_emails/` Directory
Contains .eml files downloaded by the email scraper. Each file represents one verification email.

### Result Files
The scripts generate various result files:
- `verification_results_YYYYMMDD_HHMMSS.json` - Detailed verification results
- `verification_summary_YYYYMMDD_HHMMSS.txt` - Summary report

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install seleniumbase requests beautifulsoup4 google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Setup Gmail API (for email scraper)
1. Create Google Cloud project
2. Enable Gmail API
3. Create Desktop Application OAuth2 credentials
4. Download and save as `credentials.json`

### 3. Prepare CSV Files
Create `accountgen.csv` with the format shown above.

### 4. Optional: Setup Proxies
Create `proxies.txt` with proxy information if needed.

### 5. Optional: Setup Capsolver (for CAPTCHA solving)
1. Get API key from Capsolver
2. Update `capsolver_api_key` in account generator script

## 🔄 Typical Workflow

1. **Create Accounts**: Run `chaos_cards_account_generator.py` to create accounts
2. **Download Emails**: Run `emailscraper.py` to download verification emails
3. **Verify Emails**: Run `VerifyAccounts.py` to automatically verify emails
4. **Enter Raffles**: Run `chaos_cards_raffle_bot.py` to participate in raffles

## ⚙️ Configuration Options

### Raffle Bot Configuration
- **Headless Mode**: Runs without visible browser
- **Target URL**: Update `RAFFLE_URLS` in the script

### Account Generator Configuration
- **Headless Mode**: Set in script initialization
- **CAPTCHA Solving**: Enable/disable Capsolver integration
- **Proxy Usage**: Enable/disable proxy rotation

### Email Scraper Configuration
- **Date Range**: Modify `query` variable for different date ranges
- **Subject Filter**: Change subject line search criteria

## 🛠️ Troubleshooting

### Common Issues

**"credentials.json not found"**
- Follow Gmail API setup instructions above

**"No emails found"**
- Check date range in email scraper query
- Verify Gmail account has the emails

**"Could not find email input field"**
- Website structure may have changed
- Run in visible mode to debug: `--visible`

**"Cloudflare detected"**
- Scripts include Cloudflare handling
- May need to adjust wait times

### Debug Mode
Most scripts support visible/debug mode:
```bash
python script_name.py --visible
```

## 📝 Notes

- **Rate Limiting**: Scripts include delays to avoid being flagged
- **Error Handling**: Comprehensive error logging and recovery
- **Stealth Features**: Uses undetected Chrome and realistic user behavior
- **UK Focus**: Addresses and postcodes are UK-specific

## 🔧 Technical Details

- **Browser**: Chrome with SeleniumBase (undetected mode)
- **Python Version**: 3.7+
- **APIs**: Gmail API v1
- **CAPTCHA Service**: Capsolver integration to bypass CloudFlare
- **Proxy Support**: HTTP/HTTPS proxies with authentication

---

*Last Updated: September 19, 2025*