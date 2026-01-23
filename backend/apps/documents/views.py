from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
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
        if self.request.user.role == 'admin':
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        OPTIMIZED: Fast upload with minimal validation
        """
        logger.info(f"📤 Document upload started by {request.user.email}")
        
        try:
            # Quick file size check BEFORE processing
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                max_size = 5 * 1024 * 1024  # 5MB
                
                if uploaded_file.size > max_size:
                    return Response(
                        {'error': f'File too large: {uploaded_file.size / 1024 / 1024:.2f}MB. Maximum: 5MB'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                logger.info(f"✓ File size OK: {uploaded_file.size / 1024:.0f}KB")
            
            # Use atomic transaction for safety
            with transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                
                # Save document
                self.perform_create(serializer)
                
                headers = self.get_success_headers(serializer.data)
                logger.info(f"✓ Document uploaded: {serializer.data.get('id')}")
                
                return Response(
                    {
                        'message': 'Document uploaded successfully',
                        'document': serializer.data
                    },
                    status=status.HTTP_201_CREATED,
                    headers=headers
                )
            
        except DjangoValidationError as e:
            logger.error(f"❌ Validation error: {str(e)}")
            error_message = str(e.message) if hasattr(e, 'message') else str(e)
            return Response(
                {'error': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"❌ Upload error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Upload failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """Save document with user"""
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Save error: {str(e)}", exc_info=True)
            raise
    
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
            
            logger.info(f"✓ Document {document.id} verified by {request.user.email}")
            
            serializer = self.get_serializer(document)
            return Response({
                'message': 'Document verified',
                'document': serializer.data
            })
            
        except Exception as e:
            logger.error(f"❌ Verify error: {str(e)}", exc_info=True)
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
            
            logger.info(f"✓ Document {document.id} rejected by {request.user.email}")
            
            serializer = self.get_serializer(document)
            return Response({
                'message': 'Document rejected',
                'document': serializer.data
            })
            
        except Exception as e:
            logger.error(f"❌ Reject error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Rejection failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )