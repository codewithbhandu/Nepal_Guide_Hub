from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import UserRegistrationForm, CustomAuthenticationForm, TouristProfileForm, AgencyProfileForm
from .models import User, Tourist, Agency, VerificationRequest
from apps.packages.models import Package
from apps.guides.models import Guide
from apps.bookings.models import Booking
from django.db.models import Q, Case, When, IntegerField, Value
from datetime import date, datetime, timedelta
from django.utils import timezone
import re
import json

# ============= CUSTOM SEARCH, SORT, AND FILTER ALGORITHMS =============

def custom_text_search(queryset, search_term, fields):
    """
    ALGORITHM NAME: Tourist Package Text Search Algorithm
    
    PSEUDO CODE:
    1. Initialize empty Q object for OR conditions
    2. Clean search term (remove extra spaces, convert to lowercase)
    3. Split search term into individual words
    4. For each word:
        a. For each searchable field:
            - Create icontains filter condition
            - Add to OR chain
    5. Apply combined OR filter to queryset
    6. Calculate relevance score based on field matches
    7. Order by relevance score descending
    """
    if not search_term or not fields:
        return queryset
    
    # Clean and prepare search terms
    search_term = search_term.lower().strip()
    search_words = [word.strip() for word in search_term.split() if word.strip()]
    
    if not search_words:
        return queryset
    
    # Build Q object for OR conditions across all fields and words
    search_conditions = Q()
    
    for word in search_words:
        word_conditions = Q()
        for field in fields:
            word_conditions |= Q(**{f'{field}__icontains': word})
        search_conditions |= word_conditions
    
    # Apply search filter
    filtered_queryset = queryset.filter(search_conditions)
    
    # Custom relevance scoring
    relevance_cases = []
    score = 100  # Starting score
    
    for field in fields:
        for word in search_words:
            # Higher score for exact matches, lower for partial
            relevance_cases.append(
                When(**{f'{field}__iexact': word}, then=Value(score))
            )
            relevance_cases.append(
                When(**{f'{field}__icontains': word}, then=Value(score // 2))
            )
        score -= 10  # Decrease score for each field (priority order)
    
    # Add default case
    relevance_cases.append(When(pk__isnull=False, then=Value(1)))
    
    # Annotate with relevance score and order by it
    return filtered_queryset.annotate(
        relevance_score=Case(*relevance_cases, default=Value(0), output_field=IntegerField())
    ).order_by('-relevance_score')

def apply_custom_filters(request, queryset):
    """
    ALGORITHM NAME: Tourist Multi-Criteria Filter Algorithm
    
    PSEUDO CODE:
    1. Get filter parameters from request
    2. For each filter type:
        a. Check if filter value exists
        b. Apply specific filtering logic:
            - Package type: exact match
            - Duration: range-based filtering
            - Price: numeric range filtering
    3. Chain all filters using AND logic
    4. Return filtered queryset
    """
    filtered_queryset = queryset
    
    # Package type filter
    package_type = request.GET.get('package_type')
    if package_type:
        filtered_queryset = filtered_queryset.filter(package_type=package_type)
    
    # Duration filter (custom range logic)
    duration = request.GET.get('duration')
    if duration:
        if duration == '1-3':
            filtered_queryset = filtered_queryset.filter(duration_days__gte=1, duration_days__lte=3)
        elif duration == '4-7':
            filtered_queryset = filtered_queryset.filter(duration_days__gte=4, duration_days__lte=7)
        elif duration == '8-14':
            filtered_queryset = filtered_queryset.filter(duration_days__gte=8, duration_days__lte=14)
        elif duration == '15+':
            filtered_queryset = filtered_queryset.filter(duration_days__gte=15)
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price:
        try:
            min_price_val = float(min_price)
            filtered_queryset = filtered_queryset.filter(price_per_person__gte=min_price_val)
        except (ValueError, TypeError):
            pass
    
    if max_price:
        try:
            max_price_val = float(max_price)
            filtered_queryset = filtered_queryset.filter(price_per_person__lte=max_price_val)
        except (ValueError, TypeError):
            pass
    
    # Difficulty filter
    difficulty = request.GET.get('difficulty')
    if difficulty:
        filtered_queryset = filtered_queryset.filter(difficulty_level=difficulty)
    
    return filtered_queryset

def apply_custom_sort(request, queryset, search_query=None):
    """
    ALGORITHM NAME: Tourist Adaptive Sort Algorithm
    
    PSEUDO CODE:
    1. Get sort parameter from request
    2. Define sort priority matrix:
        a. If search query exists: prioritize relevance
        b. Price sorts: use numeric ordering
        c. Rating sort: use agency rating + total ratings
        d. Duration sort: use duration_days
        e. Default: newest first
    3. Apply multi-level sorting with fallbacks
    4. Return sorted queryset
    """
    sort_by = request.GET.get('sort', 'newest')
    
    if sort_by == 'price_low':
        return queryset.order_by('price_per_person', '-created_at')
    elif sort_by == 'price_high':
        return queryset.order_by('-price_per_person', '-created_at')
    elif sort_by == 'rating':
        return queryset.order_by('-agency__rating', '-agency__total_ratings', '-created_at')
    elif sort_by == 'duration_short':
        return queryset.order_by('duration_days', 'price_per_person')
    elif sort_by == 'duration_long':
        return queryset.order_by('-duration_days', 'price_per_person')
    elif sort_by == 'relevance' and search_query:
        # If relevance score exists from search, use it
        return queryset.order_by('-relevance_score', '-created_at')
    elif search_query and hasattr(queryset.first(), 'relevance_score') if queryset.first() else False:
        # Auto-sort by relevance if search was performed
        return queryset.order_by('-relevance_score', '-created_at')
    else:
        # Default: newest first
        return queryset.order_by('-created_at')

def get_current_filters(request):
    """
    Helper function to get current filter values for template context
    """
    return {
        'package_type': request.GET.get('package_type', ''),
        'duration': request.GET.get('duration', ''),
        'min_price': request.GET.get('min_price', ''),
        'max_price': request.GET.get('max_price', ''),
        'difficulty': request.GET.get('difficulty', ''),
        'sort': request.GET.get('sort', 'newest'),
    }

def apply_custom_guide_filters(request, queryset):
    """
    ALGORITHM NAME: Tourist Guide Multi-Criteria Filter Algorithm
    
    PSEUDO CODE:
    1. Get filter parameters from request
    2. Apply specialization filter (JSON array contains)
    3. Apply experience range filter with custom logic
    4. Apply language filter (JSON array contains)
    5. Apply daily rate range filter
    6. Return filtered queryset
    """
    filtered_queryset = queryset
    
    # Specialization filter
    specialization = request.GET.get('specialization')
    if specialization:
        # Custom JSON array search
        filtered_queryset = filtered_queryset.extra(
            where=["specialties::jsonb ? %s"],
            params=[specialization]
        )
    
    # Experience range filter
    experience = request.GET.get('experience')
    if experience:
        if experience == '1-5':
            filtered_queryset = filtered_queryset.filter(experience_years__gte=1, experience_years__lte=5)
        elif experience == '6-10':
            filtered_queryset = filtered_queryset.filter(experience_years__gte=6, experience_years__lte=10)
        elif experience == '11+':
            filtered_queryset = filtered_queryset.filter(experience_years__gte=11)
    
    # Language filter
    language = request.GET.get('language')
    if language:
        # Custom JSON array search
        filtered_queryset = filtered_queryset.extra(
            where=["languages::jsonb ? %s"],
            params=[language]
        )
    
    # Daily rate filter
    min_rate = request.GET.get('min_rate')
    max_rate = request.GET.get('max_rate')
    
    if min_rate:
        try:
            min_rate_val = float(min_rate)
            filtered_queryset = filtered_queryset.filter(daily_rate__gte=min_rate_val)
        except (ValueError, TypeError):
            pass
    
    if max_rate:
        try:
            max_rate_val = float(max_rate)
            filtered_queryset = filtered_queryset.filter(daily_rate__lte=max_rate_val)
        except (ValueError, TypeError):
            pass
    
    return filtered_queryset

def apply_custom_guide_sort(request, queryset, search_query=None):
    """
    ALGORITHM NAME: Tourist Guide Adaptive Sort Algorithm
    
    PSEUDO CODE:
    1. Get sort parameter from request
    2. Define sort logic:
        - Rating: order by rating desc, total_ratings desc
        - Price: order by daily_rate (asc/desc)
        - Experience: order by experience_years desc
        - Name: alphabetical order
        - Relevance: if search exists, use relevance_score
    3. Apply fallback sorting
    4. Return sorted queryset
    """
    sort_by = request.GET.get('sort', 'rating')
    
    if sort_by == 'rate_low':
        return queryset.order_by('daily_rate', '-rating')
    elif sort_by == 'rate_high':
        return queryset.order_by('-daily_rate', '-rating')
    elif sort_by == 'experience':
        return queryset.order_by('-experience_years', '-rating')
    elif sort_by == 'name':
        return queryset.order_by('name')
    elif sort_by == 'relevance' and search_query:
        return queryset.order_by('-relevance_score', '-rating')
    elif search_query and hasattr(queryset.first(), 'relevance_score') if queryset.first() else False:
        return queryset.order_by('-relevance_score', '-rating')
    else:
        # Default: rating-based
        return queryset.order_by('-rating', '-total_ratings', '-created_at')

def get_current_guide_filters(request):
    """
    Helper function to get current guide filter values
    """
    return {
        'specialization': request.GET.get('specialization', ''),
        'experience': request.GET.get('experience', ''),
        'language': request.GET.get('language', ''),
        'min_rate': request.GET.get('min_rate', ''),
        'max_rate': request.GET.get('max_rate', ''),
        'sort': request.GET.get('sort', 'rating'),
    }

def apply_custom_agency_filters(request, queryset):
    """
    ALGORITHM NAME: Tourist Agency Multi-Criteria Filter Algorithm
    
    PSEUDO CODE:
    1. Get filter parameters from request
    2. Apply location-based filter
    3. Apply services filter
    4. Apply experience/establishment filter with year calculation
    5. Apply minimum rating filter
    6. Return filtered queryset
    """
    filtered_queryset = queryset
    
    # Location filter
    location = request.GET.get('location')
    if location:
        filtered_queryset = filtered_queryset.filter(address__icontains=location)
    
    # Services filter (based on packages offered)
    services = request.GET.get('services')
    if services:
        filtered_queryset = filtered_queryset.filter(packages__package_type=services).distinct()
    
    # Experience filter based on establishment year
    experience = request.GET.get('experience')
    if experience:
        from django.utils import timezone
        current_year = timezone.now().year
        
        if experience == 'new':
            # 0-5 years
            filtered_queryset = filtered_queryset.filter(established_year__gte=current_year - 5)
        elif experience == 'experienced':
            # 6-15 years
            filtered_queryset = filtered_queryset.filter(
                established_year__gte=current_year - 15,
                established_year__lt=current_year - 5
            )
        elif experience == 'veteran':
            # 15+ years
            filtered_queryset = filtered_queryset.filter(established_year__lt=current_year - 15)
    
    # Minimum rating filter
    min_rating = request.GET.get('min_rating')
    if min_rating:
        try:
            min_rating_val = float(min_rating)
            filtered_queryset = filtered_queryset.filter(rating__gte=min_rating_val)
        except (ValueError, TypeError):
            pass
    
    return filtered_queryset

def apply_custom_agency_sort(request, queryset, search_query=None):
    """
    ALGORITHM NAME: Tourist Agency Adaptive Sort Algorithm
    
    PSEUDO CODE:
    1. Get sort parameter from request
    2. Define sort logic:
        - Rating: order by rating desc, total_ratings desc
        - Name: alphabetical order
        - Established: order by established_year (oldest/newest)
        - Packages: count packages and order by count
        - Relevance: use relevance_score if search exists
    3. Apply fallback sorting
    4. Return sorted queryset
    """
    sort_by = request.GET.get('sort', 'rating')
    
    if sort_by == 'name':
        return queryset.order_by('name')
    elif sort_by == 'established_old':
        return queryset.order_by('established_year', 'name')
    elif sort_by == 'established_new':
        return queryset.order_by('-established_year', '-rating')
    elif sort_by == 'packages':
        from django.db.models import Count
        return queryset.annotate(package_count=Count('packages')).order_by('-package_count', '-rating')
    elif sort_by == 'relevance' and search_query:
        return queryset.order_by('-relevance_score', '-rating')
    elif search_query and hasattr(queryset.first(), 'relevance_score') if queryset.first() else False:
        return queryset.order_by('-relevance_score', '-rating')
    else:
        # Default: rating-based
        return queryset.order_by('-rating', '-total_ratings', 'name')

def get_current_agency_filters(request):
    """
    Helper function to get current agency filter values
    """
    return {
        'location': request.GET.get('location', ''),
        'services': request.GET.get('services', ''),
        'experience': request.GET.get('experience', ''),
        'min_rating': request.GET.get('min_rating', ''),
        'sort': request.GET.get('sort', 'rating'),
    }

# ============= END CUSTOM ALGORITHMS =============

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
    Custom login view for tourists and agencies only.
    Admin users must use the admin-dashboard login page.
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
                # Check if user is admin - restrict admin login to admin dashboard only
                if user.user_type == 'admin' or user.is_superuser:
                    messages.error(request, 'Admin users must login through the admin dashboard. Please use the admin login page.')
                    return render(request, 'accounts/login.html', {'form': form})
                
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
                        return redirect('accounts:tourist_home')
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
            return redirect('accounts:tourist_home')
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

@login_required
def tourist_home_view(request):
    """Tourist homepage with listings"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    # Ensure tourist profile exists
    try:
        tourist = request.user.tourist
    except Tourist.DoesNotExist:
        return redirect('accounts:tourist_profile')
    
    # Fetch real data
    packages = Package.objects.filter(is_active=True, agency__is_verified=True)[:6]
    guides = Guide.objects.filter(is_available=True, agency__is_verified=True)[:6]
    agencies = Agency.objects.filter(is_verified=True)[:4]
    
    context = {
        'packages': packages,
        'guides': guides,
        'agencies': agencies,
        'is_tourist': True,
        'tourist': tourist,
        'packages_count': Package.objects.filter(is_active=True, agency__is_verified=True).count(),
        'guides_count': Guide.objects.filter(is_available=True, agency__is_verified=True).count(),
        'agencies_count': Agency.objects.filter(is_verified=True).count(),
    }
    
    return render(request, 'tourist/home.html', context)

@login_required
def tourist_packages_view(request):
    """Tourist packages listing page"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    # Custom Search, Sort, and Filter Algorithm Implementation
    packages = Package.objects.filter(is_active=True, agency__is_verified=True)
    
    # CUSTOM TEXT SEARCH ALGORITHM - "Tourist Package Text Search"
    search_query = request.GET.get('search', '').strip()
    if search_query:
        packages = custom_text_search(packages, search_query, ['title', 'description', 'package_type', 'agency__name'])
    
    # CUSTOM FILTER ALGORITHM - "Tourist Multi-Criteria Filter"
    packages = apply_custom_filters(request, packages)
    
    # CUSTOM SORT ALGORITHM - "Tourist Adaptive Sort"
    packages = apply_custom_sort(request, packages, search_query)
    
    context = {
        'packages': packages,
        'is_tourist': True,
        'search_query': search_query,
        'current_filters': get_current_filters(request),
    }
    
    return render(request, 'tourist/packages.html', context)

@login_required
def tourist_guides_view(request):
    """Tourist guides listing page"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    # Custom Search, Sort, and Filter Algorithm Implementation for Guides
    guides = Guide.objects.filter(is_available=True, agency__is_verified=True)
    
    # CUSTOM TEXT SEARCH for Guides
    search_query = request.GET.get('search', '').strip()
    if search_query:
        guides = custom_text_search(guides, search_query, ['name', 'bio', 'places_covered', 'agency__name'])
    
    # CUSTOM FILTER for Guides
    guides = apply_custom_guide_filters(request, guides)
    
    # CUSTOM SORT for Guides
    guides = apply_custom_guide_sort(request, guides, search_query)
    
    context = {
        'guides': guides,
        'is_tourist': True,
        'search_query': search_query,
        'current_filters': get_current_guide_filters(request),
    }
    
    return render(request, 'tourist/guides.html', context)

@login_required
def tourist_agencies_view(request):
    """Tourist agencies listing page"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    # Custom Search, Sort, and Filter Algorithm Implementation for Agencies
    agencies = Agency.objects.filter(is_verified=True)
    
    # CUSTOM TEXT SEARCH for Agencies
    search_query = request.GET.get('search', '').strip()
    if search_query:
        agencies = custom_text_search(agencies, search_query, ['name', 'description', 'address', 'contact_person'])
    
    # CUSTOM FILTER for Agencies
    agencies = apply_custom_agency_filters(request, agencies)
    
    # CUSTOM SORT for Agencies
    agencies = apply_custom_agency_sort(request, agencies, search_query)
    
    context = {
        'agencies': agencies,
        'is_tourist': True,
        'search_query': search_query,
        'current_filters': get_current_agency_filters(request),
    }
    
    return render(request, 'tourist/agencies.html', context)

@login_required
def agency_detail_view(request, agency_id):
    """Agency detail page with packages and guides"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    agency = get_object_or_404(Agency, id=agency_id, is_verified=True)
    packages = Package.objects.filter(agency=agency, is_active=True)
    guides = Guide.objects.filter(agency=agency, is_available=True)

    context = {
        'agency': agency,
        'packages': packages,
        'guides': guides,
        'is_tourist': True,
    }
    return render(request, 'tourist/agency_detail.html', context)

@login_required
def tourist_bookings_view(request):
    """Tourist bookings management page"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    # Get tourist's bookings
    try:
        tourist = request.user.tourist
        all_bookings = Booking.objects.filter(tourist=tourist).order_by('-created_at')
        
        # Filter bookings by status and payment
        # Active bookings: Confirmed bookings with payment (advance or full) that haven't been completed
        active_bookings = all_bookings.filter(
            status='confirmed',
            advance_amount__gt=0  # Must have some payment to be considered active
        ).exclude(status='completed')
        
        # Pending bookings: Bookings waiting for payment
        pending_bookings = all_bookings.filter(
            status='pending',
            advance_amount=0  # No payment made yet
        )
        
        # Completed bookings: Finished trips
        completed_bookings = all_bookings.filter(
            status='completed'
        )
        
    except Tourist.DoesNotExist:
        all_bookings = []
        active_bookings = []
        pending_bookings = []
        completed_bookings = []
    
    context = {
        'bookings': all_bookings,  # For compatibility
        'active_bookings': active_bookings,
        'pending_bookings': pending_bookings,
        'completed_bookings': completed_bookings,
        'is_tourist': True,
    }
    
    return render(request, 'tourist/bookings.html', context)

@login_required
def package_detail_view(request, package_id):
    """Package detail view with booking option"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    package = get_object_or_404(Package, id=package_id, is_active=True, agency__is_verified=True)
    package.increment_views()  # Increment view count
    
    # Get blocked dates (existing bookings)
    existing_bookings = Booking.objects.filter(
        package=package,
        status__in=['pending', 'confirmed']
    ).values_list('travel_date', 'end_date')
    
    blocked_dates = []
    for booking in existing_bookings:
        start_date = booking[0]
        end_date = booking[1] or start_date
        current_date = start_date
        while current_date <= end_date:
            blocked_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)
    
    # Add past dates to blocked dates
    today = date.today()
    for i in range(30):  # Block past 30 days
        past_date = today - timedelta(days=i+1)
        blocked_dates.append(past_date.isoformat())
    
    context = {
        'package': package,
        'is_tourist': True,
        'blocked_dates_json': json.dumps(blocked_dates),
        'min_date': today.isoformat(),
    }
    
    return render(request, 'tourist/package_detail.html', context)

@login_required
def guide_detail_view(request, guide_id):
    """Guide detail view with booking option"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    guide = get_object_or_404(Guide, id=guide_id, is_available=True, agency__is_verified=True)
    
    # Get blocked dates (existing guide bookings)
    existing_bookings = Booking.objects.filter(
        guide=guide,
        status__in=['pending', 'confirmed']
    ).values_list('travel_date', 'end_date')
    
    blocked_dates = []
    for booking in existing_bookings:
        start_date = booking[0]
        end_date = booking[1] or start_date
        current_date = start_date
        while current_date <= end_date:
            blocked_dates.append(current_date.isoformat())
            current_date += timedelta(days=1)
    
    # Add past dates to blocked dates
    today = date.today()
    for i in range(30):  # Block past 30 days
        past_date = today - timedelta(days=i+1)
        blocked_dates.append(past_date.isoformat())
    
    context = {
        'guide': guide,
        'is_tourist': True,
        'blocked_dates_json': json.dumps(blocked_dates),
        'min_date': today.isoformat(),
    }
    
    return render(request, 'tourist/guide_detail.html', context)

@login_required 
def book_package_view(request, package_id):
    """Handle package booking with calendar selection"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    package = get_object_or_404(Package, id=package_id, is_active=True, agency__is_verified=True)
    
    if request.method == 'POST':
        try:
            tourist = request.user.tourist
        except Tourist.DoesNotExist:
            messages.error(request, 'Please complete your profile first.')
            return redirect('accounts:tourist_profile')
        
        # Get booking details from form
        start_date_str = request.POST.get('start_date')
        number_of_people = int(request.POST.get('number_of_people', 1))
        special_requirements = request.POST.get('special_requirements', '')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=package.duration_days - 1)
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('accounts:package_detail', package_id=package_id)
        
        # Check if date is available
        conflicting_booking = Booking.objects.filter(
            package=package,
            travel_date__lte=end_date,
            end_date__gte=start_date,
            status__in=['pending', 'confirmed']
        ).exists()
        
        if conflicting_booking:
            messages.error(request, 'Selected dates are not available.')
            return redirect('accounts:package_detail', package_id=package_id)
        
        if start_date < date.today():
            messages.error(request, 'Cannot book past dates.')
            return redirect('accounts:package_detail', package_id=package_id)
        
        # Validate number of people
        if number_of_people < package.min_people or number_of_people > package.max_people:
            messages.error(request, f'Number of people must be between {package.min_people} and {package.max_people}.')
            return redirect('accounts:package_detail', package_id=package_id)
        
        # Calculate total amount
        total_amount = package.price_per_person * number_of_people
        
        # Create booking
        booking = Booking.objects.create(
            tourist=tourist,
            package=package,
            agency=package.agency,
            travel_date=start_date,
            end_date=end_date,
            number_of_people=number_of_people,
            total_amount=total_amount,
            special_requirements=special_requirements,
        )
        
        # Redirect to payment
        return redirect('accounts:payment_view', booking_type='package', booking_id=booking.id)
    
    return redirect('accounts:package_detail', package_id=package_id)

@login_required
def book_guide_view(request, guide_id):
    """Handle guide booking with calendar selection"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    guide = get_object_or_404(Guide, id=guide_id, is_available=True, agency__is_verified=True)
    
    if request.method == 'POST':
        try:
            tourist = request.user.tourist
        except Tourist.DoesNotExist:
            messages.error(request, 'Please complete your profile first.')
            return redirect('accounts:tourist_profile')
        
        # Get booking details from form
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        number_of_people = int(request.POST.get('number_of_people', 1))
        special_requirements = request.POST.get('special_requirements', '')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('accounts:guide_detail', guide_id=guide_id)
        
        # Validate date range
        if start_date < date.today():
            messages.error(request, 'Cannot book past dates.')
            return redirect('accounts:guide_detail', guide_id=guide_id)
        
        if end_date < start_date:
            messages.error(request, 'End date must be after start date.')
            return redirect('accounts:guide_detail', guide_id=guide_id)
        
        # Check if dates are available
        conflicting_booking = Booking.objects.filter(
            guide=guide,
            travel_date__lte=end_date,
            end_date__gte=start_date,
            status__in=['pending', 'confirmed']
        ).exists()
        
        if conflicting_booking:
            messages.error(request, 'Selected dates are not available.')
            return redirect('accounts:guide_detail', guide_id=guide_id)
        
        # Calculate total amount
        duration_days = (end_date - start_date).days + 1
        total_amount = guide.daily_rate * duration_days
        
        # Create booking
        booking = Booking.objects.create(
            tourist=tourist,
            guide=guide,
            agency=guide.agency,
            travel_date=start_date,
            end_date=end_date,
            number_of_people=number_of_people,
            total_amount=total_amount,
            special_requirements=special_requirements,
        )
        
        # Redirect to payment
        return redirect('accounts:payment_view', booking_type='guide', booking_id=booking.id)
    
    return redirect('accounts:guide_detail', guide_id=guide_id)

@login_required
def payment_view(request, booking_type, booking_id):
    """Payment page for bookings"""
    if request.user.user_type != 'tourist':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    try:
        tourist = request.user.tourist
    except Tourist.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('accounts:tourist_profile')
    
    booking = get_object_or_404(Booking, id=booking_id, tourist=tourist)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        if payment_method == 'advance':
            # Set advance payment (50% of total)
            advance_amount = booking.total_amount * 0.5
            booking.advance_amount = advance_amount
            booking.status = 'confirmed'
            booking.save()
            
            messages.success(request, 'Advance payment confirmed! Your booking is now confirmed.')
            return redirect('accounts:tourist_bookings')
        
        elif payment_method == 'full':
            # Set full payment
            booking.advance_amount = booking.total_amount
            booking.status = 'confirmed'
            booking.save()
            
            messages.success(request, 'Full payment confirmed! Your booking is now confirmed.')
            return redirect('accounts:tourist_bookings')
    
    context = {
        'booking': booking,
        'booking_type': booking_type,
        'is_tourist': True,
        'advance_amount': booking.total_amount * 0.5,
    }
    
    return render(request, 'tourist/payment.html', context)

def custom_logout(request):
    """Custom logout view that redirects to main homepage"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('core:home')  # Redirect to main website homepage

