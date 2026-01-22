from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Document
from .serializers import DocumentSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'status']
    search_fields = ['title']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Document.objects.all()
        return Document.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as e:
            # Re-raise as DRF validation error
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'file': str(e)})
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        document = self.get_object()
        document.status = 'verified'
        document.save()
        return Response({'message': 'Document verified successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        document = self.get_object()
        document.status = 'rejected'
        document.rejection_reason = request.data.get('reason', '')
        document.save()
        return Response({'message': 'Document rejected'})