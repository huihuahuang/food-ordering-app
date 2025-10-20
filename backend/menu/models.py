from django.db import models

class MenuCategory(models.Model):
    name = models.CharField(max_length=30, unique=True)
    sort_order = models.SmallIntegerField(unique=True)

    class Meta:  
        ordering = ["sort_order"]
        db_table = "menu_category"       
        verbose_name = "Menu Category"   
        verbose_name_plural = "Menu Categories"

    def __str__(self):
        return f"{self.name} ({self.sort_order})"
    
class Allergen(models.Model):
    """Allergen list"""
    name = models.CharField(max_length=20, unique=True)
    class Meta:
        db_table = "allergen"
        verbose_name = "Allergen"
        verbose_name_plural = "Allergens"

    def __str__(self):
        return self.name
    
class MenuItem(models.Model):
    """Items on menu"""
    name = models.CharField(max_length=50)
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE, 
        blank=False,
        related_name="items"   # Custom name for reverse relationship
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.CharField(max_length=300)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(blank=True, null=True)   # Add default image later
    allergens = models.ManyToManyField(
        Allergen,
        through="ItemAllergen",
        related_name="menu_items"
    )
    class Meta:
        db_table = "menu_item"
        unique_together = ["name", "category"]  # Composite key
        verbose_name = "Menu Item"   
        verbose_name_plural = "Menu Items"

    def __str__(self):
        return f"{self.name} - {self.category.name}"


class ItemAllergen(models.Model):
    """Allegern list for all items."""
    item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        blank=False,
        related_name="item"
    )
    allergen = models.ForeignKey(
        Allergen,
        on_delete=models.CASCADE,
        blank=False,
        related_name="allergen"
    )
    class Meta:
        db_table = "item_allergen"
        unique_together = ["item", "allergen"]  # Composite key
        verbose_name = "Item Allergen"
        verbose_name_plural = "Item Allergens"

    def __str__(self):
        return f"{self.item.name} - {self.allergen.name}"