from django.contrib import admin
from .models import Booking, Rating,Payment

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'tourist', 'agency', 'package', 'guide', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at', 'travel_date')
    search_fields = ('tourist__full_name', 'agency__name', 'package__title', 'guide__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'travel_date'
    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']
    
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} bookings were marked as confirmed.')
    mark_confirmed.short_description = "Mark selected bookings as confirmed"
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} bookings were marked as completed.')
    mark_completed.short_description = "Mark selected bookings as completed"
    
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} bookings were marked as cancelled.')
    mark_cancelled.short_description = "Mark selected bookings as cancelled"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tourist', 'agency', 'package', 'guide')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('tourist', 'rating_type', 'rating', 'get_target', 'created_at')
    list_filter = ('rating_type', 'rating', 'created_at')
    search_fields = ('tourist__full_name', 'review', 'guide__name', 'agency__name', 'package__title')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_target(self, obj):
        if obj.rating_type == 'guide' and obj.guide:
            return obj.guide.name
        elif obj.rating_type == 'agency' and obj.agency:
            return obj.agency.name
        elif obj.rating_type == 'package' and obj.package:
            return obj.package.title
        return '-'
    get_target.short_description = 'Target'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'booking', 'amount', 'status')
    list_filter = ('status',)
    search_fields = ('transaction_id', 'booking__tourist__full_name', 'booking__agency__name')
     