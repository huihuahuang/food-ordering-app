from rest_framework.permissions import BasePermission, AllowAny
from rest_framework import viewsets, generics
from .serializers import MenuItemSerializer, MenuItemPublicSerializer
from ..models import MenuItem
    
class IsSuperUserOrAdmin(BasePermission):
    """Permission for super user and admin user"""
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.is_staff)
    
class MenuItemView(viewsets.ModelViewSet):
    """Only admin and super user can modify the items of menu"""
    queryset = MenuItem.objects.all().select_related("category").prefetch_related("allergens")
    serializer_class = MenuItemSerializer
    permission_classes = [IsSuperUserOrAdmin]
    ordering = ["name"]

class MenuItemPublicView(generics.ListAPIView):
    """Public API for customers to browse available menu items"""
    queryset = MenuItem.objects.all().select_related("category").prefetch_related("allergens")
    permission_classes = [AllowAny]
    serializer_class = MenuItemPublicSerializer