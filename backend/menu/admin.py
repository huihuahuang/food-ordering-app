from django.contrib import admin
from .models import Allergen, MenuCategory, MenuItem, ItemAllergen
# Register your models here.
admin.site.register(Allergen)
admin.site.register(MenuCategory)
admin.site.register(MenuItem)
admin.site.register(ItemAllergen)
