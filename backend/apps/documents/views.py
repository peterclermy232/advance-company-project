from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .models import Document
from .serializers import DocumentSerializer
import logging
import os

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['category', 'status']
    search_fields = ['title']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        ULTRA-FAST UPLOAD
        Only validates: size, extension
        NO content validation
        """
        logger.info(f"📤 Upload start: {request.user.email}")
        
        try:
            # FAST VALIDATION
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            
            # 1. SIZE CHECK (instant)
            MAX_SIZE = 5 * 1024 * 1024
            if file.size > MAX_SIZE:
                logger.warning(f"❌ File too large: {file.size / 1024 / 1024:.2f}MB")
                return Response(
                    {'error': f'File too large: {file.size / 1024 / 1024:.2f}MB. Max: 5MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 2. EXTENSION CHECK (instant)
            ext = os.path.splitext(file.name)[1].lower()
            allowed = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
            if ext not in allowed:
                logger.warning(f"❌ Invalid extension: {ext}")
                return Response(
                    {'error': f'Invalid file type "{ext}". Allowed: PDF, JPEG, PNG, GIF'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"✓ Validation passed: {file.name} ({file.size / 1024:.0f}KB)")
            
            # SAVE (no validation)
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(user=request.user)
                
                logger.info(f"✓ Saved: {serializer.data.get('id')}")
                
                return Response(
                    {
                        'message': 'Document uploaded successfully',
                        'document': serializer.data
                    },
                    status=status.HTTP_201_CREATED
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
            
            logger.info(f"✓ Verified: {document.id}")
            
            return Response({
                'message': 'Document verified',
                'document': self.get_serializer(document).data
            })
            
        except Exception as e:
            logger.error(f"❌ Verify failed: {str(e)}", exc_info=True)
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
            
            logger.info(f"✓ Rejected: {document.id}")
            
            return Response({
                'message': 'Document rejected',
                'document': self.get_serializer(document).data
            })
            
        except Exception as e:
            logger.error(f"❌ Reject failed: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Rejection failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )