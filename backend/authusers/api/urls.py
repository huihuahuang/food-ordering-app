from django.urls import path
from .views import CreateUserView, UpdatePasswordView, UpdateRetrieveUserInfoView

urlpatterns = [
    # API end points
    path("register/", CreateUserView.as_view(), name="create-user"),
    path("me/", UpdateRetrieveUserInfoView.as_view(), name="current-user"),
    path("me/password/", UpdatePasswordView.as_view(), name="update-password")
]