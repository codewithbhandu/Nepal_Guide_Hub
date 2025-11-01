from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import Tourist, Agency
from apps.guides.models import Guide
from apps.packages.models import Package

class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE, related_name='bookings')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True, blank=True)
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, null=True, blank=True)
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE)
    
    booking_date = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    number_of_people = models.IntegerField(validators=[MinValueValidator(1)])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} - {self.tourist.full_name}"

    @property
    def remaining_amount(self):
        return self.total_amount - self.advance_amount

class Rating(models.Model):
    RATING_TYPES = (
        ('guide', 'Guide'),
        ('agency', 'Agency'),
        ('package', 'Package'),
    )
    
    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE, related_name='ratings')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    rating_type = models.CharField(max_length=10, choices=RATING_TYPES)
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, null=True, blank=True, related_name='ratings')
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, null=True, blank=True, related_name='ratings')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, null=True, blank=True, related_name='ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ['tourist', 'guide'],
            ['tourist', 'agency'],
            ['tourist', 'package'],
        ]

    def __str__(self):
        return f"{self.rating}★ - {self.get_rating_type_display()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update related model ratings
        if self.rating_type == 'guide' and self.guide:
            self.guide.update_rating()
        elif self.rating_type == 'agency' and self.agency:
            self.agency.update_rating()

 
class Payment(models.Model):
    status_choices = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    product_code = models.CharField(max_length=100, default='EPAYTEST')
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
