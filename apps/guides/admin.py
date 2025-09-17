from django.contrib import admin
from .models import Guide

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'agency', 'experience_years', 'daily_rate', 'rating', 'is_available')
    list_filter = ('is_available', 'agency__is_verified', 'experience_years')
    search_fields = ('name', 'agency__name', 'places_covered')
    readonly_fields = ('rating', 'total_ratings', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agency')