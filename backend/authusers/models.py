from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
class User(AbstractUser):
    """
    Columns: username, is_staff=False, is_superuser=False, date_joined,
    last_login, first_name, last_name, email, phone
    """
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    email = models.EmailField(blank=False, unique=True)
    # Use django-phonenumber-field module to validate us numbers automaically
    phone = PhoneNumberField(blank=True, region="US")

    # Login with email
    USERNAME_FIELD = "email" 
    REQUIRED_FIELDS = ["username"]  

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        """Return user's full name or email prefix."""
        return self.get_full_name() or self.email.split("@")[0]


