from rest_framework import serializers
from ..models import  Allergen, MenuCategory, MenuItem


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
        fields = ["id", "name", "category_name", "price", "description", "image", 
                  "is_available", "allergens"]
        read_only_fields = ["id"]