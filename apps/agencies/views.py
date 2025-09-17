from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.accounts.models import Agency
from apps.guides.forms import GuideForm
from apps.packages.forms import PackageForm, PackageImageFormSet
from apps.guides.models import Guide
from apps.packages.models import Package, PackageImage

def agency_list(request):
    agencies = Agency.objects.filter(is_verified=True)
    
    # Sorting
    sort_by = request.GET.get('sort', 'rating')
    if sort_by == 'name':
        agencies = agencies.order_by('name')
    elif sort_by == 'newest':
        agencies = agencies.order_by('-created_at')
    else:
        agencies = agencies.order_by('-rating', '-total_ratings')
    
    # Pagination
    paginator = Paginator(agencies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_sort': sort_by,
    }
    return render(request, 'agencies/agency_list.html', context)

def agency_detail(request, id):
    agency = get_object_or_404(Agency, id=id, is_verified=True)
    
    # Get agency's guides and packages
    guides = agency.guides.filter(is_available=True)
    packages = agency.packages.filter(is_active=True)
    
    context = {
        'agency': agency,
        'guides': guides,
        'packages': packages,
    }
    return render(request, 'agencies/agency_detail.html', context)

@login_required
def agency_dashboard(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied. You must be an agency to access this page.')
        return redirect('core:home')
    
    try:
        agency = request.user.agency
    except Agency.DoesNotExist:
        messages.error(request, 'Please complete your agency profile first.')
        return redirect('accounts:agency_profile')
    
    from django.db.models import Sum, Count, Avg
    from datetime import datetime, timedelta
    from django.utils import timezone
    import json
    
    # Get agency statistics
    guides_count = agency.guides.count()
    packages_count = agency.packages.count()
    active_packages = agency.packages.filter(is_active=True).count()
    bookings_count = agency.booking_set.count()
    
    # Revenue calculations
    total_revenue = agency.booking_set.filter(
        status__in=['confirmed', 'completed']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Monthly revenue (current month)
    current_month = timezone.now().replace(day=1)
    monthly_revenue = agency.booking_set.filter(
        status__in=['confirmed', 'completed'],
        created_at__gte=current_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get recent bookings
    recent_bookings = agency.booking_set.order_by('-created_at')[:5]
    
    # Popular packages (by booking count)
    popular_packages = agency.packages.annotate(
        booking_count=Count('booking')
    ).order_by('-booking_count')[:5]
    
    # Top performing guides (by rating and booking count)
    top_guides = agency.guides.annotate(
        booking_count=Count('booking')
    ).filter(is_available=True).order_by('-rating', '-booking_count')[:5]
    
    # Chart data - last 6 months
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # Revenue data for chart
    revenue_data = []
    revenue_labels = []
    booking_data = []
    booking_labels = []
    
    for i in range(6):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        
        month_revenue = agency.booking_set.filter(
            status__in=['confirmed', 'completed'],
            created_at__gte=month_start,
            created_at__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        month_bookings = agency.booking_set.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        revenue_data.insert(0, float(month_revenue))
        booking_data.insert(0, month_bookings)
        revenue_labels.insert(0, month_start.strftime('%b %Y'))
        booking_labels.insert(0, month_start.strftime('%b %Y'))
    
    context = {
        'agency': agency,
        'guides_count': guides_count,
        'packages_count': packages_count,
        'active_packages': active_packages,
        'bookings_count': bookings_count,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'recent_bookings': recent_bookings,
        'popular_packages': popular_packages,
        'top_guides': top_guides,
        'revenue_data': json.dumps(revenue_data),
        'revenue_labels': json.dumps(revenue_labels),
        'booking_data': json.dumps(booking_data),
        'booking_labels': json.dumps(booking_labels),
    }
    return render(request, 'agencies/agency_dashboard.html', context)

@login_required
def manage_guides(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    agency = request.user.agency
    guides = agency.guides.all()
    
    context = {
        'guides': guides,
        'agency': agency,
    }
    return render(request, 'agencies/manage_guides.html', context)

@login_required
def add_guide(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = GuideForm(request.POST, request.FILES)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.agency = request.user.agency
            guide.save()
            messages.success(request, 'Guide added successfully!')
            return redirect('agencies:manage_guides')
    else:
        form = GuideForm()
    
    return render(request, 'agencies/add_guide.html', {'form': form})

@login_required
def edit_guide(request, guide_id):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    guide = get_object_or_404(Guide, id=guide_id, agency=request.user.agency)
    
    if request.method == 'POST':
        form = GuideForm(request.POST, request.FILES, instance=guide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guide updated successfully!')
            return redirect('agencies:manage_guides')
    else:
        form = GuideForm(instance=guide)
    
    return render(request, 'agencies/edit_guide.html', {'form': form, 'guide': guide})

@login_required
def manage_packages(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    agency = request.user.agency
    packages = agency.packages.all()
    
    context = {
        'packages': packages,
        'agency': agency,
    }
    return render(request, 'agencies/manage_packages.html', context)

@login_required
def add_package(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = PackageForm(request.POST)
        image_formset = PackageImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and image_formset.is_valid():
            package = form.save(commit=False)
            package.agency = request.user.agency
            # Generate slug from title
            from django.utils.text import slugify
            package.slug = slugify(package.title)
            package.save()
            
            # Save images
            for image_form in image_formset:
                if image_form.cleaned_data:
                    image = image_form.save(commit=False)
                    image.package = package
                    image.save()
            
            messages.success(request, 'Package added successfully!')
            return redirect('agencies:manage_packages')
    else:
        form = PackageForm()
        image_formset = PackageImageFormSet(queryset=PackageImage.objects.none())
    
    context = {
        'form': form,
        'image_formset': image_formset,
    }
    return render(request, 'agencies/add_package.html', context)

@login_required
def edit_package(request, package_id):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    package = get_object_or_404(Package, id=package_id, agency=request.user.agency)
    
    if request.method == 'POST':
        form = PackageForm(request.POST, instance=package)
        image_formset = PackageImageFormSet(request.POST, request.FILES, queryset=package.images.all())
        
        if form.is_valid() and image_formset.is_valid():
            package = form.save()
            
            # Save images
            for image_form in image_formset:
                if image_form.cleaned_data:
                    if image_form.cleaned_data.get('DELETE'):
                        if image_form.instance.pk:
                            image_form.instance.delete()
                    else:
                        image = image_form.save(commit=False)
                        image.package = package
                        image.save()
            
            messages.success(request, 'Package updated successfully!')
            return redirect('agencies:manage_packages')
    else:
        form = PackageForm(instance=package)
        image_formset = PackageImageFormSet(queryset=package.images.all())
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'package': package,
    }
    return render(request, 'agencies/edit_package.html', context)

@login_required
def agency_bookings(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    agency = request.user.agency
    bookings = agency.booking_set.order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'confirmed', 'cancelled', 'completed']:
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'agency': agency,
        'page_obj': page_obj,
        'current_status': status_filter,
    }
    return render(request, 'agencies/bookings.html', context)

@login_required
def agency_analytics(request):
    if request.user.user_type != 'agency':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    from django.db.models import Sum, Count, Avg, Q
    from datetime import datetime, timedelta
    from django.utils import timezone
    import json
    
    agency = request.user.agency
    
    # Get time period from request (default: last 12 months)
    period = request.GET.get('period', '12m')
    
    if period == '30d':
        start_date = timezone.now() - timedelta(days=30)
        date_format = '%b %d'
        periods = 30
    elif period == '6m':
        start_date = timezone.now() - timedelta(days=180)
        date_format = '%b %Y'
        periods = 6
    else:  # 12m
        start_date = timezone.now() - timedelta(days=365)
        date_format = '%b %Y'
        periods = 12
    
    # Revenue analysis
    revenue_stats = agency.booking_set.filter(
        status__in=['confirmed', 'completed'],
        created_at__gte=start_date
    ).aggregate(
        total_revenue=Sum('total_amount'),
        avg_booking_value=Avg('total_amount'),
        total_bookings=Count('id')
    )
    
    # Package performance
    package_performance = agency.packages.annotate(
        booking_count=Count('booking', filter=Q(booking__created_at__gte=start_date)),
        revenue=Sum('booking__total_amount', filter=Q(
            booking__status__in=['confirmed', 'completed'],
            booking__created_at__gte=start_date
        ))
    ).order_by('-revenue')[:10]
    
    # Guide performance
    guide_performance = agency.guides.annotate(
        booking_count=Count('booking', filter=Q(booking__created_at__gte=start_date)),
        avg_rating=Avg('ratings__rating')
    ).order_by('-booking_count')[:10]
    
    # Monthly trend data
    monthly_data = []
    for i in range(periods):
        if period == '30d':
            current_date = timezone.now() - timedelta(days=i)
            month_bookings = agency.booking_set.filter(
                created_at__date=current_date.date()
            ).count()
            month_revenue = agency.booking_set.filter(
                status__in=['confirmed', 'completed'],
                created_at__date=current_date.date()
            ).aggregate(total=Sum('total_amount'))['total'] or 0
        else:
            month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
            month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            
            month_bookings = agency.booking_set.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            month_revenue = agency.booking_set.filter(
                status__in=['confirmed', 'completed'],
                created_at__gte=month_start,
                created_at__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_data.insert(0, {
            'period': current_date.strftime(date_format) if period == '30d' else month_start.strftime(date_format),
            'bookings': month_bookings,
            'revenue': float(month_revenue)
        })
    
    context = {
        'agency': agency,
        'period': period,
        'revenue_stats': revenue_stats,
        'package_performance': package_performance,
        'guide_performance': guide_performance,
        'monthly_data': json.dumps(monthly_data),
    }
    return render(request, 'agencies/analytics.html', context)

@login_required
def new_bookings_count(request):
    """API endpoint to get count of new bookings for notifications"""
    if request.user.user_type != 'agency':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from django.http import JsonResponse
    from django.utils import timezone
    from datetime import timedelta
    
    # Get bookings from last 24 hours that are still pending
    last_24h = timezone.now() - timedelta(hours=24)
    new_bookings_count = request.user.agency.booking_set.filter(
        created_at__gte=last_24h,
        status='pending'
    ).count()
    
    return JsonResponse({'count': new_bookings_count})
