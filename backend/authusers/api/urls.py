from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import CreateUserView, UpdatePasswordView, UpdateRetrieveUserInfoView
from orders.api.views import CustomerOrderViewSet

auth_urlpatterns = [
    # API end points
    path("register/", CreateUserView.as_view(), name="create-user"),
    path("me/", UpdateRetrieveUserInfoView.as_view(), name="current-user"),
    path("me/password/", UpdatePasswordView.as_view(), name="update-password")
]

# Nested router for orders under users
# This will create routes like /users/{username}/orders/
router = DefaultRouter()
# This creates the pattern: /{username}/orders/
users_orders_router = nested_routers.SimpleRouter()
# (?P<username>...) accessible via kwargs["username"]
users_orders_router.register(r'(?P<username>[^/.]+)/orders', CustomerOrderViewSet, basename='user-orders')


urlpatterns = auth_urlpatterns + users_orders_router.urls