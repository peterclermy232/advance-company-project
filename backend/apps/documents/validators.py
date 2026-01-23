import os
from django.core.exceptions import ValidationError
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class SecureFileValidator:
    """
    PRODUCTION-OPTIMIZED file validator - minimal processing for speed
    """

    ALLOWED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }

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
        ULTRA-FAST validation - only checks:
        1. File size
        2. Extension
        3. Magic number (first 2KB only)
        """
        try:
            logger.info(f"Fast validating: {file.name}, size: {file.size}")
            
            # 1. Size check FIRST (fastest)
            if file.size > SecureFileValidator.MAX_FILE_SIZE:
                raise ValidationError(
                    f'File too large: {file.size / 1024 / 1024:.2f}MB. Maximum: 5MB'
                )

            # 2. Extension check
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in SecureFileValidator.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f'Invalid file type "{file_ext}". Allowed: PDF, JPEG, PNG, GIF'
                )

            # 3. Magic number check (only read 2KB - DO NOT read entire file)
            file.seek(0)
            header = file.read(2048)
            file.seek(0)

            expected_mime = SecureFileValidator.ALLOWED_EXTENSIONS[file_ext]
            if not SecureFileValidator._quick_magic_check(header, expected_mime):
                raise ValidationError(
                    'File content does not match extension'
                )

            # 4. For images, ONLY check if it opens (no full verification)
            if expected_mime.startswith('image/'):
                try:
                    file.seek(0)
                    img = Image.open(file)
                    width, height = img.size
                    if width * height > SecureFileValidator.MAX_IMAGE_PIXELS:
                        raise ValidationError(f'Image too large: {width}x{height}')
                    file.seek(0)
                except Exception as e:
                    raise ValidationError('Invalid image file')

            file.seek(0)
            logger.info(f"✓ File validated: {file.name}")
            return file

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise ValidationError(f'File validation failed: {str(e)}')

    @staticmethod
    def _quick_magic_check(header, expected_mime):
        """Quick magic number check"""
        if expected_mime in SecureFileValidator.MAGIC_NUMBERS:
            for magic_num in SecureFileValidator.MAGIC_NUMBERS[expected_mime]:
                if header.startswith(magic_num):
                    return True
        return False

    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename"""
        filename = os.path.basename(filename)
        dangerous_chars = ['..', '/', '\\', '\x00', '\n', '\r', '|', '<', '>', ':', '"', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '')
        
        name, ext = os.path.splitext(filename)
        name = name[:100]
        return f"{name}{ext}".strip()


def validate_document_file(file):
    """Wrapper for validation"""
    return SecureFileValidator.validate_file(file)