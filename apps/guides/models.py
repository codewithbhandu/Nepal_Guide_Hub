from django.db import models
from apps.accounts.models import Agency

class Guide(models.Model):
    LANGUAGES = (
        ('en', 'English'),
        ('ne', 'Nepali'),
        ('hi', 'Hindi'),
        ('zh', 'Chinese'),
        ('fr', 'French'),
        ('de', 'German'),
        ('ja', 'Japanese'),
        ('ko', 'Korean'),
    )
    
    SPECIALTIES = (
        ('trekking', 'Trekking'),
        ('mountaineering', 'Mountaineering'),
        ('cultural', 'Cultural Tours'),
        ('wildlife', 'Wildlife Safari'),
        ('adventure', 'Adventure Sports'),
        ('pilgrimage', 'Pilgrimage Tours'),
        ('photography', 'Photography Tours'),
    )

    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='guides')
    name = models.CharField(max_length=100)
    bio = models.TextField()
    experience_years = models.IntegerField()
    languages = models.JSONField(default=list)  # Store multiple languages
    specialties = models.JSONField(default=list)  # Store multiple specialties
    profile_picture = models.ImageField(upload_to='guides/', null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_ratings = models.IntegerField(default=0)
    places_covered = models.TextField(help_text="Comma-separated list of places")
    certifications = models.TextField(blank=True, help_text="Guide certifications and training")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.agency.name}"

    def get_languages_display(self):
        lang_dict = dict(self.LANGUAGES)
        return [lang_dict.get(lang, lang) for lang in self.languages]

    def get_specialties_display(self):
        spec_dict = dict(self.SPECIALTIES)
        return [spec_dict.get(spec, spec) for spec in self.specialties]

    def update_rating(self):
        from apps.bookings.models import Rating
        ratings = Rating.objects.filter(guide=self, rating_type='guide')
        if ratings.exists():
            self.total_ratings = ratings.count()
            self.rating = sum(r.rating for r in ratings) / self.total_ratings
            self.save(update_fields=['rating', 'total_ratings'])
