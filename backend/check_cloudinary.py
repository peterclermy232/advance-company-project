import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

import cloudinary
import cloudinary.api
from django.conf import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
    api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
)

print("="*60)
print("Checking Cloudinary Storage")
print("="*60)

try:
    print("\n📷 IMAGE files in 'documents' folder:")
    images = cloudinary.api.resources(
        type='upload',
        prefix='documents/',
        resource_type='image',
        max_results=100
    )
    for resource in images.get('resources', []):
        print(f"   ✓ {resource['public_id']}")
        print(f"     {resource['secure_url']}")
    print(f"   Total: {len(images.get('resources', []))} images")
    
except Exception as e:
    print(f"   Error: {str(e)}")

try:
    print("\n📄 RAW files in 'documents' folder:")
    raw = cloudinary.api.resources(
        type='upload',
        prefix='documents/',
        resource_type='raw',
        max_results=100
    )
    for resource in raw.get('resources', []):
        print(f"   ✓ {resource['public_id']}")
        print(f"     {resource['secure_url']}")
    print(f"   Total: {len(raw.get('resources', []))} raw files")
    
except Exception as e:
    print(f"   Error: {str(e)}")

try:
    print("\n📁 ROOT level files (not in folders):")
    root_images = cloudinary.api.resources(
        type='upload',
        resource_type='image',
        max_results=100
    )
    count = 0
    for resource in root_images.get('resources', []):
        if not resource['public_id'].startswith('documents/') and not resource['public_id'].startswith('test/'):
            print(f"   ✓ {resource['public_id']}")
            print(f"     {resource['secure_url']}")
            count += 1
    print(f"   Total: {count} root images")
    
except Exception as e:
    print(f"   Error: {str(e)}")

print("\n" + "="*60)
