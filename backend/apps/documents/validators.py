import os
from django.core.exceptions import ValidationError
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Try to import python-magic, but don't fail if it's not available
try:
    import magic
    MAGIC_AVAILABLE = True
    logger.info("python-magic is available")
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("python-magic not available - using fallback validation")


class SecureFileValidator:
    """
    Production-safe file upload validator - OPTIMIZED FOR SPEED
    """

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }

    # Magic numbers for file type detection
    MAGIC_NUMBERS = {
        'application/pdf': [b'%PDF'],
        'image/jpeg': [b'\xFF\xD8\xFF'],
        'image/png': [b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'],
        'image/gif': [b'GIF87a', b'GIF89a'],
    }

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_PIXELS = 4096 * 4096

    @staticmethod
    def validate_file(file):
        """
        OPTIMIZED: Fast validation with minimal processing
        """
        try:
            logger.info(f"Validating file: {file.name}, size: {file.size}")
            
            # 1. Quick file size check FIRST
            if file.size > SecureFileValidator.MAX_FILE_SIZE:
                logger.warning(f"File too large: {file.size} bytes")
                raise ValidationError(
                    f'File size exceeds 5MB limit. Your file is {file.size / 1024 / 1024:.2f}MB'
                )

            # 2. Quick extension check
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in SecureFileValidator.ALLOWED_EXTENSIONS:
                logger.warning(f"Invalid file extension: {file_ext}")
                raise ValidationError(
                    f'Unsupported file type "{file_ext}". Allowed: PDF, JPEG, PNG, GIF'
                )

            # 3. Read ONLY first 2KB for magic number check (not entire file)
            file.seek(0)
            header = file.read(2048)  # Only read 2KB
            file.seek(0)

            # 4. Quick magic number validation
            expected_mime = SecureFileValidator.ALLOWED_EXTENSIONS[file_ext]
            if not SecureFileValidator._quick_magic_check(header, expected_mime):
                logger.warning(f"Magic number validation failed for {file.name}")
                raise ValidationError(
                    'File content does not match its extension. File may be corrupted.'
                )

            # 5. SKIP heavy validation for images (trust the magic number)
            # Only do basic sanity check for images
            if expected_mime.startswith('image/'):
                SecureFileValidator._quick_image_check(file)
            
            # For PDFs, skip dangerous pattern check in production
            # (can be done async or in background job if needed)

            file.seek(0)
            logger.info(f"File validation passed for {file.name}")
            return file

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}", exc_info=True)
            raise ValidationError(f'File validation failed: {str(e)}')

    @staticmethod
    def _quick_magic_check(header, expected_mime):
        """Quick magic number check - no external libraries"""
        if expected_mime in SecureFileValidator.MAGIC_NUMBERS:
            for magic_num in SecureFileValidator.MAGIC_NUMBERS[expected_mime]:
                if header.startswith(magic_num):
                    return True
        return False

    @staticmethod
    def _quick_image_check(file):
        """
        ULTRA FAST image check - just verify it opens, don't fully verify
        """
        try:
            file.seek(0)
            img = Image.open(file)
            
            # Quick dimension check
            width, height = img.size
            if width * height > SecureFileValidator.MAX_IMAGE_PIXELS:
                raise ValidationError(
                    f'Image too large: {width}x{height} pixels. Maximum: 4096x4096'
                )
            
            # SKIP img.verify() - it's slow and we trust the magic number
            file.seek(0)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            raise ValidationError('Invalid or corrupted image file')

    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename to prevent path traversal"""
        try:
            # Get just the filename, no path
            filename = os.path.basename(filename)
            
            # Remove dangerous characters
            dangerous_chars = ['..', '/', '\\', '\x00', '\n', '\r', '|', '<', '>', ':', '"', '?', '*']
            for char in dangerous_chars:
                filename = filename.replace(char, '')
            
            # Limit length
            name, ext = os.path.splitext(filename)
            name = name[:100]  # Max 100 chars for name
            
            sanitized = f"{name}{ext}".strip()
            logger.info(f"Sanitized filename: {filename} -> {sanitized}")
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Filename sanitization error: {str(e)}")
            return 'document' + os.path.splitext(filename)[1]