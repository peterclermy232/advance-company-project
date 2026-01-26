from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['user', 'uploaded_at', 'updated_at']
    
    def get_file_url(self, obj):
        """Get the correct Cloudinary URL"""
        if obj.file:
            # Cloudinary returns the full URL automatically
            return obj.file.url
        return None