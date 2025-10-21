from rest_framework import serializers
from ..models import  Allergen, MenuCategory, MenuItem, ItemAllergen


class MenuCategorySerializer(serializers.ModelSerializer):
    """Serializer for menu category model - superuser only"""
    item_count = serializers.SerializerMethodField()
    class Meta:
        model = MenuCategory
        fields = ["id", "name", "sort_order", "item_count"]
        read_only_fields = ["id"]
    
    def get_item_count(self, obj):
        """Return the number of items in each category"""
        # User the related name in menu item (reverse relationship)
        return obj.items.count()
    

class AllergenSerializer(serializers.ModelSerializer):
    """Serializer for allergen model - superuser only"""
    allergen_count = serializers.SerializerMethodField()
    class Meta:
        model = Allergen
        fields = ["id", "name", "allergen_count"]
        read_only_fields = ["id"]
    
    def get_allergen_count(self, obj):
        """Return the number of items in each allergen"""
        return obj.menu_items.count()
    

class MenuItemSerializer(serializers.ModelSerializer):
    """Serializer for menu items"""

    category_id = serializers.IntegerField(read_only=True) 

    # Read with names
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )
    allergens = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field= "name",
    )

    # Write with ids
    category = serializers.PrimaryKeyRelatedField(
        queryset = MenuCategory.objects.all(), write_only=True
    )
    allergen_ids = serializers.PrimaryKeyRelatedField(
        queryset=Allergen.objects.all(), many=True, write_only=True, source="allergens"
    )

    class Meta:
        model = MenuItem
        fields = ["id", "name", "category", "category_id","category_name", "price",
                   "description", "is_available", "allergen_ids", "allergens"]          
        read_only_fields = ["id"]
    
    
class MenuItemImageSerializer(serializers.ModelSerializer):
    """Image Serializer for menu item - superuser only"""
    
    class Meta:
        model = MenuItem
        fields = ["image"]


class ItemAllergenSerializer(serializers.ModelSerializer):
    """Allergens of each item - superuser only"""
    item_name = serializers.CharField(source="item.name")
    allergen_name = serializers.CharField(source="allergen.name")
    class Meta:
        model = ItemAllergen
        fields = ["id", "item", "item_name", "allergen", "allergen_name"]


class MenuItemPublicSerializer(serializers.ModelSerializer):
    """Public serializer for menu items - read-only"""
    category_name = serializers.CharField(source="category.name", read_only=True)
    allergens = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )
    
    class Meta:
        model = MenuItem
        fields = ["id", "name", "category_name", "price", "description", "image", "allergens"]
        read_only_fields = ["id"]