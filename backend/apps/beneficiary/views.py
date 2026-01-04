from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Beneficiary
from .serializers import BeneficiarySerializer

class BeneficiaryViewSet(viewsets.ModelViewSet):
    queryset = Beneficiary.objects.all()
    serializer_class = BeneficiarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'relation', 'verification_status']
    search_fields = ['name', 'phone_number']
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Beneficiary.objects.all()
        return Beneficiary.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        beneficiary = self.get_object()
        beneficiary.verification_status = 'verified'
        beneficiary.save()
        return Response({'message': 'Beneficiary verified successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_deceased(self, request, pk=None):
        beneficiary = self.get_object()
        beneficiary.status = 'deceased'
        beneficiary.save()
        return Response({'message': 'Beneficiary marked as deceased'})

