from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .forms import UserRegistrationForm, TouristProfileForm, AgencyProfileForm, CustomAuthenticationForm
from .models import User, Tourist, Agency, VerificationRequest

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account successfully created for {username}! Please log in to continue.')
            # Don't auto-login, redirect to login page instead
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
        
        # Pre-select user type if provided in URL
        user_type = request.GET.get('user_type')
        if user_type in ['tourist', 'agency']:
            form.fields['user_type'].initial = user_type
    
    return render(request, 'accounts/register.html', {'form': form})

def custom_login(request):
    """
    Custom login view that redirects agencies to their profile page after successful login
    if they haven't completed their profile yet.
    """
    if request.user.is_authenticated:
        # If user is already logged in, redirect appropriately
        if request.user.user_type == 'agency':
            try:
                agency = request.user.agency
                return redirect('agencies:dashboard')
            except Agency.DoesNotExist:
                return redirect('accounts:agency_profile')
        elif request.user.user_type == 'tourist':
            try:
                tourist = request.user.tourist
                return redirect('core:home')
            except Tourist.DoesNotExist:
                return redirect('accounts:tourist_profile')
        else:
            return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Redirect based on user type after successful login
                if user.user_type == 'agency':
                    try:
                        agency = user.agency
                        messages.success(request, f'Welcome back, {agency.name}!')
                        return redirect('agencies:dashboard')
                    except Agency.DoesNotExist:
                        messages.info(request, 'Please complete your agency profile to continue.')
                        return redirect('accounts:agency_profile')
                elif user.user_type == 'tourist':
                    try:
                        tourist = user.tourist
                        messages.success(request, f'Welcome back, {tourist.full_name}!')
                        return redirect('core:home')
                    except Tourist.DoesNotExist:
                        messages.info(request, 'Please complete your profile to continue.')
                        return redirect('accounts:tourist_profile')
                else:
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('core:home')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def tourist_profile(request):
    try:
        tourist = request.user.tourist
    except Tourist.DoesNotExist:
        tourist = None
    
    if request.method == 'POST':
        form = TouristProfileForm(request.POST, request.FILES, instance=tourist)
        if form.is_valid():
            tourist = form.save(commit=False)
            tourist.user = request.user
            tourist.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:home')
    else:
        form = TouristProfileForm(instance=tourist)
    
    return render(request, 'accounts/tourist_profile.html', {'form': form})

@login_required
def agency_profile(request):
    try:
        agency = request.user.agency
    except Agency.DoesNotExist:
        agency = None
    
    if request.method == 'POST':
        form = AgencyProfileForm(request.POST, request.FILES, instance=agency)
        if form.is_valid():
            agency = form.save(commit=False)
            agency.user = request.user
            is_new_agency = agency.pk is None
            agency.save()
            
            # Create verification request if this is a new profile or if not already verified
            if is_new_agency or not agency.is_verified:
                # Check if there's already a pending verification request
                existing_request = VerificationRequest.objects.filter(
                    agency=agency,
                    status='pending'
                ).first()
                
                if not existing_request:
                    VerificationRequest.objects.create(
                        agency=agency,
                        requested_by=request.user,
                        message=f"Profile {'created' if is_new_agency else 'updated'} and submitted for verification."
                    )
            
            messages.success(request, 'Profile updated successfully and sent for verification! You will be notified once your agency is verified.')
            return redirect('agencies:dashboard')
    else:
        form = AgencyProfileForm(instance=agency)
    
    return render(request, 'accounts/agency_profile.html', {'form': form})