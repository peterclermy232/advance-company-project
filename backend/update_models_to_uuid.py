#!/usr/bin/env python3
"""
Script to automatically update all model files to use UUID as primary key

This script will:
1. Read all model files
2. Remove id field definitions
3. Update uuid field to be primary_key=True
4. Save updated files

Usage:
    python update_models_to_uuid_improved.py --dry-run
    python update_models_to_uuid_improved.py --execute
"""

import os
import re
import sys


def update_model_file(filepath, dry_run=True):
    """Update a single model file to use UUID as primary key"""
    
    print(f"\nProcessing: {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Pattern 1: Remove id field definition (handles single and multi-line)
    # Matches: id = models.BigAutoField(primary_key=True)
    id_pattern = r'    id = models\.BigAutoField\(primary_key=True\)\n'
    if re.search(id_pattern, content):
        content = re.sub(id_pattern, '', content)
        changes_made.append("Removed id field definition")
    
    # Pattern 2: Update uuid field to be primary key
    # This handles multi-line uuid field definitions
    # Match uuid field that may span multiple lines
    uuid_pattern = r'    uuid = models\.UUIDField\(\s*\n\s*default=uuid\.uuid4,\s*\n\s*editable=False,\s*\n\s*unique=True,\s*\n\s*db_index=True\s*\n\s*\)'
    
    uuid_replacement = '''    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )'''
    
    if re.search(uuid_pattern, content):
        content = re.sub(uuid_pattern, uuid_replacement, content)
        changes_made.append("Updated uuid to be primary key (removed unique=True and db_index=True)")
    
    # Also handle if uuid might already be formatted differently
    # Match compact single-line version
    uuid_pattern_compact = r'    uuid = models\.UUIDField\(default=uuid\.uuid4, editable=False, unique=True, db_index=True\)'
    if re.search(uuid_pattern_compact, content):
        content = re.sub(uuid_pattern_compact, uuid_replacement, content)
        changes_made.append("Updated uuid to be primary key (compact format)")
    
    # Check if changes were made
    if content == original_content:
        print("  No changes needed")
        return False
    
    print(f"  Changes: {', '.join(changes_made)}")
    
    if not dry_run:
        # Create backup
        backup_path = filepath + '.backup'
        with open(backup_path, 'w') as f:
            f.write(original_content)
        print(f"  Backup created: {backup_path}")
        
        # Write updated content
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"  ✓ File updated")
    else:
        print(f"  [DRY RUN] Would update file")
        # Show a preview of changes
        print("\n  Preview of changes:")
        print("  " + "-" * 60)
        for change in changes_made:
            print(f"    • {change}")
    
    return True


def main():
    """Main function"""
    
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("=== DRY RUN MODE - No files will be modified ===\n")
    else:
        print("=== EXECUTING - Files will be modified ===\n")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm != 'yes':
            print("Cancelled")
            return
    
    # Model files to update
    model_files = [
        'backend/apps/accounts/models.py',
        'backend/apps/financial/models.py',
        'backend/apps/beneficiary/models.py',
        'backend/apps/documents/models.py',
        'backend/apps/applications/models.py',
        'backend/apps/notifications/models.py',
        'backend/apps/reports/models.py',
    ]
    
    files_updated = 0
    files_not_found = []
    
    for filepath in model_files:
        if os.path.exists(filepath):
            if update_model_file(filepath, dry_run):
                files_updated += 1
        else:
            files_not_found.append(filepath)
            print(f"\n✗ File not found: {filepath}")
    
    print(f"\n{'=' * 70}")
    print(f"=== Summary ===")
    print(f"{'=' * 70}")
    print(f"Files found: {len(model_files) - len(files_not_found)}")
    print(f"Files updated: {files_updated}")
    if files_not_found:
        print(f"Files not found: {len(files_not_found)}")
    
    if dry_run:
        print("\n" + "=" * 70)
        print("This was a dry run. Use --execute to apply changes.")
        print("=" * 70)
    else:
        print("\n✓ All files updated successfully")
        print("\n" + "=" * 70)
        print("IMPORTANT: Next steps:")
        print("=" * 70)
        print("1. Review the changes in each file")
        print("2. Update ForeignKey references:")
        print("   - Change to_field='uuid' for relationships")
        print("   - Or update ForeignKey to reference uuid directly")
        print("3. Run: python manage.py makemigrations")
        print("4. Review the generated migration carefully")
        print("5. Update serializers to use uuid instead of id")
        print("6. Update API endpoints and views")
        print("7. Update frontend code to use uuid")
        print("8. Test thoroughly before deploying!")
        print("=" * 70)


if __name__ == '__main__':
    main()