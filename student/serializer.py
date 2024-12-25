from rest_framework import serializers
from .models import LoginForm

class LoginFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginForm
        fields = [
            '__all__'
        ]
        
