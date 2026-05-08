from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, RawMeasure

class RegisterSerializer(serializers.ModelSerializer):
    taille = serializers.FloatField(write_only=True, required=False)
    activite = serializers.ChoiceField(choices=Profile.ACTIVITE_CHOICES, write_only=True, required=False)
    pathologies = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'taille', 'activite', 'pathologies')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extract profile data
        profile_data = {
            'taille': validated_data.pop('taille', None),
            'activite': validated_data.pop('activite', 'sedentaire'),
            'pathologies': validated_data.pop('pathologies', None)
        }
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile
        Profile.objects.create(user=user, **profile_data)
        
        return user

class RawMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMeasure
        fields = '__all__'

