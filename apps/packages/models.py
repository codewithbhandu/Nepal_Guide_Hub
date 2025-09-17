from django.db import models
from apps.accounts.models import Agency

class Package(models.Model):
    PACKAGE_TYPES = (
        ('trekking', 'Trekking'),
        ('cultural', 'Cultural Tour'),
        ('adventure', 'Adventure'),
        ('wildlife', 'Wildlife Safari'),
        ('pilgrimage', 'Pilgrimage'),
        ('mountaineering', 'Mountaineering'),
        ('photography', 'Photography Tour'),
        ('luxury', 'Luxury Tour'),
    )
    
    DIFFICULTY_LEVELS = (
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('difficult', 'Difficult'),
        ('extreme', 'Extreme')
    )

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='packages')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    duration_days = models.IntegerField()
    max_people = models.IntegerField()
    min_people = models.IntegerField(default=1)
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    included_services = models.TextField()
    excluded_services = models.TextField()
    itinerary = models.JSONField(default=dict)  # Day-wise itinerary
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    best_season = models.CharField(max_length=100)
    altitude = models.IntegerField(null=True, blank=True, help_text="Maximum altitude in meters")
    equipment_provided = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.agency.name}"

    def get_main_image(self):
        return self.images.first()

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

class PackageImage(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='packages/')
    caption = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main', 'created_at']

    def __str__(self):
        return f"{self.package.title} - Image"
