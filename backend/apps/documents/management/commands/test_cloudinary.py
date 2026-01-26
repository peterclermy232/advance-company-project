from django.core.management.base import BaseCommand
from django.conf import settings
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO
from PIL import Image


class Command(BaseCommand):
    help = 'Test Cloudinary configuration and upload'

    def handle(self, *args, **options):
        self.stdout.write("="*60)
        self.stdout.write(self.style.SUCCESS("Testing Cloudinary Configuration"))
        self.stdout.write("="*60)
        
        # 1. Check settings
        self.stdout.write("\n1. Checking Django settings...")
        try:
            cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME')
            api_key = settings.CLOUDINARY_STORAGE.get('API_KEY')
            api_secret = settings.CLOUDINARY_STORAGE.get('API_SECRET')
            
            if cloud_name and api_key and api_secret:
                self.stdout.write(self.style.SUCCESS(f"   ✓ Cloud Name: {cloud_name}"))
                self.stdout.write(self.style.SUCCESS(f"   ✓ API Key: {api_key[:6]}..."))
                self.stdout.write(self.style.SUCCESS(f"   ✓ API Secret: ****** (hidden)"))
            else:
                self.stdout.write(self.style.ERROR("   ✗ Cloudinary credentials missing!"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Error reading settings: {str(e)}"))
            return
        
        # 2. Check storage backend
        self.stdout.write("\n2. Checking storage backend...")
        self.stdout.write(f"   DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
        if 'cloudinary' in settings.DEFAULT_FILE_STORAGE.lower():
            self.stdout.write(self.style.SUCCESS("   ✓ Using Cloudinary storage"))
        else:
            self.stdout.write(self.style.WARNING("   ! Not using Cloudinary storage"))
        
        # 3. Test upload with generated image
        self.stdout.write("\n3. Creating test image...")
        try:
            # Create a simple test image
            img = Image.new('RGB', (300, 300), color='red')
            img_io = BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            self.stdout.write(self.style.SUCCESS("   ✓ Test image created (300x300 red square)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Failed to create image: {str(e)}"))
            return
        
        # 4. Upload to Cloudinary
        self.stdout.write("\n4. Testing upload to Cloudinary...")
        try:
            # Configure cloudinary
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret
            )
            
            # Upload the test image
            result = cloudinary.uploader.upload(
                img_io,
                folder="test",
                public_id="test_upload",
                resource_type="image"
            )
            
            self.stdout.write(self.style.SUCCESS("   ✓ Upload successful!"))
            self.stdout.write(f"   URL: {result['secure_url']}")
            self.stdout.write(f"   Public ID: {result['public_id']}")
            self.stdout.write(f"   Format: {result['format']}")
            self.stdout.write(f"   Size: {result['bytes']} bytes")
            self.stdout.write(f"   Width: {result['width']}px")
            self.stdout.write(f"   Height: {result['height']}px")
            
            # Try to access the URL
            self.stdout.write("\n5. Verifying uploaded file is accessible...")
            response = requests.get(result['secure_url'], timeout=10)
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f"   ✓ File is publicly accessible ({len(response.content)} bytes downloaded)"))
            else:
                self.stdout.write(self.style.ERROR(f"   ✗ File returned status {response.status_code}"))
            
            # Cleanup
            self.stdout.write("\n6. Cleaning up test file...")
            cloudinary.uploader.destroy(result['public_id'])
            self.stdout.write(self.style.SUCCESS("   ✓ Test file deleted from Cloudinary"))
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS("✅ Cloudinary is configured correctly!"))
            self.stdout.write(self.style.SUCCESS("✅ Ready for production use!"))
            self.stdout.write("="*60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Upload failed: {str(e)}"))
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.ERROR("❌ Cloudinary test failed!"))
            self.stdout.write("="*60)
            self.stdout.write("\nPossible issues:")
            self.stdout.write("1. Check your API credentials are correct")
            self.stdout.write("2. Verify internet connection")
            self.stdout.write("3. Check Cloudinary account is active")
            
            import traceback
            self.stdout.write(f"\nFull error:\n{traceback.format_exc()}")