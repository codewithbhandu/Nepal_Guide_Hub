# apps/bookings/forms.py
from django import forms
from django.utils import timezone
from datetime import date
from .models import Booking, Rating

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['travel_date', 'end_date', 'number_of_people', 'special_requirements']
        widgets = {
            'travel_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'special_requirements': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date to today
        today = date.today().isoformat()
        self.fields['travel_date'].widget.attrs.update({
            'min': today,
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
        self.fields['end_date'].widget.attrs.update({
            'min': today,
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
        self.fields['special_requirements'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
        self.fields['number_of_people'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'min': '1'
        })

    def clean(self):
        cleaned_data = super().clean()
        travel_date = cleaned_data.get('travel_date')
        end_date = cleaned_data.get('end_date')
        
        # Check if travel date is in the past
        if travel_date and travel_date < date.today():
            raise forms.ValidationError("Travel date cannot be in the past.")
        
        # Check if end date is before travel date
        if travel_date and end_date and end_date <= travel_date:
            raise forms.ValidationError("End date must be after travel date.")
        
        # Check if end date is in the past
        if end_date and end_date < date.today():
            raise forms.ValidationError("End date cannot be in the past.")
        
        return cleaned_data

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)]),
            'review': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            })