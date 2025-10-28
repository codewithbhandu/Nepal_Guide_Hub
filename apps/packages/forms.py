
# apps/packages/forms.py
from django import forms
from .models import Package, PackageImage

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['title', 'description', 'package_type', 'duration_days', 'max_people', 'min_people',
                 'price_per_person', 'included_services', 'excluded_services', 'difficulty_level',
                 'best_season', 'altitude', 'equipment_provided', 'is_active', 'featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'included_services': forms.Textarea(attrs={'rows': 4}),
            'excluded_services': forms.Textarea(attrs={'rows': 4}),
            'equipment_provided': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['is_active', 'featured']:
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-nepal-green-500 focus:border-nepal-green-500'
                })
            else:
                # For checkboxes
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-nepal-green-600 focus:ring-nepal-green-500 border-gray-300 rounded'
                })

class PackageImageForm(forms.ModelForm):
    class Meta:
        model = PackageImage
        fields = ['image', 'caption', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-nepal-green-50 file:text-nepal-green-700 hover:file:bg-nepal-green-100'}),
            'caption': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-nepal-green-500 focus:border-nepal-green-500'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_main'].widget.attrs.update({
            'class': 'h-4 w-4 text-nepal-green-600 focus:ring-nepal-green-500 border-gray-300 rounded'
        })

# Multiple image upload formset
PackageImageFormSet = forms.modelformset_factory(
    PackageImage, 
    form=PackageImageForm, 
    extra=3, 
    can_delete=True
)