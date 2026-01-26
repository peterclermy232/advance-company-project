from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Document
from .serializers import DocumentSerializer
import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['category', 'status']
    search_fields = ['title']
    
    def get_queryset(self):
        """Filter documents based on user role"""
        if self.request.user.role == 'admin':
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Upload document with validation"""
        logger.info(f"📤 Upload request from: {request.user.email}")
        
        try:
            # Check if file is provided
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            logger.info(f"Processing file: {file.name} ({file.size / 1024:.1f}KB)")
            
            # Validate file (size, extension, content)
            from .validators import SecureFileValidator
            try:
                SecureFileValidator.validate_file(file)
            except ValidationError as e:
                logger.warning(f"❌ Validation failed: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save document
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                document = serializer.save(user=request.user)
                
                logger.info(f"✅ Document uploaded: ID={document.id}, File={document.file.name}")
                
                return Response(
                    {
                        'message': 'Document uploaded successfully',
                        'document': serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            
        except ValidationError as e:
            logger.warning(f"❌ Validation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"❌ Upload failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Upload failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Admin: verify document"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            document = self.get_object()
            document.status = 'verified'
            document.save()
            
            logger.info(f"✅ Document verified: {document.id} by {request.user.email}")
            
            return Response({
                'message': 'Document verified successfully',
                'document': self.get_serializer(document).data
            })
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Verification failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Admin: reject document"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            document = self.get_object()
            document.status = 'rejected'
            document.rejection_reason = request.data.get('reason', 'No reason provided')
            document.save()
            
            logger.info(f"✅ Document rejected: {document.id} by {request.user.email}")
            
            return Response({
                'message': 'Document rejected',
                'document': self.get_serializer(document).data
            })
            
        except Exception as e:
            logger.error(f"❌ Rejection failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Rejection failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )