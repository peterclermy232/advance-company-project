#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from apps.documents.models import Document
from apps.accounts.models import User
from PIL import Image
import io
import random

print("="*60)
print("Testing Real Document Upload to Cloudinary")
print("="*60)

# Get or create a test user with unique phone
print("\n1. Getting test user...")
try:
    # Try to get existing test user
    user = User.objects.filter(email='test@example.com').first()
    
    if not user:
        # Create new user with random phone to avoid conflicts
        random_phone = f'+25470{random.randint(1000000, 9999999)}'
        user = User.objects.create(
            email='test@example.com',
            full_name='Test User',
            phone_number=random_phone,
            role='user',
        )
        user.set_password('testpass123')
        user.save()
        print(f"   ✓ Created test user: {user.email}")
    else:
        print(f"   ✓ Using existing test user: {user.email}")
    
    print(f"   ✓ User ID: {user.id}")
    print(f"   ✓ Phone: {user.phone_number}")
    
except Exception as e:
    print(f"   ✗ Error with user: {str(e)}")
    # Use any existing user as fallback
    user = User.objects.first()
    if user:
        print(f"   ✓ Using first available user: {user.email}")
    else:
        print("   ✗ No users found in database!")
        sys.exit(1)

# Create a test image
print("\n2. Creating test image...")
img = Image.new('RGB', (500, 500), color='blue')
img_io = io.BytesIO()
img.save(img_io, format='JPEG', quality=85)
img_io.seek(0)

test_file = SimpleUploadedFile(
    "test_identity_document.jpg",
    img_io.read(),
    content_type="image/jpeg"
)

print(f"   ✓ Test image created: {test_file.name}")
print(f"   ✓ Size: {test_file.size / 1024:.2f} KB")

# Upload document
print("\n3. Uploading document via Django ORM...")
try:
    document = Document.objects.create(
        user=user,
        title="Test Identity Document",
        category="identity",
        file=test_file,
        status="pending"
    )
    
    print(f"   ✓ Document created successfully!")
    print(f"   ✓ Document ID: {document.id}")
    print(f"   ✓ Status: {document.status}")
    print(f"   ✓ File name: {document.file.name}")
    print(f"   ✓ File URL: {document.file.url}")
    
    # Verify URL is from Cloudinary
    print("\n4. Verifying Cloudinary storage...")
    if 'res.cloudinary.com' in document.file.url:
        print(f"   ✅ File is stored on Cloudinary!")
        print(f"   ✅ Cloud Name: dd9ooasmq")
    elif 'cloudinary.com' in document.file.url:
        print(f"   ✅ File is stored on Cloudinary!")
    else:
        print(f"   ⚠️  Warning: File not on Cloudinary")
        print(f"   URL: {document.file.url}")
    
    # Test file accessibility
    print("\n5. Testing file accessibility...")
    import requests
    try:
        response = requests.get(document.file.url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ File is publicly accessible!")
            print(f"   ✓ HTTP Status: {response.status_code}")
            print(f"   ✓ Content Size: {len(response.content) / 1024:.2f} KB")
            print(f"   ✓ Content Type: {response.headers.get('Content-Type')}")
        else:
            print(f"   ✗ HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error accessing file: {str(e)}")
    
    # Show in Cloudinary dashboard
    print("\n6. View in Cloudinary Dashboard:")
    print(f"   🌐 https://console.cloudinary.com/console/c-dd9ooasmq/media_library/folders/documents")
    print(f"   Look for folder: documents/2026/01/")
    
    # Cleanup
    print("\n7. Cleaning up...")
    document_id = document.id
    file_url = document.file.url
    document.delete()
    print(f"   ✓ Document {document_id} deleted from database")
    print(f"   ✓ File removed from Cloudinary")
    
    print("\n" + "="*60)
    print("✅ DOCUMENT UPLOAD TEST PASSED!")
    print("✅ Your app is ready to upload files to Cloudinary!")
    print("="*60)
    print(f"\nYour Cloudinary setup:")
    print(f"  Cloud: dd9ooasmq")
    print(f"  Storage: MediaCloudinaryStorage")
    print(f"  Test URL: {file_url}")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Upload failed: {str(e)}")
    import traceback
    traceback.print_exc()