from rest_framework.permissions import BasePermission, AllowAny
from rest_framework import viewsets, generics
from .serializers import (
    MenuCategorySerializer,
    AllergenSerializer, 
    ItemAllergenSerializer, 
    MenuItemImageSerializer, 
    MenuItemSerializer,
    MenuItemPublicSerializer
)
from ..models import MenuCategory, MenuItem, Allergen, ItemAllergen

class IsSuperUser(BasePermission):
    """Permission for super user"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
    
class IsSuperUserOrAdmin(BasePermission):
    """Permission for super user and admin user"""
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.is_staff)
    
# Create your views here.
class MenuCategoryView(viewsets.ModelViewSet):
    """Menu category view for super user only"""
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer
    permission_classes = [IsSuperUser]

class AllergenView(viewsets.ModelViewSet):
    """Allergen view for super user only"""
    queryset = Allergen.objects.all()
    serializer_class = AllergenSerializer
    permission_classes = [IsSuperUser]


class ItemAllergenView(viewsets.ModelViewSet):
    """Item allergen view for super user only"""
    queryset = ItemAllergen.objects.all()
    serializer_class = ItemAllergenSerializer
    permission_classes = [IsSuperUser]

class MenuItemImageView(viewsets.ModelViewSet):
    """Only super user can upload the image of menu item"""
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemImageSerializer
    permission_classes = [IsSuperUser]

class MenuItemView(viewsets.ModelViewSet):
    """Only admin and super user can modify the items of menu"""
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsSuperUserOrAdmin]
    ordering = ["name"]

class MenuItemPublicView(generics.ListAPIView):
    """Anyone can view the menu item"""
    permission_classes = [AllowAny]
    serializer_class = MenuItemPublicSerializer
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ["name", "price"]
    ordering = ["name"]
    def get_queryset(self):
        return MenuItem.objects.all().select_related("category").prefetch_related("allergens")