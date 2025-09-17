# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re
from .models import User, Tourist, Agency

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=17, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'user_type', 'password1', 'password2')
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove admin from choices for public registration
        user_type_choices = [choice for choice in User.USER_TYPES if choice[0] != 'admin']
        self.fields['user_type'].choices = user_type_choices
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            # Check minimum length
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for at least one uppercase letter
            if not re.search(r'[A-Z]', password):
                raise ValidationError("Password must contain at least 1 capital letter.")
            
            # Check for at least one character (letter)
            if not re.search(r'[a-zA-Z]', password):
                raise ValidationError("Password must contain at least 1 character (letter).")
            
            # Check for at least one digit
            if not re.search(r'\d', password):
                raise ValidationError("Password must contain at least 1 number.")
        
        return password

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Password'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Allow login with email
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username

class TouristProfileForm(forms.ModelForm):
    class Meta:
        model = Tourist
        fields = ['full_name', 'nationality', 'date_of_birth', 'profile_picture', 'emergency_contact', 'emergency_phone']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'profile_picture':
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                })

class AgencyProfileForm(forms.ModelForm):
    class Meta:
        model = Agency
        fields = ['name', 'license_number', 'address', 'description', 'website', 'logo', 'established_year', 'contact_person']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'logo':
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
                })
