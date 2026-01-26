from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    # Include user's full name for convenience
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    # Proper Cloudinary URL for frontend
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['user', 'uploaded_at', 'updated_at']

    def get_file_url(self, obj):
      """Return the Cloudinary URL exactly as uploaded"""
      return obj.file.url if obj.file else None
