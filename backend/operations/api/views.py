from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, AllowAny
from .serializers import RestaurantSettingSerializer
from ..models import RestaurantSetting
# Create your views here.

# For admin/staff users to view and change the settings
class RestaurantSettingsView(viewsets.ModelViewSet):
    """Restaurant Settings for admin/staff only"""
    queryset = RestaurantSetting.objects.all()
    serializer_class = RestaurantSettingSerializer
    permission_classes = [IsAdminUser]

# APIview is well suited for checking computed status
class CheckOpenView(APIView):
    """Public endpoint to display the status of openness and order acceptance."""
    permission_classes = [AllowAny]

    def get(self, request):
        restaurant_settings = RestaurantSetting.objects.first()
        if not restaurant_settings:
            return Response({
                "is_open": False,
                "is_accepting_orders": False,
                "message": "The restaurant is still being built."
            })
        
        return Response({
            "is_open": restaurant_settings.is_open_now(),
            "is_accepting_orders": restaurant_settings.is_accepting_orders_now(),
            "last_call": restaurant_settings.last_call.strftime("%H:%M") if restaurant_settings.last_call else None,
        })





