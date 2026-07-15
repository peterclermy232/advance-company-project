#!/usr/bin/env python
import os
import sys
import django
import logging

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

from apps.documents.models import Document

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("="*60)
print("Fixing old documents to regenerate correct Cloudinary URLs")
print("="*60)

documents = Document.objects.exclude(file='')  # Only docs with files
fixed_count = 0

for doc in documents:
    old_url = doc.file.url
    # Trigger storage backend to regenerate URL
    doc.file.name = doc.file.name
    doc.save(update_fields=['file'])
    new_url = doc.file.url
    logger.info(f"[{doc.id}] {old_url} -> {new_url}")
    fixed_count += 1

print(f"\n✅ Fixed {fixed_count} documents successfully!")
print("="*60)
