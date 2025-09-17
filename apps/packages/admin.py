from django.contrib import admin
from .models import Package, PackageImage

class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'agency', 'package_type', 'duration_days', 'price_per_person', 'is_active', 'featured')
    list_filter = ('package_type', 'difficulty_level', 'is_active', 'featured', 'created_at')
    search_fields = ('title', 'description', 'agency__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views_count', 'created_at', 'updated_at')
    inlines = [PackageImageInline]
    actions = ['make_featured', 'remove_featured']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} packages were marked as featured.')
    make_featured.short_description = "Mark selected packages as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} packages were removed from featured.')
    remove_featured.short_description = "Remove from featured"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agency')

@admin.register(PackageImage)
class PackageImageAdmin(admin.ModelAdmin):
    list_display = ('package', 'caption', 'is_main', 'created_at')
    list_filter = ('is_main', 'created_at')
    search_fields = ('package__title', 'caption')