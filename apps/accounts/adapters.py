from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import perform_login
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Tourist, Agency
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class GoogleSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for handling Google OAuth authentication
    Handles both new user registration and existing user login
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just before logging in with a social account
        """
        # Get the email from the social login
        email = sociallogin.account.extra_data.get('email', '')
        
        if email:
            try:
                # Check if user with this email already exists
                existing_user = User.objects.get(email=email)
                
                if not sociallogin.is_existing:
                    # User exists but social account doesn't - connect them
                    sociallogin.connect(request, existing_user)
                    logger.info(f"Connected existing user {existing_user.email} to Google account")
                    
            except User.DoesNotExist:
                # New user - let the normal flow continue
                logger.info(f"New user signing up with Google: {email}")
                pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login user
        """
        user = super().save_user(request, sociallogin, form)
        
        # Extract additional data from Google
        extra_data = sociallogin.account.extra_data
        
        # Update user with Google data
        if not user.first_name and extra_data.get('given_name'):
            user.first_name = extra_data.get('given_name', '')
        
        if not user.last_name and extra_data.get('family_name'):
            user.last_name = extra_data.get('family_name', '')
        
        # Set default user type if not set
        if not user.user_type:
            user.user_type = 'tourist'  # Default to tourist
        
        user.save()
        
        # Create profile based on user type
        self.create_user_profile(user, extra_data)
        
        logger.info(f"Created new user via Google OAuth: {user.email} as {user.user_type}")
        return user
    
    def create_user_profile(self, user, extra_data):
        """
        Create appropriate profile based on user type
        """
        if user.user_type == 'tourist':
            tourist, created = Tourist.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'nationality': '',  # User can fill this later
                }
            )
            if created:
                logger.info(f"Created tourist profile for {user.email}")
        
        elif user.user_type == 'agency':
            # For agency users, we'll create a basic profile
            # They'll need to complete it later with license, etc.
            agency, created = Agency.objects.get_or_create(
                user=user,
                defaults={
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'license_number': '',  # Must be filled later
                    'address': '',
                    'description': f"Agency profile for {user.get_full_name() or user.username}",
                    'contact_person': user.get_full_name() or user.username,
                }
            )
            if created:
                logger.info(f"Created agency profile for {user.email}")
    
    def get_login_redirect_url(self, request, user):
        """
        Determine where to redirect after successful Google login
        """
        if user.user_type == 'tourist':
            # Check if tourist profile is complete
            try:
                tourist = user.tourist
                if not tourist.nationality:
                    messages.info(request, "Please complete your tourist profile!")
                    return '/accounts/profile/tourist/'
                else:
                    messages.success(request, f"Welcome back, {tourist.full_name}!")
                    return '/'
            except Tourist.DoesNotExist:
                messages.info(request, "Please complete your tourist profile!")
                return '/accounts/profile/tourist/'
        
        elif user.user_type == 'agency':
            # Check if agency profile is complete
            try:
                agency = user.agency
                if not agency.license_number or not agency.address:
                    messages.info(request, "Please complete your agency profile!")
                    return '/accounts/profile/agency/'
                else:
                    messages.success(request, f"Welcome back, {agency.name}!")
                    return '/agencies/dashboard/'
            except Agency.DoesNotExist:
                messages.info(request, "Please complete your agency profile!")
                return '/accounts/profile/agency/'
        
        # Default redirect
        messages.success(request, f"Welcome, {user.get_full_name() or user.username}!")
        return '/'
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Handle authentication errors
        """
        logger.error(f"Google OAuth error: {error} - {exception}")
        messages.error(request, "Authentication with Google failed. Please try again.")
        return redirect('/accounts/login/')


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for regular account operations
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user from regular registration form
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Get user type from form if available
        if hasattr(form, 'cleaned_data') and 'user_type' in form.cleaned_data:
            user.user_type = form.cleaned_data['user_type']
        elif not user.user_type:
            user.user_type = 'tourist'  # Default
        
        if commit:
            user.save()
        
        return user