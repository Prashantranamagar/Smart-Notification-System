# api/serializers.py
from .models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from app_notification.signals import jwt_logged_in
import logging
import re

logger = logging.getLogger(__name__)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    phone_number = serializers.CharField(required=True, max_length=15)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "phone_number")

    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate_phone_number(self, value):
        """Validate Nepali phone number format (length 10, starts with 98/97/96 etc.)"""
        if not re.fullmatch(r"9[6-9]\d{8}", value):
            raise serializers.ValidationError("Enter a valid 10-digit Nepali phone number.")
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number is already registered.")
        return value

    def validate_password(self, value):
        """Ensure password is strong enough"""
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not re.search(r"[^\w\s]", value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            phone_number=validated_data["phone_number"],
        )
        logger.info(f"User created successfully: {user.username}")
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Trigger user_logged_in manually
        request = self.context.get("request")
        jwt_logged_in.send(sender=self.user.__class__, request=request, user=self.user)

        return data
