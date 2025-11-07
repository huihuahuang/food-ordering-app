from rest_framework import serializers
from decimal import Decimal
from ..models import Order, OrderItem

class OrderItemWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating order items"""
    class Meta:
        model = OrderItem
        fields = [
            "item",  # FK to MenuItem - accepts ID
            "quantity",
            "unit_price",
            "note"
        ]

    def validate_item(self, value):
        """Validate item's availability"""
        # value = entire menu item object, DRF automatically maps it out
        if not value.is_available:
            raise serializers.ValidationError(
                    f"Item '{value.name}' is currently not available"
                )
        return value
    
    def validate_quantity(self, value):
        """Validate item's quantity"""
        # value = quantity
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_unit_price(self, value):
        """Validate item's unit price"""
        # value = unit price
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than 0")
        return value
    
    def validate(self, attrs):
        """Validate with a cross-field approach """
        # In this case, attrs is dict, not an object
        menu_item = attrs.get("item")
        unit_price = attrs.get("unit_price")

        if menu_item and unit_price:
            if unit_price != menu_item.price:
                raise serializers.ValidationError({
                    'unit_price': f"Price mismatch. Current price is {menu_item.price}. " + 
                    "Please refresh and try again."
                })
            
        return attrs
    

class OrderItemReadSerializer(serializers.ModelSerializer):
    """Serializer for reading the order items"""
    item_id = serializers.IntegerField(source='item.id', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item_id",
            "item_name",
            "quantity",
            "note",
            "unit_price",
            "item_total",
        ]
        read_only_fields = fields

# ============== Order ==============
class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new orders"""
    items = OrderItemWriteSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            "id",
            "items",
            "gratuity",
            "status",
            "subtotal",
            "tax_rate",
            "tax_amount",
            "total",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "subtotal",
            "tax_amount",
            "total",
            "created_at",
        ]

    def validate_items(self, value):
        """Ensure the items of an order must be greater than zero"""
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")

        return value
    
    def validate_gratuity(self, value):
        """Ensure the gratuity must be non-negative"""
        if value < 0:
            raise serializers.ValidationError("Gratuity must be non-negative")
        
        return value
    
    def create(self, validated_data):
        """Create order with items"""
        items_data = validated_data.pop("items")

        # Create the order with the authenticated user
        order = Order.objects.create(
            user=self.context["request"].user,
            gratuity=validated_data.get("gratuity", Decimal("0.00"))
        )

        # Create the order items with price snapshots from the frontend
        for order_item in items_data:
            OrderItem.objects.create(
                order=order,
                item=order_item["item"],
                quantity=order_item["quantity"],
                note=order_item.get("note", ""),
                unit_price=order_item["unit_price"]
            )
        # Calculate related prices
        order.calculate_prices()

        # Store it into related database
        order.refresh_from_db()

        return order

class OrderSimpliedSerializer(serializers.ModelSerializer):
    """Serializer for simplied view"""
    # This simplified view is for both staff and end users
    user_name = serializers.CharField(source="user", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    promised_ready_time = serializers.DateTimeField(
        read_only=True,
        format="%Y-%m-%d %H:%M"
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "user_name",
            "user_phone",
            "item_count",
            "status",
            "total",
            "created_at",
            "promised_ready_time"
        ]
        read_only_fields = fields
    
class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view"""
    items = OrderItemReadSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user", read_only=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    promised_ready_time = serializers.DateTimeField(
        read_only=True,
        format="%Y-%m-%d %H:%M"
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "user_phone",
            "user_name",
            "status",
            "items",
            "item_count",
            "subtotal",
            "tax_rate",
            "tax_amount",
            "gratuity",
            "total",
            "created_at",
            "promised_ready_time",
            "completed_at",
            "canceled_at",
            "cancel_reason",
        ]
        read_only_fields = fields
            
class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for the staff to update the order states

    Status includes "Ready", "Complete", "Cancel"
    """
    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "completed_at",
            "canceled_at",
            "cancel_reason"
        ]
        read_only_fields = ["id", "completed_at", "canceled_at", "cancel_reason"]

    def validate_status(self, value):
        instance = self.instance
        current_status = instance.status

        # The validated transactions
        # Pending => Ready or Cancel
        # Ready => Complete or Cancel
        # Complete => no further status
        # Cancel => no further status

        valid_transactions = {
            Order.Status.PENDING: [Order.Status.READY, Order.Status.CANCELED],
            Order.Status.READY: [Order.Status.COMPLETE, Order.Status.CANCELED],
            Order.Status.COMPLETE: [],
            Order.Status.CANCELED: []
        }

        if value not in valid_transactions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'"
            )
        
        return value
    
    def update(self, instance, validated_data):
        """Update status with order model methods"""

        new_status = validated_data.get("status")

        if new_status == Order.Status.READY:
            instance.make_order_ready()
        elif new_status == Order.Status.COMPLETE:
            instance.complete_order()
        elif new_status == Order.Status.CANCELED:
            reason = self.context.get("cancel_reason", "Canceled by staff")
            instance.cancel_order(reason)

        return instance
    

class OrderCanceledByCustomerSerializer(serializers.Serializer):
    """Serializer for customers to cancel order"""
    cancel_reason = serializers.CharField(
        max_length=200,
        required=True,
        help_text="Reason to cancel this order"
    )

    def validate_cancel_reason(self, value):
        """Ensure the cancel reason is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Cancel reason cannot be empty")
        
        return value.strip()
    
    def save(self):
        """Cancel order by customer"""
        order = self.context["order"]

        if order.status not in [Order.Status.PENDING, Order.Status.READY]:
            raise serializers.ValidationError(
                f"Cannot cancel order with status: {order.status}"
            )
        
        order.cancel_order(self.validated_data["cancel_reason"])

        return order