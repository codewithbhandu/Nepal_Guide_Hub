from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Tourist, Agency, VerificationRequest

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone')}),
    )

@admin.register(Tourist)
class TouristAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nationality', 'user__email', 'created_at')
    list_filter = ('nationality', 'created_at')
    search_fields = ('full_name', 'user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def user__email(self, obj):
        return obj.user.email
    user__email.short_description = 'Email'

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number', 'is_verified', 'rating', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('name', 'license_number', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'rating', 'total_ratings')
    actions = ['verify_agencies', 'unverify_agencies']
    
    def verify_agencies(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_verified=True, verified_at=timezone.now(), verified_by=request.user)
        self.message_user(request, f'{updated} agencies were successfully verified.')
    verify_agencies.short_description = "Verify selected agencies"
    
    def unverify_agencies(self, request, queryset):
        updated = queryset.update(is_verified=False, verified_at=None, verified_by=None)
        self.message_user(request, f'{updated} agencies were unverified.')
    unverify_agencies.short_description = "Unverify selected agencies"

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('agency', 'requested_by', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('agency__name', 'requested_by__username', 'agency__license_number')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        
        approved_count = 0
        for verification_request in queryset.filter(status='pending'):
            # Update the verification request
            verification_request.status = 'approved'
            verification_request.reviewed_by = request.user
            verification_request.reviewed_at = timezone.now()
            verification_request.save()
            
            # Update the agency
            agency = verification_request.agency
            agency.is_verified = True
            agency.verified_at = timezone.now()
            agency.verified_by = request.user
            agency.save()
            
            approved_count += 1
            
        self.message_user(request, f'{approved_count} verification requests were approved and agencies verified.')
    approve_requests.short_description = "Approve selected verification requests"
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        
        rejected_count = 0
        for verification_request in queryset.filter(status='pending'):
            verification_request.status = 'rejected'
            verification_request.reviewed_by = request.user
            verification_request.reviewed_at = timezone.now()
            verification_request.save()
            rejected_count += 1
            
        self.message_user(request, f'{rejected_count} verification requests were rejected.')
    reject_requests.short_description = "Reject selected verification requests"
