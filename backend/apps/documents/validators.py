import os
from django.core.exceptions import ValidationError
from PIL import Image

# Safe import of python-magic
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class SecureFileValidator:
    """
    Enterprise-grade file upload security validator
    Works with or without python-magic library
    """

    # Allowed file extensions (fallback when magic not available)
    ALLOWED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }

    # Allowed MIME types and their magic numbers
    ALLOWED_TYPES = {
        'image/jpeg': [b'\xFF\xD8\xFF'],
        'image/png': [b'\x89\x50\x4E\x47'],
        'image/gif': [b'GIF87a', b'GIF89a'],
        'application/pdf': [b'%PDF'],
    }

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_PIXELS = 4096 * 4096   # Decompression bomb protection

    @staticmethod
    def validate_file(file):
        """
        Main validation entry point
        Falls back to extension checking if python-magic not available
        """
        # 1. File size check
        if file.size > SecureFileValidator.MAX_FILE_SIZE:
            raise ValidationError(
                'File size exceeds 5MB limit'
            )

        # 2. Read file header
        file.seek(0)
        header = file.read(2048)
        file.seek(0)

        # 3. Validate file extension (always)
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in SecureFileValidator.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f'Unsupported file type. Allowed: PDF, JPEG, PNG, GIF'
            )

        # 4. MIME type detection (if magic available)
        if MAGIC_AVAILABLE:
            try:
                mime = magic.from_buffer(header, mime=True)
            except Exception:
                raise ValidationError('Unable to determine file type')

            if mime not in SecureFileValidator.ALLOWED_TYPES:
                raise ValidationError(
                    'Unsupported file type. Allowed: PDF, JPEG, PNG, GIF'
                )

            # Magic number verification
            valid_magic = False
            for magic_num in SecureFileValidator.ALLOWED_TYPES[mime]:
                if header.startswith(magic_num):
                    valid_magic = True
                    break

            if not valid_magic:
                raise ValidationError(
                    'File content does not match its declared type'
                )
        else:
            # Fallback: Basic magic number check without python-magic
            mime = SecureFileValidator._detect_mime_fallback(header, file_ext)
            if not mime:
                raise ValidationError(
                    'Unable to verify file type. Please ensure file is not corrupted.'
                )

        # 5. Image validation
        if mime and mime.startswith('image/'):
            SecureFileValidator._validate_image(file)

        # 6. PDF validation
        if mime == 'application/pdf':
            SecureFileValidator._validate_pdf(file)

        file.seek(0)
        return file

    @staticmethod
    def _detect_mime_fallback(header, file_ext):
        """
        Fallback MIME detection using magic numbers
        Used when python-magic is not available
        """
        # Check magic numbers
        if header.startswith(b'%PDF'):
            return 'application/pdf'
        elif header.startswith(b'\xFF\xD8\xFF'):
            return 'image/jpeg'
        elif header.startswith(b'\x89\x50\x4E\x47'):
            return 'image/png'
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return 'image/gif'
        
        # If magic number doesn't match, trust extension (less secure)
        return SecureFileValidator.ALLOWED_EXTENSIONS.get(file_ext)

    @staticmethod
    def _validate_image(file):
        """
        Protect against corrupted images & decompression bombs
        """
        try:
            file.seek(0)
            image = Image.open(file)

            width, height = image.size
            if width * height > SecureFileValidator.MAX_IMAGE_PIXELS:
                raise ValidationError(
                    'Image dimensions too large'
                )

            image.verify()
            file.seek(0)

        except Exception:
            raise ValidationError(
                'Invalid or corrupted image file'
            )

    @staticmethod
    def _validate_pdf(file):
        """
        Detect common PDF malware patterns
        """
        file.seek(0)
        content = file.read()
        file.seek(0)

        dangerous_patterns = [
            b'/JavaScript',
            b'/JS',
            b'/OpenAction',
            b'/AA',
        ]

        for pattern in dangerous_patterns:
            if pattern in content:
                raise ValidationError(
                    'PDF contains potentially dangerous embedded content'
                )

    @staticmethod
    def sanitize_filename(filename):
        """
        Prevent path traversal & unsafe filenames
        """
        filename = os.path.basename(filename)

        dangerous_chars = ['..', '/', '\\', '\x00', '\n', '\r']
        for char in dangerous_chars:
            filename = filename.replace(char, '')

        name, ext = os.path.splitext(filename)
        name = name[:100]

        return f"{name}{ext}"