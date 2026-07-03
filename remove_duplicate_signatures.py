#!/usr/bin/env python3
"""
Remove duplicate signatures from the Supabase signatories table.

Duplicates are identified by email address. For each email with multiple signatures,
only the most recent one (by created_at) is kept. All other entries are deleted.

Usage:
    python remove_duplicate_signatures.py [--dry-run] [--force]

Options:
    --dry-run   Show what would be deleted without actually deleting
    --force     Skip confirmation prompt and proceed with deletion
"""

import os
import sys
import argparse
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

# --- Configuration from Environment Variables ---
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
TARGET_TABLE = 'signatories'


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "Supabase URL or Service Role Key environment variables are not set.\n"
            "Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def fetch_all_signatures(supabase: Client) -> list:
    """Fetch all signatures from the database."""
    try:
        response = supabase.table(TARGET_TABLE).select('*').execute()
        if response.data:
            print(f"✓ Fetched {len(response.data)} total signatures")
            return response.data
        else:
            print(f"✗ Error fetching data: {response.error}")
            return []
    except Exception as e:
        print(f"✗ An error occurred during fetch: {e}")
        return []


def identify_duplicates(signatures: list) -> tuple[dict, list]:
    """
    Identify duplicate signatures by email.
    
    Returns:
        tuple: (dict of email -> [signatures], list of duplicate IDs to remove)
    """
    email_groups = {}
    
    # Group signatures by email
    for sig in signatures:
        email = sig.get('email', '').lower()
        if email:
            if email not in email_groups:
                email_groups[email] = []
            email_groups[email].append(sig)
    
    # Identify duplicates and mark for removal
    duplicates_to_remove = []
    duplicate_count = 0
    
    for email, sigs in email_groups.items():
        if len(sigs) > 1:
            # Sort by created_at (most recent last)
            sigs_sorted = sorted(
                sigs,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )
            # Keep the first (most recent), mark others for removal
            for sig in sigs_sorted[1:]:
                duplicates_to_remove.append(sig['id'])
                duplicate_count += 1
    
    return email_groups, duplicates_to_remove


def report_duplicates(email_groups: dict, duplicates_to_remove: list) -> None:
    """Print a detailed report of duplicates found."""
    print("\n" + "="*70)
    print("DUPLICATE ANALYSIS REPORT")
    print("="*70)
    
    duplicate_emails = {
        email: sigs for email, sigs in email_groups.items()
        if len(sigs) > 1
    }
    
    print(f"\nEmails with duplicates: {len(duplicate_emails)}")
    print(f"Total duplicate entries to remove: {len(duplicates_to_remove)}\n")
    
    for email, sigs in sorted(duplicate_emails.items()):
        print(f"\n📧 Email: {email}")
        print(f"   Total entries: {len(sigs)}")
        
        sigs_sorted = sorted(
            sigs,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        for i, sig in enumerate(sigs_sorted):
            created = sig.get('created_at', 'N/A')
            name = f"{sig.get('first_name', '')} {sig.get('last_name', '')}".strip()
            sig_id = sig['id']
            status = "✓ KEEP (most recent)" if i == 0 else "✗ REMOVE"
            
            print(f"   {status}")
            print(f"      ID: {sig_id}")
            print(f"      Name: {name}")
            print(f"      Created: {created}")
    
    print("\n" + "="*70)


def delete_duplicates(supabase: Client, duplicate_ids: list, dry_run: bool = False) -> bool:
    """
    Delete duplicate signatures.
    
    Args:
        supabase: Supabase client
        duplicate_ids: List of IDs to delete
        dry_run: If True, don't actually delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not duplicate_ids:
        print("\n✓ No duplicates to remove!")
        return True
    
    if dry_run:
        print(f"\n[DRY RUN] Would delete {len(duplicate_ids)} duplicate entries")
        return True
    
    try:
        # Delete each duplicate
        deleted_count = 0
        failed_count = 0
        
        print(f"\nDeleting {len(duplicate_ids)} duplicate entries...")
        
        for sig_id in duplicate_ids:
            try:
                supabase.table(TARGET_TABLE).delete().eq('id', sig_id).execute()
                deleted_count += 1
            except Exception as e:
                print(f"   ✗ Failed to delete {sig_id}: {e}")
                failed_count += 1
        
        print(f"\n✓ Successfully deleted: {deleted_count}")
        if failed_count > 0:
            print(f"✗ Failed to delete: {failed_count}")
        
        return failed_count == 0
    
    except Exception as e:
        print(f"✗ Error during deletion: {e}")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Remove duplicate signatures from the Supabase database"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview duplicates without deleting'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation and proceed with deletion'
    )
    
    args = parser.parse_args()
    
    try:
        print("Connecting to Supabase...")
        supabase = get_supabase_client()
        
        print("Fetching all signatures...")
        signatures = fetch_all_signatures(supabase)
        
        if not signatures:
            print("✗ No signatures found!")
            return 1
        
        print("\nAnalyzing for duplicates...")
        email_groups, duplicates_to_remove = identify_duplicates(signatures)
        
        report_duplicates(email_groups, duplicates_to_remove)
        
        if not duplicates_to_remove:
            print("✓ No duplicates found!")
            return 0
        
        # Handle deletion
        if args.dry_run:
            print("\n[DRY RUN MODE] No changes were made.")
            return 0
        
        if not args.force:
            response = input(
                f"\n⚠️  Proceed with deleting {len(duplicates_to_remove)} "
                "duplicate entries? (yes/no): "
            )
            if response.lower() not in ['yes', 'y']:
                print("Cancelled. No changes were made.")
                return 0
        
        success = delete_duplicates(supabase, duplicates_to_remove, dry_run=False)
        
        if success:
            print("\n✓ Deduplication complete!")
            return 0
        else:
            print("\n✗ Deduplication encountered errors")
            return 1
    
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
