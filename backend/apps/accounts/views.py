import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, BiometricDevice
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    BiometricRegistrationSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
)
from .emails import send_verification_email
from .utils.biometric_verification import BiometricVerifier

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Cache helpers (safe for Redis downtime)
# -------------------------------------------------------------------

def safe_cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception as e:
        logger.warning(f"Cache get failed [{key}]: {e}")
        return default


def safe_cache_set(key, value, timeout=None):
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed [{key}]: {e}")
        return False


def safe_cache_delete(key):
    try:
        cache.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed [{key}]: {e}")
        return False


# -------------------------------------------------------------------
# User ViewSet
# -------------------------------------------------------------------

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # ---------------------------------------------------------------
    # Permissions (THIS IS THE ONLY PLACE WE CHECK self.action)
    # ---------------------------------------------------------------
    def get_permissions(self):
        public_actions = [
            "register",
            "login",
            "verify_email",
            "resend_verification",
            "forgot_password",
            "reset_password_confirm",
            "verify_2fa",
            "biometric_challenge",
            "biometric_login",
        ]

        if self.action in public_actions:
            return [AllowAny()]

        return [IsAuthenticated()]

    # ---------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    # ---------------------------------------------------------------
    # AUTH / REGISTRATION
    # ---------------------------------------------------------------

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST"))
    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save(is_active=True, email_verified=False)

        try:
            send_verification_email(user)
            message = "Registration successful. Check your email to verify."
        except Exception:
            message = "Registration successful."

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": message,
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def verify_email(self, request):
        token = request.data.get("token")
        email = request.data.get("email")

        if not token or not email:
            return Response(
                {"error": "Token and email required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user.email_verified:
            return Response({"message": "Email already verified"})

        if not user.verify_email(token):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"message": "Email verified successfully"})

    @action(detail=False, methods=["post"])
    def resend_verification(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            if not user.email_verified:
                send_verification_email(user)
        except User.DoesNotExist:
            pass

        return Response(
            {"message": "If the email exists, a verification link was sent"}
        )

    # ---------------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------------

    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST"))
    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        if not user.is_active:
            return Response(
                {"error": "Account disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2FA flow
        if user.two_factor_enabled:
            temp_token = secrets.token_urlsafe(32)
            if not safe_cache_set(f"2fa_{temp_token}", user.id, timeout=300):
                return Response(
                    {"error": "2FA service unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            return Response(
                {
                    "requires_2fa": True,
                    "temp_token": temp_token,
                    "email": user.email,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )

    # ---------------------------------------------------------------
    # 2FA
    # ---------------------------------------------------------------

    @action(detail=False, methods=["post"])
    def enable_2fa(self, request):
        secret = request.user.generate_2fa_secret()
        return Response(
            {
                "secret": secret,
                "qr_code": request.user.get_2fa_qr_code(),
            }
        )

    @action(detail=False, methods=["post"])
    def confirm_2fa(self, request):
        serializer = TwoFactorSetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.verify_2fa_code(serializer.validated_data["code"]):
            return Response(
                {"error": "Invalid code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.two_factor_enabled = True
        backup_codes = request.user.generate_backup_codes()
        request.user.save()

        return Response(
            {
                "message": "2FA enabled",
                "backup_codes": backup_codes,
            }
        )

    @method_decorator(ratelimit(key="ip", rate="5/5m", method="POST"))
    @action(detail=False, methods=["post"])
    def verify_2fa(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        temp_token = request.data.get("temp_token")
        user_id = safe_cache_get(f"2fa_{temp_token}")

        if not user_id:
            return Response(
                {"error": "Session expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = User.objects.get(
                id=user_id,
                email=serializer.validated_data["email"],
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if serializer.validated_data.get("is_backup_code"):
            valid = user.verify_backup_code(serializer.validated_data["code"])
        else:
            valid = user.verify_2fa_code(serializer.validated_data["code"])

        if not valid:
            return Response(
                {"error": "Invalid code"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        safe_cache_delete(f"2fa_{temp_token}")

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            }
        )

    # ---------------------------------------------------------------
    # PASSWORD RESET
    # ---------------------------------------------------------------

    @method_decorator(ratelimit(key="ip", rate="3/h", method="POST"))
    @action(detail=False, methods=["post"])
    def forgot_password(self, request):
        email = request.data.get("email", "").lower()

        if not email:
            return Response(
                {"error": "Email required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email, is_active=True)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = (
                f"{settings.FRONTEND_URL}/reset-password"
                f"?uid={uid}&token={token}"
            )

            send_mail(
                "Password Reset",
                f"Reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
        except User.DoesNotExist:
            pass

        return Response(
            {
                "message": "If the email exists, a reset link was sent"
            }
        )

    @action(detail=False, methods=["post"])
    def reset_password_confirm(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("new_password")

        if not all([uid, token, password]):
            return Response(
                {"error": "Missing fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response(
                {"error": "Invalid reset link"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validate_password(password, user)
        user.set_password(password)
        user.save()

        return Response({"message": "Password reset successful"})
