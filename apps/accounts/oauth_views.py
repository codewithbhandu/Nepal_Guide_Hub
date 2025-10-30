from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, JsonResponse
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthCallbackView(View):
    """
    Handle Google OAuth callback
    This view processes the callback from Google after user authentication
    """
    
    def get(self, request):
        """
        Handle GET request from Google OAuth callback
        """
        # Check for error in callback
        error = request.GET.get('error')
        if error:
            error_description = request.GET.get('error_description', 'Unknown error')
            logger.error(f"Google OAuth error: {error} - {error_description}")
            messages.error(request, f"Google authentication failed: {error_description}")
            return redirect('accounts:login')
        
        # Check for authorization code
        code = request.GET.get('code')
        if not code:
            logger.error("No authorization code received from Google")
            messages.error(request, "Google authentication failed: No authorization code received")
            return redirect('accounts:login')
        
        # Let allauth handle the actual OAuth flow
        # This is handled by allauth's built-in views
        logger.info("Received Google OAuth callback with authorization code")
        
        # Return success - allauth will handle the rest
        return HttpResponseRedirect('/')


@method_decorator(csrf_exempt, name='dispatch')
class GoogleOAuthStatusView(View):
    """
    Check Google OAuth status and user information
    Useful for debugging and frontend integration
    """
    
    def get(self, request):
        """
        Return current user's Google OAuth status
        """
        if not request.user.is_authenticated:
            return JsonResponse({
                'authenticated': False,
                'google_connected': False
            })
        
        # Check if user has Google social account
        try:
            social_account = SocialAccount.objects.get(
                user=request.user,
                provider='google'
            )
            
            # Get Google user info
            google_data = social_account.extra_data
            
            return JsonResponse({
                'authenticated': True,
                'google_connected': True,
                'user': {
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'user_type': request.user.user_type,
                },
                'google_data': {
                    'email': google_data.get('email'),
                    'name': google_data.get('name'),
                    'picture': google_data.get('picture'),
                    'verified_email': google_data.get('verified_email', False),
                }
            })
            
        except SocialAccount.DoesNotExist:
            return JsonResponse({
                'authenticated': True,
                'google_connected': False,
                'user': {
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'user_type': request.user.user_type,
                }
            })


class GoogleDisconnectView(View):
    """
    Disconnect Google account from user profile
    """
    
    def post(self, request):
        """
        Remove Google social account connection
        """
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to disconnect your Google account.")
            return redirect('accounts:login')
        
        try:
            social_account = SocialAccount.objects.get(
                user=request.user,
                provider='google'
            )
            
            # Remove all associated tokens
            SocialToken.objects.filter(account=social_account).delete()
            
            # Remove the social account
            social_account.delete()
            
            messages.success(request, "Your Google account has been disconnected successfully.")
            logger.info(f"User {request.user.email} disconnected Google account")
            
        except SocialAccount.DoesNotExist:
            messages.info(request, "No Google account was connected to your profile.")
        
        return redirect('accounts:login')
    
    def get(self, request):
        """
        GET request not allowed for security
        """
        messages.error(request, "Invalid request method.")
        return redirect('accounts:login')