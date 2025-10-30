from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import RestaurantSetting


class RestaurantSettingSerializer(serializers.ModelSerializer):
    """Serializer for restaurant settings"""
    min_ready_minutes = serializers.IntegerField(min_value=0)
    max_ready_minutes = serializers.IntegerField(min_value=0)
    default_ready_minutes = serializers.IntegerField(min_value=0)
    open_time = serializers.TimeField(
        format="%H:%M", 
        input_formats=["%H:%M"]
    )
    close_time = serializers.TimeField(
        format="%H:%M", 
        input_formats=["%H:%M"]
    )

    last_call = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    is_accepting_orders_now = serializers.SerializerMethodField()

    class Meta:
        model = RestaurantSetting
        fields = "__all__"
        read_only_fields = ["id"]

    def get_last_call(self, obj):
        """Get last call time from model"""
        return obj.last_call.strftime("%H:%M") if obj.last_call else None
    
    def get_is_open(self, obj):
        """Check if the restaurant is open"""
        return obj.is_open_now() 
    
    def get_is_accepting_orders_now(self, obj):
        """Check if the restaurant is accepting orders"""
        return obj.is_accepting_orders_now() if obj.is_accepting_orders_now else None

    # Utilize Model + Serializer validation to improve API experience
    def validate(self, attrs):
        """Validate business logic in the serializer level"""
        instance = getattr(self, "instance", None)

        # Get related fields
        min_ready_mins = attrs.get("min_ready_minutes", getattr(instance, "min_ready_minutes", None))
        max_ready_mins = attrs.get("max_ready_minutes", getattr(instance, "max_ready_minutes", None))
        default_ready = attrs.get("default_ready_minutes", getattr(instance, "default_ready_minutes", None))
        open_time = attrs.get("open_time", getattr(instance, "open_time", None))
        close_time = attrs.get("close_time", getattr(instance, "close_time", None))

        # Store errors 
        errors = {}

        # Check min mins <= max_ready_mins
        if (min_ready_mins is not None and
            max_ready_mins is not None and 
            min_ready_mins > max_ready_mins):
            errors["min_ready_minutes"] = "Must be less than or equal to max ready minutes"
            errors["max_ready_minutes"] = "Must be equal or greater than min ready minutes"
        
        # Check open time < close time
        # Assume close time is always before midnight
        if (open_time is not None and
            close_time is not None and 
            not (open_time < close_time)):
            errors["open_time"] = "Must be earlier than the close time"
            errors["close_time"] = "Must be later than the open time"

        # Check default ready time must be in the min-max range
        if (default_ready is not None and 
            min_ready_mins is not None and 
            max_ready_mins is not None):
            if not (min_ready_mins <= default_ready <= max_ready_mins):
                errors["default_ready_minutes"] = "Must be in the min-max range"
        
        # Check the last call 
        if (open_time is not None and 
            close_time is not None and 
            default_ready is not None):
            tz = timezone.get_current_timezone()
            today = timezone.localdate()  
            close_datetime = tz.localize(datetime.combine(today, close_time))
            last_call_datetime = close_datetime - timedelta(minutes=default_ready)
            if last_call_datetime.time() < open_time:
                errors["last_call"] = "Must be between open time and close time"

        
        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs