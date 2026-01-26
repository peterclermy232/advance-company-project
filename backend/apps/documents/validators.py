import os
import imghdr
from django.core.exceptions import ValidationError
import logging
import re
import uuid

logger = logging.getLogger(__name__)


class SecureFileValidator:
    """
    Production-safe validator with content verification and filename sanitization.
    """

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.pdf', '.jpg', '.jpeg', '.png', '.gif'
    }

    # Mapping for content verification of images
    IMAGE_TYPES = {
        '.jpg': ['jpeg'],
        '.jpeg': ['jpeg'],
        '.png': ['png'],
        '.gif': ['gif'],
    }

    # Maximum file size: 5MB
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    @staticmethod
    def validate_file(file):
        """
        Validates uploaded files:
        1. Size check
        2. Extension check
        3. Content verification (prevents spoofing)
        """
        try:
            # 1. SIZE CHECK
            if file.size > SecureFileValidator.MAX_FILE_SIZE:
                raise ValidationError(
                    f'File too large: {file.size / 1024 / 1024:.2f}MB. Max: 5MB'
                )

            # 2. EXTENSION CHECK
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in SecureFileValidator.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f'Invalid file type "{file_ext}". Allowed: PDF, JPEG, PNG, GIF'
                )

            # 3. CONTENT VERIFICATION
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                file.seek(0)
                image_type = imghdr.what(file)
                file.seek(0)

                expected_types = SecureFileValidator.IMAGE_TYPES.get(file_ext, [])
                if image_type not in expected_types:
                    logger.warning(
                        f"File type mismatch: {file.name} - expected {file_ext}, got {image_type}"
                    )
                    raise ValidationError(
                        f'File appears to be corrupted or misnamed. Expected {file_ext} format.'
                    )

            elif file_ext == '.pdf':
                file.seek(0)
                header = file.read(5)
                file.seek(0)

                if header != b'%PDF-':
                    logger.warning(f"Invalid PDF header: {file.name}")
                    raise ValidationError('File does not appear to be a valid PDF.')

            logger.info(f"✓ File validated: {file.name} ({file.size / 1024:.1f}KB)")
            return file

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error for {file.name}: {str(e)}")
            raise ValidationError(f'File validation failed: {str(e)}')

    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filenames for safe storage in Cloudinary:
        - Removes dangerous characters and path traversal
        - Replaces spaces with underscores
        - Limits length
        - Keeps lowercase extension
        """
        # Get base filename
        filename = os.path.basename(filename)

        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')

        # Keep only alphanumeric, spaces, hyphens, underscores, dots
        filename = re.sub(r'[^\w\s.-]', '', filename)

        # Split name and extension
        name, ext = os.path.splitext(filename)

        # Generate fallback name if empty
        if not name or len(name.strip()) == 0:
            name = f'document_{uuid.uuid4().hex[:8]}'

        # Replace spaces with underscores and limit length
        name = '_'.join(name.split())
        name = name[:100]  # Limit filename length

        # Return sanitized filename with lowercase extension
        safe_filename = f"{name}{ext.lower()}".strip()

        logger.debug(f"Sanitized filename: {filename} -> {safe_filename}")
        return safe_filename


def validate_document_file(file):
    """
    Wrapper function for use in Django FileField validators
    """
    return SecureFileValidator.validate_file(file)
