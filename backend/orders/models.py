from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.db.models import Q, F, Sum
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from operations.models import RestaurantSetting

# Create your models here.
class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        COMPLETE = "complete", "Complete"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT  # Prevent user deletion if they have orders
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # money
    total = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.07"))
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    gratuity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))

    # times
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        constraints = [
            # Non negative decimals in tax, gratuity and total
            models.CheckConstraint(
                name="non_negative_decimals",
                check=Q(tax_rate__gte=0) & Q(tax_rate__lte=1) &
                      Q(tax_amount__gte=0) &
                      Q(gratuity__gte=0) &
                      Q(total__gte=0) &
                      Q(subtotal__gte=0)
            ),
            # Order completed time must be equal or later than created time
            models.CheckConstraint(
                name="order_completed_after_created",
                check=Q(completed_at__isnull=True) | Q(completed_at__gte=F("created_at"))
            ),
            # Order canceled time must be equal or later than created time
            models.CheckConstraint(
                name="order_canceled_after_create",
                check=Q(canceled_at__isnull=True) | Q(canceled_at__gte=F("created_at")),
            ),
            # Order canceled time and completed time can not exist together
            models.CheckConstraint(
                name="order_not_both_completed_and_canceled",
                check=Q(completed_at__isnull=True) | Q(canceled_at__isnull=True),
            ),
        ]

    def save(self, *args, **kwargs):
        """Override save to ensure the validation runs"""
        if self.pk:
            old = type(self).objects.only("status","completed_at","canceled_at").get(pk=self.pk)

            # -> COMPLETE
            if old.status != self.Status.COMPLETE and self.status == self.Status.COMPLETE and not self.completed_at:
                self.completed_at = timezone.now()
                if self.canceled_at:  # keep your DB constraint happy
                    self.canceled_at = None

            # -> CANCELED
            if old.status != self.Status.CANCELED and self.status == self.Status.CANCELED and not self.canceled_at:
                self.canceled_at = timezone.now()
                if self.completed_at:
                    self.completed_at = None
            else:
                now = timezone.now()
                if self.status == self.Status.COMPLETE and not self.completed_at:
                    self.completed_at = now
                if self.status == self.Status.CANCELED and not self.canceled_at:
                    self.canceled_at = now
                    
        self.full_clean()  # This ensures clean() always runs
        super().save(*args, **kwargs)

    def __str__(self):
        phone = getattr(self.user, "phone", "")
        return f"NO.{self.pk} ({self.status}) ordered by {self.user} ({phone})"

    def clean(self):
        """Validate the order can be created"""
        
        rs = RestaurantSetting.load()
        # Only validate when new order is created
        if self._state.adding:
            creation_time = self.created_at.astimezone(timezone.get_current_timezone()).time()

            # Check if the restaurant is accepting orders
            if not rs.is_accepting_orders:
                raise ValidationError(
                    "Restaurant is not accepting orders."
                )
            
            # Check if the order creation time is not valid
            if ((creation_time < rs.open_time) or 
                (creation_time > rs.last_call) or
                (creation_time >= rs.close_time)):
                raise ValidationError(
                    "Only accept orders created within available business hours"
                )

    @property
    def promised_ready_time(self):
        """Property that returns the promist ready time for an order"""
        rs = RestaurantSetting.load()
        return timezone.localtime(self.created_at) + timedelta(minutes=rs.default_ready_minutes)
    
    @property
    def item_count(self):
        """Return the sum of the items in the order"""
        return self.items.aggregate(counts=Sum("quantity"))["counts"] or 0   
    
    # Change states ========================================================
    def make_order_ready(self):
        """Mark order as ready"""
        if timezone.localtime(timezone.now()) >= self.promised_ready_time:
            self.status = self.Status.READY
            self.save(update_fields=["status"])

    def complete_order(self):
        """Mark order as completed"""
        self.completed_at = timezone.now()
        self.status = self.Status.COMPLETE
        self.save(update_fields=["status", "completed_at"])

    def cancel_order(self, reason):
        """Mark order as canceled"""
        self.canceled_at = timezone.now()
        self.status = self.Status.CANCELED
        self.cancel_reason = reason
        self.save(update_fields=[ "status", "canceled_at", "cancel_reason"])

    # Calculate prices ====================================================
    def calculate_prices(self):
        """Return the prices of the order"""
        decimals = Decimal("0.01")
        self.subtotal = self.items.aggregate(s=Sum("item_total"))["s"] or Decimal("0.00")
        self.subtotal = self.subtotal.quantize(decimals, rounding=ROUND_HALF_UP)

        self.tax_amount = (self.subtotal * self.tax_rate).quantize(decimals, rounding=ROUND_HALF_UP)
        self.gratuity = (self.gratuity or Decimal("0.00")).quantize(decimals, rounding=ROUND_HALF_UP)
        self.total = (self.subtotal + self.tax_amount + self.gratuity).quantize(decimals, rounding=ROUND_HALF_UP)
        self.save(update_fields=["subtotal", "tax_amount", "total", "gratuity"])

    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey("menu.MenuItem", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    # Note for modification on specific items
    note = models.CharField(max_length=200, blank=True, null=True)
    # Snapshot of money history, not using FK
    unit_price = models.DecimalField(max_digits=5, decimal_places=2)
    item_total = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ["order", "item"]
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        constraints = [
            models.CheckConstraint(
                name="order_item_quantity_positive",
                check=Q(quantity__gt=0),
            ),
            models.CheckConstraint(
                name="order_prices",
                check=Q(unit_price__gte=0) & Q(item_total__gte=0)
            )
        ]
    
    def __str__(self):
        return f"{self.quantity} x {self.item.name} @{self.unit_price} = ${self.item_total}"
    
    def save(self, *args, **kwargs):
        q = Decimal("0.01")
        self.item_total = (self.unit_price * self.quantity).quantize(q, rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)