
# apps/core/forms.py
from django import forms
from .models import Contact, NewsletterSubscription

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            })

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            })
        }

class SearchForm(forms.Form):
    # Search type options
    SEARCH_TYPES = (
        ('all', 'All'),
        ('packages', 'Packages'),
        ('guides', 'Guides'),
        ('agencies', 'Agencies'),
    )

    # Package type options — you can later populate dynamically from Package model
    PACKAGE_TYPES = (
        ('', 'All Types'),
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural'),
        ('family', 'Family'),
    )

    # Search query
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search packages, guides, or agencies...',
            'class': 'block w-full px-4 py-2 text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500'
        })
    )

    # Search type dropdown
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )

    # Package type dropdown
    package_type = forms.ChoiceField(
        choices=PACKAGE_TYPES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )

    # Minimum price
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price',
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )

    # Maximum price
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price',
            'class': 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
        })
    )
