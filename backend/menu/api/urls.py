from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MenuCategoryView,
    AllergenView,
    ItemAllergenView,
    MenuItemImageView,
    MenuItemView,
    MenuItemPublicView
)
# Router for ViewSets (provides full CRUD)
router = DefaultRouter()
router.register(r'admin/categories', MenuCategoryView, basename='menu-categories')
router.register(r'admin/allergens', AllergenView, basename='allergens')
router.register(r'admin/item-allergens', ItemAllergenView, basename='item-allergens')
router.register(r'admin/images', MenuItemImageView, basename='item-images')
router.register(r'manager/menu-items', MenuItemView, basename='menu-manager')

urlpatterns = [
    path("", include(router.urls)),
    path("public-menu/", MenuItemPublicView.as_view(), name="menu")
]