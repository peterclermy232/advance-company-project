import os
import logging
from django.core.files.storage import Storage
from django.conf import settings
from supabase import create_client

logger = logging.getLogger(__name__)


def get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


class SupabaseStorage(Storage):
    """
    Django storage backend using Supabase Storage (private bucket).
    Files are accessed via signed URLs, not public URLs.
    """

    def __init__(self, bucket=None):
        self.bucket = bucket or settings.SUPABASE_BUCKET

    def deconstruct(self):
        """Required for Django migrations to serialize this storage class."""
        return 'apps.documents.storage.SupabaseStorage', [], {}

    def _save(self, name, content):
        """Upload file to Supabase."""
        supabase = get_supabase()
        content.seek(0)
        file_data = content.read()

        # Determine content type
        ext = os.path.splitext(name)[1].lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')

        try:
            supabase.storage.from_(self.bucket).upload(
                path=name,
                file=file_data,
                file_options={
                    'content-type': content_type,
                    'upsert': 'true'
                }
            )
            logger.info(f"Uploaded to Supabase: {name}")
            return name
        except Exception as e:
            logger.error(f"Supabase upload error: {str(e)}")
            raise

    def _open(self, name, mode='rb'):
        raise NotImplementedError("Direct file open not supported. Use url() to get signed URL.")

    def delete(self, name):
        """Delete file from Supabase."""
        try:
            supabase = get_supabase()
            supabase.storage.from_(self.bucket).remove([name])
            logger.info(f"Deleted from Supabase: {name}")
        except Exception as e:
            logger.error(f"Supabase delete error: {str(e)}")

    def exists(self, name):
        """Check if file exists."""
        try:
            supabase = get_supabase()
            files = supabase.storage.from_(self.bucket).list(
                path=os.path.dirname(name)
            )
            filename = os.path.basename(name)
            return any(f['name'] == filename for f in files)
        except Exception:
            return False

    def url(self, name):
        """
        Generate a signed URL valid for 1 hour.
        This is what gets returned when you access document.file.url
        """
        try:
            supabase = get_supabase()
            result = supabase.storage.from_(self.bucket).create_signed_url(
                path=name,
                expires_in=3600  # 1 hour
            )
            signed_url = result.get('signedURL') or result.get('signed_url')
            logger.info(f"Generated signed URL for: {name}")
            return signed_url
        except Exception as e:
            logger.error(f"Signed URL error: {str(e)}")
            return ''

    def size(self, name):
        return 0  # Optional: implement if needed


# Backward compatibility alias — keeps old migrations working
CleanMediaCloudinaryStorage = SupabaseStorage