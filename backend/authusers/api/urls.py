from django.urls import path
from .views import CreateUserView, UpdatePasswordView, UpdateRetrieveUserInfoView
from orders.api.views import CustomerOrderViewSet

auth_urlpatterns = [
    # API for account management
    path("register/", CreateUserView.as_view(), name="create-user"),
    path("me/", UpdateRetrieveUserInfoView.as_view(), name="current-user"),
    path("me/password/", UpdatePasswordView.as_view(), name="update-password")
]

# Manual URL patterns for customer orders management
order_urlpatterns = [
    # List and create orders
    path(
        "<str:username>/orders/",
        CustomerOrderViewSet.as_view({"get": "list", "post": "create"}),
        name="user-orders-list"
    ),
    # Order statistics
    path(
        "<str:username>/orders/statistics/",
        CustomerOrderViewSet.as_view({"get": "statistics"}),
        name="user-orders-statistics"
    ),
    # Order detail
    path(
        "<str:username>/orders/<int:pk>/",
        CustomerOrderViewSet.as_view({"get": "retrieve"}),
        name="user-orders-detail"
    ),
    # Cancel order
    path(
        "<str:username>/orders/<int:pk>/cancel/",
        CustomerOrderViewSet.as_view({"post": "cancel"}),
        name="user-orders-cancel"
    ),
]

# Combine all URL patterns
urlpatterns = auth_urlpatterns + order_urlpatterns