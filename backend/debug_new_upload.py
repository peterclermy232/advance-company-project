import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

from apps.documents.models import Document
from apps.accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
import requests

# Get a user
user = User.objects.first()
if not user:
    print("❌ No users found! Create a user first.")
    exit()

print(f"Testing upload for user: {user.email}")

# Create test image
img = Image.new('RGB', (200, 200), color='green')
img_io = BytesIO()
img.save(img_io, format='JPEG')
img_io.seek(0)

# Create uploaded file
uploaded_file = SimpleUploadedFile(
    "test_green_square.jpg",
    img_io.read(),
    content_type="image/jpeg"
)

# Create document
print("\n📤 Uploading document...")
doc = Document.objects.create(
    user=user,
    title="Test Green Square",
    category="identity",
    file=uploaded_file
)

print(f"✅ Document created: ID={doc.id}")
print(f"📁 Stored path: {doc.file.name}")
print(f"🔗 URL: {doc.file.url}")

# Test the URL
print("\n🔍 Testing URL...")
response = requests.get(doc.file.url, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print(f"✅ SUCCESS! File is accessible ({len(response.content)} bytes)")
    print("\n🎉 Everything is working correctly!")
else:
    print(f"❌ FAILED! URL returned status {response.status_code}")