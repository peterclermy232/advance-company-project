import os
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class SecureFileValidator:
    """
    PRODUCTION-SAFE MINIMAL VALIDATOR
    Only checks: size, extension
    NO content validation to avoid timeouts
    """

    ALLOWED_EXTENSIONS = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif'
    }

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def validate_file(file):
        """
        MINIMAL VALIDATION - MAXIMUM SPEED
        Only checks size and extension
        """
        try:
            # 1. SIZE CHECK (instant)
            if file.size > SecureFileValidator.MAX_FILE_SIZE:
                raise ValidationError(
                    f'File too large: {file.size / 1024 / 1024:.2f}MB. Max: 5MB'
                )

            # 2. EXTENSION CHECK (instant)
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in SecureFileValidator.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f'Invalid file type "{file_ext}". Allowed: PDF, JPEG, PNG, GIF'
                )

            # 3. THAT'S IT - NO CONTENT VALIDATION
            # Trust the browser and Django's FileField validation
            
            logger.info(f"✓ File validated (minimal): {file.name}")
            return file

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise ValidationError(f'Invalid file: {str(e)}')

    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename - fast"""
        filename = os.path.basename(filename)
        dangerous_chars = ['..', '/', '\\', '\x00', '|', '<', '>', ':', '"', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '')
        
        name, ext = os.path.splitext(filename)
        return f"{name[:100]}{ext}".strip()


def validate_document_file(file):
    """Wrapper for validation"""
    return SecureFileValidator.validate_file(file)