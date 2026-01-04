from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
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
        serializer.save(user=self.request.user)
    
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
