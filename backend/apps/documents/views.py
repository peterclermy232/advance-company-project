from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Document
from .serializers import DocumentSerializer
import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Handle file uploads
    filterset_fields = ['category', 'status']
    search_fields = ['title']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create to handle file validation errors properly"""
        try:
            logger.info(f"Document upload started by user {request.user.email}")
            logger.info(f"Request data: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            self.perform_create(serializer)
            
            headers = self.get_success_headers(serializer.data)
            logger.info(f"Document uploaded successfully: {serializer.data.get('id')}")
            
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
            
        except DjangoValidationError as e:
            logger.error(f"Validation error during document upload: {str(e)}")
            return Response(
                {'error': str(e.message) if hasattr(e, 'message') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error during document upload: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to upload document. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """Save the document with the current user"""
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as e:
            # Re-raise to be caught by create method
            raise
        except Exception as e:
            logger.error(f"Error in perform_create: {str(e)}", exc_info=True)
            raise
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Admin endpoint to verify a document"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can verify documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            document = self.get_object()
            document.status = 'verified'
            document.save()
            
            logger.info(f"Document {document.id} verified by admin {request.user.email}")
            
            serializer = self.get_serializer(document)
            return Response({
                'message': 'Document verified successfully',
                'document': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error verifying document: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to verify document'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Admin endpoint to reject a document"""
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can reject documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            document = self.get_object()
            document.status = 'rejected'
            document.rejection_reason = request.data.get('reason', 'No reason provided')
            document.save()
            
            logger.info(f"Document {document.id} rejected by admin {request.user.email}")
            
            serializer = self.get_serializer(document)
            return Response({
                'message': 'Document rejected',
                'document': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error rejecting document: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to reject document'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )