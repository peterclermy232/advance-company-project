from rest_framework import serializers
from .models import Application, ApplicationActivity

class ApplicationActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = ApplicationActivity
        fields = '__all__'

class ApplicationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    activities = ApplicationActivitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = [
            'user', 'status', 'reviewed_by', 'reviewed_at',
            'approved_at', 'created_at', 'updated_at'
        ]
