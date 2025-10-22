from datetime import time, datetime, timedelta
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Create your models here.
class RestaurantSetting(models.Model):
    """Restaurant operational settings
    
    Assumptions:
    - Restaurant never operates over midnight (times are same-day)
    - open time < last call time < close time
    - default ready minutes must be between min and max range
    
    """
    is_accepting_orders = models.BooleanField(default=True)

    min_ready_minutes = models.PositiveIntegerField(default=10)
    max_ready_minutes = models.PositiveIntegerField(default=75)
    default_ready_minutes = models.PositiveIntegerField(default=20)

    open_time = models.TimeField(default=time(11, 30))
    close_time = models.TimeField(default=time(21, 30))

    @classmethod
    def load(cls):
        """Always return the only one object"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    class Meta:
        verbose_name = "Restaurant Setting"
        verbose_name_plural = "Restaurant Settings"

    def save(self, *args, **kwargs):
        """Only one record exists"""
        self.pk = 1
        self.full_clean()  
        super().save(*args, **kwargs) 

    def clean(self):
        """Validate business logic"""
        # Validate operational times
        if self.open_time >= self.close_time:
            raise ValidationError(
                "Open time must be before close time (no midnight)"
            )
        
        # Minimum ready times must be less than the maximum ready times
        if self.min_ready_minutes > self.max_ready_minutes:
            raise ValidationError(
                f"Min ready time must be less than the max ready time."
            )
        
        # Validate preparation minutes
        if not (self.min_ready_minutes <= self.default_ready_minutes <= self.max_ready_minutes):
            raise ValidationError(
                f"Default ready minutes ({self.default_ready_minutes}) must be " + 
                f"in the {self.min_ready_minutes} and {self.max_ready_minutes} range."
            )
        
        # Validate that calculated last call won't be before open time
        calculated_last_call = self.calculate_last_call()
        if calculated_last_call < self.open_time:
            raise ValidationError(
                f"Last call time ({calculated_last_call.strftime('%H:%M')}) would be "
                f"before opening time ({self.open_time.strftime('%H:%M')}). "
                f"Reduce default_ready_minutes or extend close_time."
            )

    def __str__(self):
        state = "open" if self.is_accepting_orders else "closed" 
        return f"Restaurant is {state} ({self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')})"
    
    # Business Logic belows =====================================
    def is_accepting_orders_now(self, check_time=None):
        """Check if the restaurant is accepting orders now
        
        The restaurant is supposed to be always closed before midnight.
        """

        # Admin staff terminates the business due to emergency or holidays
        if not self.is_accepting_orders:
            return False
        
        check_time = timezone.localtime().time() if check_time is None else check_time

        if self.open_time <= check_time <= self.last_call:
            return True
        
        return False
    
    def is_open_now(self, check_time=None):
        """Check if the restaurant is currently open"""
        check_time = timezone.localtime().time() if check_time is None else check_time

        return self.open_time <= check_time < self.close_time
    
    def calculate_last_call(self):
        """Calculate the last call time
        
        All orders must be placed before the last call.
        """
        tz = timezone.get_current_timezone()
        today = timezone.localdate()  
        close_datetime = tz.localize(datetime.combine(today, self.close_time))
        last_call_datetime = close_datetime - timedelta(minutes=self.default_ready_minutes)
        return last_call_datetime.time()
    
    @property
    def last_call(self):
        """Property that returns the calculated last call time"""
        return self.calculate_last_call()
    

          