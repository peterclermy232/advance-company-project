# clean_and_reset.py
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

import cloudinary
import cloudinary.api
from django.conf import settings
from apps.documents.models import Document

print("="*60)
print("CLEAN START - Reset Documents")
print("="*60)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
)

# Step 1: Delete all database records
print("\n1. Deleting all Document records from database...")
count = Document.objects.count()
Document.objects.all().delete()
print(f"   ✓ Deleted {count} records")

# Step 2: Delete all files from Cloudinary documents folder
print("\n2. Cleaning Cloudinary 'documents' folder...")
try:
    # Delete image files
    result = cloudinary.api.delete_resources_by_prefix(
        'documents/',
        resource_type='image'
    )
    print(f"   ✓ Deleted {len(result.get('deleted', {}))} images")
except Exception as e:
    print(f"   ! Error deleting images: {str(e)}")

try:
    # Delete raw files (PDFs)
    result = cloudinary.api.delete_resources_by_prefix(
        'documents/',
        resource_type='raw'
    )
    print(f"   ✓ Deleted {len(result.get('deleted', {}))} raw files")
except Exception as e:
    print(f"   ! Error deleting raw files: {str(e)}")

# Step 3: Delete test folder too
print("\n3. Cleaning Cloudinary 'test' folder...")
try:
    result = cloudinary.api.delete_resources_by_prefix(
        'test/',
        resource_type='image'
    )
    print(f"   ✓ Deleted {len(result.get('deleted', {}))} test files")
except Exception as e:
    print(f"   ! Error deleting test files: {str(e)}")

print("\n" + "="*60)
print("✅ CLEAN SLATE - Ready for fresh uploads!")
print("="*60)
print("\nNext steps:")
print("1. Update your settings.py to use the custom storage:")
print("   DEFAULT_FILE_STORAGE = 'apps.documents.storage.CleanMediaCloudinaryStorage'")
print("\n2. Upload documents through your API endpoint")
print("\n3. All new uploads will work correctly!")