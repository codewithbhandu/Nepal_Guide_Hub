# apps/guides/forms.py
from django import forms
from .models import Guide

class GuideForm(forms.ModelForm):
    class Meta:
        model = Guide
        fields = ['name', 'bio', 'experience_years', 'languages', 'specialties', 'profile_picture', 
                 'daily_rate', 'is_available', 'places_covered', 'certifications']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'languages': forms.CheckboxSelectMultiple(),
            'specialties': forms.CheckboxSelectMultiple(),
            'places_covered': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter places separated by commas'}),
            'certifications': forms.Textarea(attrs={'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set choices for languages and specialties
        self.fields['languages'].widget = forms.CheckboxSelectMultiple(choices=Guide.LANGUAGES)
        self.fields['specialties'].widget = forms.CheckboxSelectMultiple(choices=Guide.SPECIALTIES)
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name not in ['languages', 'specialties', 'is_available', 'profile_picture']:
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                })