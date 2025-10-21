from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MenuItemView, MenuItemPublicView
   
# Router for ViewSets (provides full CRUD)
router = DefaultRouter()
router.register(r'manager/items', MenuItemView, basename='menu-manager')

urlpatterns = [
    path("", include(router.urls)),
    path("items/", MenuItemPublicView.as_view(), name="public-menu")
]