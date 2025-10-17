from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth import get_user_model
from .serializers import UserCreationSerializer, ChangePasswordSerializer, UserSerializer

User = get_user_model()

class CreateUserView(generics.CreateAPIView):
    """Create new users."""
    queryset = User.objects.all()
    serializer_class = UserCreationSerializer 
    permission_classes = [AllowAny]

class UpdatePasswordView(generics.UpdateAPIView):
    """Update current password only."""
    serializer_class = ChangePasswordSerializer 
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'patch']
    # Limit rate to 2 times a day to prevent malicious actions
    throttle_classes = [UserRateThrottle]
    def get_object(self):
        return self.request.user

class UpdateRetrieveUserInfoView(generics.RetrieveUpdateAPIView):
    """Update and retrieve general information except password."""
    serializer_class = UserSerializer 
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

