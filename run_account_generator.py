#!/usr/bin/env python3
"""
Run the Chaos Cards account generator with emails from CSV
"""

import csv
import os
import time
from chaos_cards_account_generator import ChaosCardsAccountGenerator


def load_account_info_from_csv(csv_path: str = "accountgen.csv") -> list:
    """Load account information from CSV file, excluding already completed accounts"""
    account_info_list = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header row
            
            # Check if status column exists
            has_status_column = len(header) > 5
            if not has_status_column:
                print("📝 No status column found - will add one to track progress")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since we skipped header
                if row and len(row) >= 5 and row[1] and '@' in row[1]:
                    # Check status if column exists
                    status = row[5].strip() if len(row) > 5 and row[5] else ""
                    
                    # Skip if already completed (check multiple completion indicators)
                    if any(indicator in status.lower() for indicator in ['completed', 'done', 'success', '✅', 'finished']):
                        print(f"⏭️ Skipping {row[0]} ({row[1]}) - already completed ({status})")
                        continue
                    
                    # Also skip if marked as failed and we're not retrying failed ones
                    if any(indicator in status.lower() for indicator in ['failed', '❌', 'error']) and 'retry' not in status.lower():
                        print(f"⏭️ Skipping {row[0]} ({row[1]}) - marked as failed ({status})")
                        continue
                    
                    # Clean up the data
                    account_info = {
                        'name': row[0].strip(),
                        'email': row[1].strip(),
                        'first_line_address': row[2].strip(),
                        'City': row[3].strip(),
                        'PostalCode': row[4].strip(),
                        'row_number': row_num,  # Track row for updating
                        'status': status
                    }
                    account_info_list.append(account_info)
        
        print(f"📊 Loaded {len(account_info_list)} pending accounts from {csv_path}")
    else:
        print(f"❌ CSV file {csv_path} not found!")
    return account_info_list


def update_account_status_in_csv(csv_path: str, row_number: int, status: str, password: str = ""):
    """Update the status of an account in the CSV file"""
    try:
        # Read all rows
        rows = []
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
        
        # Ensure header has status and password columns
        if len(rows) > 0:
            header = rows[0]
            if len(header) == 5:  # Original format: name,,first_line_address,City,PostalCode
                header.extend(['Status', 'Password', 'Created_Date'])
                print("📝 Added Status, Password, and Created_Date columns to CSV")
        
        # Update the specific row
        if row_number < len(rows):
            row = rows[row_number - 1]  # Convert to 0-based index
            
            # Extend row if needed
            while len(row) < 8:
                row.append('')
            
            row[5] = status  # Status column
            if password:
                row[6] = password  # Password column
            if status.lower() in ['completed', 'done', 'success', '✅']:
                from datetime import datetime
                row[7] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Created date
        
        # Write back to file
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        
        print(f"📝 Updated CSV: Row {row_number} status = {status}")
        
    except Exception as e:
        print(f"⚠️ Failed to update CSV status: {e}")


def main():
    # Load account info from CSV (excluding already completed)
    account_info_list = load_account_info_from_csv("accountgen.csv")
    
    if not account_info_list:
        print("✅ No pending accounts found to process! All may be completed already.")
        return
    
    # Show summary
    print(f"\n📊 Account Summary:")
    print(f"   Pending accounts: {len(account_info_list)}")
    
    # Ask user how many accounts to create (or use all)
    try:
        max_accounts = input(f"How many accounts to create? (Enter number or 'all' for all {len(account_info_list)} pending accounts): ").strip()
        if max_accounts.lower() == 'all':
            selected_accounts = account_info_list
        else:
            num_accounts = int(max_accounts)
            selected_accounts = account_info_list[:num_accounts]
    except (ValueError, KeyboardInterrupt):
        print("Using first 5 accounts for testing...")
        selected_accounts = account_info_list[:5]
    
    print(f"Creating accounts for {len(selected_accounts)} people...")
    
    # Initialize and run account generator
    generator = ChaosCardsAccountGenerator(selected_accounts, headless=True)
    
    # Process accounts one by one with status updates
    successful_count = 0
    failed_count = 0
    
    for i, account_info in enumerate(selected_accounts, 1):
        email = account_info["email"]
        name = account_info["name"]
        row_number = account_info["row_number"]
        
        print(f"\n🔄 Creating account {i}/{len(selected_accounts)}: {name} ({email})")
        
        try:
            # Mark as in progress
            update_account_status_in_csv("accountgen.csv", row_number, "In Progress")
            
            # Generate account data and create account with retry logic
            account_data = generator.generate_account_data(account_info)
            
            # Try up to 2 times for each account
            max_retries = 2
            success = False
            
            for attempt in range(1, max_retries + 1):
                if attempt > 1:
                    print(f"🔄 Retry attempt {attempt}/{max_retries} for {name}")
                    # Generate fresh account data for retry (new password)
                    account_data = generator.generate_account_data(account_info)
                
                success = generator._create_single_account(account_data)
                
                if success == 'already_registered':
                    # Email already registered - mark as completed with special password
                    print(f"📧 Email {email} already registered - marking as completed")
                    update_account_status_in_csv("accountgen.csv", row_number, "✅ Completed", "IDK")
                    successful_count += 1
                    break  # No need to retry
                elif success:
                    break
                elif attempt < max_retries:
                    print(f"⚠️ Attempt {attempt} failed, will retry with fresh session...")
                    time.sleep(3)  # Brief pause before retry
            
            if success == 'already_registered':
                # Already handled above
                pass
            elif success:
                successful_count += 1
                # Mark as completed with password
                update_account_status_in_csv("accountgen.csv", row_number, "✅ Completed", account_data["password"])
                print(f"✅ Account created successfully! Password: {account_data['password']}")
            else:
                failed_count += 1
                # Mark as failed
                update_account_status_in_csv("accountgen.csv", row_number, "❌ Failed")
                print("❌ Account creation failed")
                
        except Exception as e:
            failed_count += 1
            error_msg = f"Error: {str(e)}"
            update_account_status_in_csv("accountgen.csv", row_number, f"❌ Failed: {error_msg[:50]}")
            print(f"❌ Account creation failed with error: {e}")
        
        # Add delay between accounts
        if i < len(selected_accounts):
            print(f"⏳ Waiting 5 seconds before next account...")
            time.sleep(5)
    
    # Print final summary
    print("\n" + "="*60)
    print("🎯 FINAL ACCOUNT CREATION RESULTS")
    print("="*60)
    print(f"✅ Successful accounts: {successful_count}")
    print(f"❌ Failed accounts: {failed_count}")
    print(f"📊 Total processed: {successful_count + failed_count}")
    print(f"\n📝 Status tracking saved to accountgen.csv")
    print(f"💡 Tip: Run again to continue with remaining accounts!")


if __name__ == "__main__":
    main()