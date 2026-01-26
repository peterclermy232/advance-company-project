# apps/documents/management/commands/reupload_documents.py
from django.core.management.base import BaseCommand
from apps.documents.models import Document
import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import requests
from io import BytesIO
import os


class Command(BaseCommand):
    help = 'Re-upload all documents to Cloudinary with correct paths'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--delete-all',
            action='store_true',
            help='Delete all files from Cloudinary and start fresh',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_all = options['delete_all']
        
        self.stdout.write("="*60)
        self.stdout.write(self.style.SUCCESS("Re-uploading Documents to Cloudinary"))
        self.stdout.write("="*60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))
        
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
            secure=True
        )
        
        # Option to delete all and start fresh
        if delete_all:
            if dry_run:
                self.stdout.write(self.style.WARNING("Would delete all files from Cloudinary"))
            else:
                self.stdout.write(self.style.WARNING("Deleting all files from Cloudinary..."))
                try:
                    # Delete all resources in the documents folder
                    result = cloudinary.api.delete_resources_by_prefix('documents/')
                    self.stdout.write(self.style.SUCCESS(f"Deleted {len(result.get('deleted', {}))} files"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error deleting: {str(e)}"))
        
        documents = Document.objects.all()
        total = documents.count()
        
        self.stdout.write(f"Found {total} documents to process\n")
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, doc in enumerate(documents, 1):
            self.stdout.write(f"\n[{i}/{total}] {doc.title}")
            self.stdout.write(f"   Current file.name: {doc.file.name}")
            
            # Check if file exists locally or needs to be fetched
            try:
                # Try to read the file content
                doc.file.seek(0)
                file_content = doc.file.read()
                doc.file.seek(0)
                self.stdout.write(f"   ✓ File accessible ({len(file_content)} bytes)")
                has_content = True
            except Exception as e:
                self.stdout.write(f"   ! Cannot read file locally: {str(e)}")
                
                # Try to fetch from Cloudinary using various URL formats
                has_content = False
                urls_to_try = [
                    doc.file.url,
                    f"https://res.cloudinary.com/{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}/raw/upload/{doc.file.name}",
                    f"https://res.cloudinary.com/{settings.CLOUDINARY_STORAGE['CLOUD_NAME']}/image/upload/{doc.file.name}",
                ]
                
                for url in urls_to_try:
                    try:
                        self.stdout.write(f"   Trying: {url}")
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            file_content = response.content
                            has_content = True
                            self.stdout.write(self.style.SUCCESS(f"   ✓ Downloaded from Cloudinary ({len(file_content)} bytes)"))
                            break
                    except:
                        continue
                
                if not has_content:
                    self.stdout.write(self.style.ERROR(f"   ✗ Cannot access file - SKIPPING"))
                    error_count += 1
                    continue
            
            if dry_run:
                self.stdout.write(self.style.WARNING("   [DRY RUN] Would re-upload this file"))
                continue
            
            try:
                # Determine file extension from filename
                original_name = doc.file.name
                if '.' in original_name:
                    file_ext = original_name.split('.')[-1].lower()
                else:
                    # Try to detect from content
                    try:
                        img = Image.open(BytesIO(file_content))
                        file_ext = img.format.lower()
                        self.stdout.write(f"   Detected image format: {file_ext}")
                    except:
                        file_ext = 'pdf'  # Default to PDF
                        self.stdout.write(f"   Defaulting to PDF")
                
                # Determine resource type
                image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
                resource_type = 'image' if file_ext in image_extensions else 'raw'
                
                # Create a clean public_id
                clean_name = os.path.basename(original_name).replace(f'.{file_ext}', '')
                if not clean_name or clean_name == '.':
                    clean_name = f"document_{doc.id}"
                
                self.stdout.write(f"   Uploading as {resource_type}/{file_ext}...")
                
                # Upload to Cloudinary with correct settings
                result = cloudinary.uploader.upload(
                    BytesIO(file_content),
                    folder='documents',
                    public_id=clean_name,
                    resource_type=resource_type,
                    overwrite=True,
                    unique_filename=True,
                    use_filename=True,
                    format=file_ext,
                )
                
                # Update document with new path
                # Store just the public_id with extension
                new_name = f"{result['public_id']}.{file_ext}"
                doc.file.name = new_name
                doc.save(update_fields=['file'])
                
                new_url = result['secure_url']
                self.stdout.write(self.style.SUCCESS(f"   ✓ Uploaded successfully"))
                self.stdout.write(f"   New URL: {new_url}")
                
                # Verify new URL works
                verify_response = requests.get(new_url, timeout=5)
                if verify_response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"   ✓ Verified ({len(verify_response.content)} bytes)"))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"   ✗ Verification failed (status {verify_response.status_code})"))
                    error_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ✗ Error: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
                error_count += 1
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write("="*60)
        self.stdout.write(f"Total documents: {total}")
        self.stdout.write(self.style.SUCCESS(f"Successfully re-uploaded: {success_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {error_count}"))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"Skipped: {skipped_count}"))
        self.stdout.write("="*60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a DRY RUN - no changes were made"))
            self.stdout.write("Run without --dry-run to actually re-upload files")
        elif success_count > 0:
            self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully processed {success_count} documents!"))