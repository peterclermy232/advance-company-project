# storage.py - Complete fix for Cloudinary storage
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.conf import settings
import cloudinary
import cloudinary.uploader
import logging
import os

logger = logging.getLogger(__name__)


class CleanMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Custom Cloudinary storage that properly handles images and documents
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure cloudinary is configured
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE['CLOUD_NAME'],
            api_key=settings.CLOUDINARY_STORAGE['API_KEY'],
            api_secret=settings.CLOUDINARY_STORAGE['API_SECRET'],
            secure=True
        )
    
    def _save(self, name, content):
        """
        Override save to upload directly to Cloudinary with correct settings
        """
        # Remove 'media/' prefix if present
        if name.startswith('media/'):
            name = name[6:]
        
        # Get file extension
        file_ext = os.path.splitext(name)[1].lower().lstrip('.')
        
        # Determine resource type
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        resource_type = 'image' if file_ext in image_extensions else 'raw'
        
        # Clean the filename - remove folder structure for simpler paths
        clean_name = os.path.basename(name)
        public_id = os.path.splitext(clean_name)[0]
        
        logger.info(f"Uploading to Cloudinary: {clean_name} as {resource_type}")
        
        try:
            # Upload directly using cloudinary uploader
            result = cloudinary.uploader.upload(
                content,
                folder='documents',  # All files go in 'documents' folder
                public_id=public_id,
                resource_type=resource_type,
                overwrite=False,  # Don't overwrite existing files
                unique_filename=True,  # Generate unique names if needed
                use_filename=True,  # Use original filename as base
            )
            
            # Extract the public_id from result (includes folder)
            saved_name = result['public_id']
            
            # Add extension back for proper URL generation
            if not saved_name.endswith(f'.{file_ext}'):
                saved_name = f"{saved_name}.{file_ext}"
            
            logger.info(f"✅ Uploaded successfully: {result['secure_url']}")
            logger.info(f"   Public ID: {result['public_id']}")
            logger.info(f"   Resource Type: {result['resource_type']}")
            
            # Return the path that will be stored in the database
            return saved_name
            
        except Exception as e:
            logger.error(f"❌ Cloudinary upload failed: {str(e)}")
            raise
    
    def url(self, name):
        """
        Generate the correct Cloudinary URL
        """
        if not name:
            return ''
        
        # Remove 'media/' prefix if present
        if name.startswith('media/'):
            name = name[6:]
        
        # Get file extension
        file_ext = os.path.splitext(name)[1].lower().lstrip('.')
        
        # Determine resource type
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        resource_type = 'image' if file_ext in image_extensions else 'raw'
        
        # Remove extension from name for public_id
        public_id = os.path.splitext(name)[0]
        
        # Build Cloudinary URL
        cloud_name = settings.CLOUDINARY_STORAGE['CLOUD_NAME']
        url = f"https://res.cloudinary.com/{cloud_name}/{resource_type}/upload/{public_id}.{file_ext}"
        
        logger.debug(f"Generated URL: {url}")
        return url
    
    def delete(self, name):
        """
        Delete file from Cloudinary
        """
        if not name:
            return
        
        try:
            # Remove extension and 'media/' prefix
            if name.startswith('media/'):
                name = name[6:]
            
            public_id = os.path.splitext(name)[0]
            
            # Get resource type
            file_ext = os.path.splitext(name)[1].lower().lstrip('.')
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
            resource_type = 'image' if file_ext in image_extensions else 'raw'
            
            # Delete from Cloudinary
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            
            logger.info(f"Deleted from Cloudinary: {public_id} (result: {result.get('result')})")
            
        except Exception as e:
            logger.error(f"Error deleting from Cloudinary: {str(e)}")
    
    def exists(self, name):
        """
        Check if file exists in Cloudinary
        """
        if not name:
            return False
        
        try:
            if name.startswith('media/'):
                name = name[6:]
            
            public_id = os.path.splitext(name)[0]
            file_ext = os.path.splitext(name)[1].lower().lstrip('.')
            
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
            resource_type = 'image' if file_ext in image_extensions else 'raw'
            
            # Try to get resource info
            cloudinary.api.resource(public_id, resource_type=resource_type)
            return True
            
        except cloudinary.exceptions.NotFound:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence: {str(e)}")
            return False