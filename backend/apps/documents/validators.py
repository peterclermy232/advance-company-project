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
    Production-safe file upload validator
    Works with or without python-magic
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
        Main validation entry point
        """
        try:
            logger.info(f"Validating file: {file.name}, size: {file.size}")
            
            # 1. File size check
            if file.size > SecureFileValidator.MAX_FILE_SIZE:
                logger.warning(f"File too large: {file.size} bytes")
                raise ValidationError(f'File size exceeds 5MB limit. Your file is {file.size / 1024 / 1024:.2f}MB')

            # 2. Extension check
            file_ext = os.path.splitext(file.name)[1].lower()
            if file_ext not in SecureFileValidator.ALLOWED_EXTENSIONS:
                logger.warning(f"Invalid file extension: {file_ext}")
                raise ValidationError(f'Unsupported file type "{file_ext}". Allowed: PDF, JPEG, PNG, GIF')

            # 3. Read file header for magic number check
            file.seek(0)
            header = file.read(min(2048, file.size))
            file.seek(0)

            # 4. Determine MIME type
            expected_mime = SecureFileValidator.ALLOWED_EXTENSIONS[file_ext]
            
            if MAGIC_AVAILABLE:
                mime = SecureFileValidator._validate_with_magic(header, expected_mime)
            else:
                mime = SecureFileValidator._validate_with_magic_numbers(header, expected_mime)

            if not mime:
                logger.warning(f"File type validation failed for {file.name}")
                raise ValidationError('File content does not match its extension. File may be corrupted.')

            # 5. Type-specific validation
            if mime.startswith('image/'):
                SecureFileValidator._validate_image(file)
            elif mime == 'application/pdf':
                SecureFileValidator._validate_pdf(file)

            file.seek(0)
            logger.info(f"File validation passed for {file.name}")
            return file

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected validation error: {str(e)}", exc_info=True)
            raise ValidationError(f'File validation failed: {str(e)}')

    @staticmethod
    def _validate_with_magic(header, expected_mime):
        """Validate using python-magic library"""
        try:
            mime = magic.from_buffer(header, mime=True)
            logger.info(f"Detected MIME type (magic): {mime}")
            
            if mime not in SecureFileValidator.ALLOWED_EXTENSIONS.values():
                return None
            
            return mime
            
        except Exception as e:
            logger.error(f"Magic library error: {str(e)}")
            # Fallback to magic numbers if library fails
            return SecureFileValidator._validate_with_magic_numbers(header, expected_mime)

    @staticmethod
    def _validate_with_magic_numbers(header, expected_mime):
        """Fallback validation using magic numbers"""
        logger.info(f"Using magic number validation for {expected_mime}")
        
        # Check if header matches expected MIME type
        if expected_mime in SecureFileValidator.MAGIC_NUMBERS:
            for magic_num in SecureFileValidator.MAGIC_NUMBERS[expected_mime]:
                if header.startswith(magic_num):
                    logger.info(f"Magic number matched for {expected_mime}")
                    return expected_mime
        
        logger.warning(f"Magic number mismatch for {expected_mime}")
        return None

    @staticmethod
    def _validate_image(file):
        """Validate image files"""
        try:
            file.seek(0)
            image = Image.open(file)
            
            # Check dimensions
            width, height = image.size
            if width * height > SecureFileValidator.MAX_IMAGE_PIXELS:
                raise ValidationError(f'Image too large: {width}x{height} pixels. Maximum: 4096x4096')
            
            # Verify image integrity
            image.verify()
            file.seek(0)
            
            logger.info(f"Image validation passed: {width}x{height}")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            raise ValidationError('Invalid or corrupted image file')

    @staticmethod
    def _validate_pdf(file):
        """Validate PDF files"""
        try:
            file.seek(0)
            content = file.read()
            file.seek(0)
            
            # Check for dangerous PDF features
            dangerous_patterns = [
                b'/JavaScript',
                b'/JS',
                b'/OpenAction',
                b'/AA',
            ]
            
            for pattern in dangerous_patterns:
                if pattern in content:
                    logger.warning(f"Dangerous PDF pattern found: {pattern}")
                    raise ValidationError('PDF contains potentially dangerous embedded content')
            
            logger.info("PDF validation passed")
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"PDF validation error: {str(e)}")
            raise ValidationError('Invalid or corrupted PDF file')

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