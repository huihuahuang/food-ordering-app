from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

# Default is authusers model
User = get_user_model()

# Base serializer - log in
class UserSerializer(serializers.ModelSerializer):
    """User serializer for viewing and updating data (except password)."""
    class Meta:
        model = User
        
        fields = [
            "id", "username", "email",
            "phone", "first_name", "last_name",
            "is_staff",
            "date_joined", "last_login",
        ]

        read_only_fields = ["id", "date_joined", "last_login", "is_staff"]

        extra_kwargs = {
            # Username and email must be required
            "username": {"required": True},
            "email": {"required": True},
        }

    def validate_email(self, value):
        # Clean the input
        value = value.strip()
        
        # Email is immutable - prevent changes
        if self.instance and value != self.instance.email:
            raise serializers.ValidationError("Email cannot be changed once set.")
        
        # Check uniqueness (case-insensitive)
        qs = User.objects.filter(email__iexact=value)

        # If updating an existing instance (Django's ORM)
        if self.instance:
            # Exclude the current user from the uniqueness check
            qs = qs.exclude(pk=self.instance.pk)
        
        # Check if email is already in use
        if qs.exists():
            raise serializers.ValidationError("Email already in use.")
        
        return value

    def validate_username(self, value):
        
        value = value.strip()

        qs = User.objects.filter(username__iexact=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        
        # Ensure uniqueness of username
        if qs.exists():
            raise serializers.ValidationError("Username already in use.")
        
        return value

    def update(self, instance, validated_data):

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

# For creation stage - sign up state
class UserCreationSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    password = serializers.CharField(write_only=True, required=True, allow_blank=False)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "first_name", "last_name", "phone"]
        extra_kwargs = {
            "username": {"required": True},
            "email": {"required": True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        attrs.pop('password_confirm')
        return attrs

    def validate_email(self, value):
        value = value.strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value
    
    def validate_username(self, value):
        
        value = value.strip()

        # Ensure uniqueness of username
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already in use.")
        
        return value
    
    def create(self, validated_data): 
        return User.objects.create_user(**validated_data)

    
# Change password - log in state
class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for updating passwords"""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)
    
    def validate_current_password(self, value):
        user = getattr(self, "instance", None) or self.context.get("request", None).user
        if not user or not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        
        return value
    
    def validate_new_password(self, value):
        # Use built-in password validator
        validate_password(value)
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords don't match."})
        
        validate_password(attrs["new_password"], user=self.instance)
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user