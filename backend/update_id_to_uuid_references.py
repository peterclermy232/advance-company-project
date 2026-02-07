#!/usr/bin/env python3
"""
Script to update .id references to .uuid in Python files

This script will:
1. Find all instance.id references in logger statements
2. Find all admin.id references
3. Replace them with .uuid
4. Handle related_*_id parameters

Usage:
    python update_id_to_uuid_references.py --dry-run
    python update_id_to_uuid_references.py --execute --file signals.py
    python update_id_to_uuid_references.py --execute --all
"""

import os
import re
import sys
import argparse


def update_file_references(filepath, dry_run=True):
    """Update .id references to .uuid in a file"""
    
    print(f"\nProcessing: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  ✗ File not found: {filepath}")
        return False
    
    original_content = content
    changes_made = []
    
    # Pattern 1: instance.id in log messages and f-strings
    # Examples: {instance.id}, instance.id
    patterns_to_replace = [
        # Logger statements with instance.id
        (r'f"([^"]*){instance\.id}([^"]*)"', r'f"\1{instance.uuid}\2"'),
        (r"f'([^']*){instance\.id}([^']*)'", r"f'\1{instance.uuid}\2'"),
        
        # Admin.id in logger statements
        (r'f"([^"]*){admin\.id}([^"]*)"', r'f"\1{admin.uuid}\2"'),
        (r"f'([^']*){admin\.id}([^']*)'", r"f'\1{admin.uuid}\2'"),
        
        # related_*_id parameters (these should reference uuid now)
        (r'related_deposit_id=instance\.id', r'related_deposit_id=instance.uuid'),
        (r'related_application_id=instance\.id', r'related_application_id=instance.uuid'),
        (r'related_document_id=instance\.id', r'related_document_id=instance.uuid'),
        (r'related_beneficiary_id=instance\.id', r'related_beneficiary_id=instance.uuid'),
        (r'related_user_id=instance\.id', r'related_user_id=instance.uuid'),
    ]
    
    for pattern, replacement in patterns_to_replace:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes_made.append(f"Replaced pattern: {pattern[:50]}...")
    
    # Check if changes were made
    if content == original_content:
        print("  No changes needed")
        return False
    
    print(f"  Changes found: {len(changes_made)}")
    for change in changes_made:
        print(f"    • {change}")
    
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
        # Show a preview
        print("\n  Preview of first few changes:")
        lines = content.split('\n')
        orig_lines = original_content.split('\n')
        for i, (orig, new) in enumerate(zip(orig_lines, lines)):
            if orig != new:
                print(f"    Line {i+1}:")
                print(f"      - {orig.strip()}")
                print(f"      + {new.strip()}")
                if i > 3:  # Only show first few
                    print("    ... (more changes)")
                    break
    
    return True


def find_python_files(directory, exclude_dirs=None):
    """Recursively find all Python files"""
    if exclude_dirs is None:
        exclude_dirs = ['venv', 'env', '__pycache__', '.git', 'migrations', 'node_modules']
    
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update .id references to .uuid')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Run in dry-run mode (default)')
    parser.add_argument('--execute', action='store_true',
                        help='Execute the changes')
    parser.add_argument('--file', type=str,
                        help='Single file to update')
    parser.add_argument('--all', action='store_true',
                        help='Update all Python files in backend/')
    parser.add_argument('--directory', type=str, default='backend/',
                        help='Directory to search (default: backend/)')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("=== DRY RUN MODE - No files will be modified ===\n")
    else:
        print("=== EXECUTING - Files will be modified ===\n")
        confirm = input("Are you sure? Type 'yes' to confirm: ")
        if confirm != 'yes':
            print("Cancelled")
            return
    
    files_to_update = []
    
    if args.file:
        files_to_update = [args.file]
    elif args.all:
        print(f"Searching for Python files in {args.directory}...")
        files_to_update = find_python_files(args.directory)
        print(f"Found {len(files_to_update)} Python files\n")
    else:
        # Default files to check
        files_to_update = [
            'backend/apps/notifications/signals.py',
            'backend/apps/notifications/views.py',
            'backend/apps/financial/views.py',
            'backend/apps/applications/views.py',
            'backend/apps/documents/views.py',
            'backend/apps/beneficiary/views.py',
        ]
    
    files_updated = 0
    files_not_found = []
    
    for filepath in files_to_update:
        if os.path.exists(filepath):
            if update_file_references(filepath, dry_run):
                files_updated += 1
        else:
            files_not_found.append(filepath)
    
    print(f"\n{'=' * 70}")
    print(f"=== Summary ===")
    print(f"{'=' * 70}")
    print(f"Files processed: {len(files_to_update)}")
    print(f"Files with changes: {files_updated}")
    if files_not_found:
        print(f"Files not found: {len(files_not_found)}")
        for f in files_not_found:
            print(f"  - {f}")
    
    if dry_run:
        print("\n" + "=" * 70)
        print("This was a dry run. Use --execute to apply changes.")
        print("=" * 70)
    else:
        print("\n✓ All files updated successfully")
        print("\nNext steps:")
        print("1. Review the changes")
        print("2. Search for any remaining .id references manually")
        print("3. Update serializers")
        print("4. Update API views")
        print("5. Run tests")


if __name__ == '__main__':
    main()