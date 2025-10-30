from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RestaurantSettingsView, CheckOpenView
   
# Router for ViewSets (provides full CRUD)
router = DefaultRouter()
router.register(r'manager/settings', RestaurantSettingsView, basename='settings-manager')

urlpatterns = [
    path("", include(router.urls)),
    path("status/", CheckOpenView.as_view(), name="restaurant-status")
]