from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """
    Standardized API response format with built-in messages for frontend toast alerts
    
    Response format:
    {
        "success": true/false,
        "message": "User-friendly message for toast",
        "toast_type": "success/error/warning/info",
        "data": {...},  # Optional
        "errors": {...}  # Optional, for validation errors
    }
    """
    
    @staticmethod
    def success(message, data=None, status_code=status.HTTP_200_OK):
        """
        Success response with green toast message
        
        Args:
            message: User-friendly success message
            data: Response data (optional)
            status_code: HTTP status code
        """
        response_data = {
            "success": True,
            "message": message,
            "toast_type": "success"
        }
        
        if data is not None:
            response_data["data"] = data
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Error response with red toast message
        
        Args:
            message: User-friendly error message
            errors: Detailed error dict (optional)
            status_code: HTTP status code
        """
        response_data = {
            "success": False,
            "message": message,
            "toast_type": "error"
        }
        
        if errors is not None:
            response_data["errors"] = errors
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def warning(message, data=None, status_code=status.HTTP_200_OK):
        """
        Warning response with orange toast message
        
        Args:
            message: User-friendly warning message
            data: Response data (optional)
            status_code: HTTP status code
        """
        response_data = {
            "success": True,
            "message": message,
            "toast_type": "warning"
        }
        
        if data is not None:
            response_data["data"] = data
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def info(message, data=None, status_code=status.HTTP_200_OK):
        """
        Info response with blue toast message
        
        Args:
            message: User-friendly info message
            data: Response data (optional)
            status_code: HTTP status code
        """
        response_data = {
            "success": True,
            "message": message,
            "toast_type": "info"
        }
        
        if data is not None:
            response_data["data"] = data
        
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(message, data=None):
        """
        Resource created response (201)
        
        Args:
            message: Success message
            data: Created resource data
        """
        return APIResponse.success(message, data, status.HTTP_201_CREATED)
    
    @staticmethod
    def no_content(message="Operation completed successfully"):
        """
        No content response (204) - used for deletions
        
        Args:
            message: Success message
        """
        return APIResponse.success(message, status_code=status.HTTP_204_NO_CONTENT)
    
    @staticmethod
    def unauthorized(message="You are not authorized to perform this action"):
        """
        Unauthorized response (401)
        
        Args:
            message: Error message
        """
        return APIResponse.error(message, status_code=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def forbidden(message="You do not have permission to access this resource"):
        """
        Forbidden response (403)
        
        Args:
            message: Error message
        """
        return APIResponse.error(message, status_code=status.HTTP_403_FORBIDDEN)
    
    @staticmethod
    def not_found(message="The requested resource was not found"):
        """
        Not found response (404)
        
        Args:
            message: Error message
        """
        return APIResponse.error(message, status_code=status.HTTP_404_NOT_FOUND)
    
    @staticmethod
    def validation_error(message, errors):
        """
        Validation error response (400)
        
        Args:
            message: General error message
            errors: Dict of field-specific errors
        """
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def server_error(message="An unexpected error occurred. Please try again later"):
        """
        Server error response (500)
        
        Args:
            message: Error message
        """
        return APIResponse.error(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Message Constants
class Messages:
    """Centralized user-facing messages"""
    
    # Authentication
    AUTH_SUCCESS = "Welcome back! Login successful."
    AUTH_FAILED = "Invalid email or password. Please try again."
    AUTH_LOCKED = "Your account has been locked due to multiple failed login attempts."
    AUTH_INACTIVE = "Your account is inactive. Please contact support."
    AUTH_VERIFY_EMAIL = "Please verify your email address before logging in."
    
    LOGOUT_SUCCESS = "You have been logged out successfully."
    
    REGISTER_SUCCESS = "Registration successful! Please check your email to verify your account."
    REGISTER_FAILED = "Registration failed. Please check your information and try again."
    
    # Password
    PASSWORD_CHANGED = "Your password has been changed successfully."
    PASSWORD_RESET_SENT = "Password reset instructions have been sent to your email."
    PASSWORD_RESET_SUCCESS = "Your password has been reset successfully."
    PASSWORD_WEAK = "Password is too weak. Please use a stronger password."
    PASSWORD_MISMATCH = "Passwords do not match."
    
    # Email Verification
    EMAIL_VERIFIED = "Email verified successfully! You can now log in."
    EMAIL_VERIFICATION_SENT = "Verification email has been sent to your address."
    EMAIL_VERIFICATION_FAILED = "Email verification failed. The link may have expired."
    
    # 2FA
    TWO_FA_ENABLED = "Two-factor authentication has been enabled for your account."
    TWO_FA_DISABLED = "Two-factor authentication has been disabled."
    TWO_FA_INVALID = "Invalid verification code. Please try again."
    TWO_FA_REQUIRED = "Two-factor authentication code required."
    
    # Profile
    PROFILE_UPDATED = "Your profile has been updated successfully."
    PROFILE_PHOTO_UPLOADED = "Profile photo uploaded successfully."
    PROFILE_PHOTO_DELETED = "Profile photo deleted successfully."
    
    # Deposits
    DEPOSIT_CREATED = "Deposit request submitted successfully and pending approval."
    DEPOSIT_APPROVED = "Deposit has been approved and credited to your account."
    DEPOSIT_REJECTED = "Deposit has been rejected."
    DEPOSIT_FAILED = "Deposit transaction failed. Please try again."
    DEPOSIT_LIMIT_REACHED = "You have already made your monthly deposit. You can deposit once per month."
    
    # Applications
    APPLICATION_SUBMITTED = "Application submitted successfully and is under review."
    APPLICATION_APPROVED = "Your application has been approved."
    APPLICATION_REJECTED = "Your application has been rejected."
    
    # Documents
    DOCUMENT_UPLOADED = "Document uploaded successfully and pending verification."
    DOCUMENT_VERIFIED = "Document has been verified successfully."
    DOCUMENT_REJECTED = "Document has been rejected."
    
    # Beneficiaries
    BENEFICIARY_ADDED = "Beneficiary added successfully."
    BENEFICIARY_UPDATED = "Beneficiary information updated successfully."
    BENEFICIARY_DELETED = "Beneficiary removed successfully."
    BENEFICIARY_VERIFIED = "Beneficiary has been verified."
    BENEFICIARY_VERIFIED = "Beneficiary has been verified and approved."
    BENEFICIARY_REJECTED = "Beneficiary has been rejected."
    
    # Notifications
    NOTIFICATIONS_MARKED_READ = "All notifications marked as read."
    NOTIFICATIONS_CLEARED = "Read notifications cleared successfully."
    
    # Generic
    SUCCESS = "Operation completed successfully."
    ERROR = "An error occurred. Please try again."
    VALIDATION_ERROR = "Please check your input and try again."
    UNAUTHORIZED = "You are not authorized to perform this action."
    NOT_FOUND = "The requested resource was not found."
    SERVER_ERROR = "An unexpected error occurred. Please try again later."