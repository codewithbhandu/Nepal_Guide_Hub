from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json

from apps.accounts.models import User, Agency, VerificationRequest
from apps.bookings.models import Booking
from apps.packages.models import Package
from apps.guides.models import Guide

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_superuser or user.user_type == 'admin')

def admin_login(request):
    """Custom admin login view - only for admin users"""
    if request.user.is_authenticated and (request.user.is_superuser or request.user.user_type == 'admin'):
        return redirect('admin_dashboard:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_superuser or user.user_type == 'admin'):
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard:dashboard')
        else:
            messages.error(request, 'Invalid admin credentials. Only admin users can access this page.')
    
    return render(request, 'admin_dashboard/login.html')

@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics"""
    
    # Get time period filter
    period = request.GET.get('period', '30d')
    
    if period == '7d':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '30d':
        start_date = timezone.now() - timedelta(days=30)
    elif period == '90d':
        start_date = timezone.now() - timedelta(days=90)
    else:  # all time
        start_date = None
    
    # Base querysets
    if start_date:
        base_filter = Q(created_at__gte=start_date)
    else:
        base_filter = Q()
    
    # Overall Statistics
    total_users = User.objects.count()
    total_agencies = Agency.objects.count()
    verified_agencies = Agency.objects.filter(is_verified=True).count()
    pending_agencies = Agency.objects.filter(is_verified=False).count()
    total_packages = Package.objects.count()
    active_packages = Package.objects.filter(is_active=True).count()
    total_guides = Guide.objects.count()
    total_bookings = Booking.objects.count()
    
    # Recent activity (last 30 days)
    recent_users = User.objects.filter(base_filter).count() if start_date else User.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    recent_bookings = Booking.objects.filter(base_filter).count() if start_date else Booking.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Revenue calculations
    if start_date:
        revenue_filter = Q(created_at__gte=start_date, status__in=['confirmed', 'completed'])
    else:
        revenue_filter = Q(status__in=['confirmed', 'completed'])
    
    total_revenue = Booking.objects.filter(revenue_filter).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Verification requests
    pending_verifications = VerificationRequest.objects.filter(status='pending').count()
    
    # Recent verification requests
    recent_verification_requests = VerificationRequest.objects.filter(
        status='pending'
    ).select_related('agency', 'requested_by').order_by('-created_at')[:10]
    
    # User type distribution
    user_distribution = User.objects.values('user_type').annotate(
        count=Count('id')
    ).order_by('user_type')
    
    # Monthly data for charts (last 12 months)
    monthly_data = []
    for i in range(12):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        
        month_users = User.objects.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        month_bookings = Booking.objects.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        ).count()
        
        month_revenue = Booking.objects.filter(
            status__in=['confirmed', 'completed'],
            created_at__gte=month_start,
            created_at__lte=month_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_data.insert(0, {
            'month': month_start.strftime('%b %Y'),
            'users': month_users,
            'bookings': month_bookings,
            'revenue': float(month_revenue)
        })
    
    # Top performing agencies
    top_agencies = Agency.objects.filter(is_verified=True).annotate(
        bookings_count=Count('booking'),
        revenue=Sum('booking__total_amount', filter=Q(booking__status__in=['confirmed', 'completed']))
    ).order_by('-revenue')[:5]
    
    # Recent bookings
    recent_bookings_list = Booking.objects.select_related(
        'tourist__user', 'agency', 'package', 'guide'
    ).order_by('-created_at')[:10]
    
    context = {
        'period': period,
        'total_users': total_users,
        'total_agencies': total_agencies,
        'verified_agencies': verified_agencies,
        'pending_agencies': pending_agencies,
        'total_packages': total_packages,
        'active_packages': active_packages,
        'total_guides': total_guides,
        'total_bookings': total_bookings,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'total_revenue': total_revenue,
        'pending_verifications': pending_verifications,
        'recent_verification_requests': recent_verification_requests,
        'user_distribution': user_distribution,
        'monthly_data': json.dumps(monthly_data),
        'top_agencies': top_agencies,
        'recent_bookings_list': recent_bookings_list,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)

@user_passes_test(is_admin)
def verification_requests(request):
    """Manage verification requests"""
    
    status_filter = request.GET.get('status', 'pending')
    
    requests = VerificationRequest.objects.select_related(
        'agency', 'requested_by', 'reviewed_by'
    ).filter(status=status_filter).order_by('-created_at')
    
    context = {
        'requests': requests,
        'current_status': status_filter,
        'pending_count': VerificationRequest.objects.filter(status='pending').count(),
        'approved_count': VerificationRequest.objects.filter(status='approved').count(),
        'rejected_count': VerificationRequest.objects.filter(status='rejected').count(),
    }
    
    return render(request, 'admin_dashboard/verification_requests.html', context)

@user_passes_test(is_admin)
def approve_verification(request, request_id):
    """Approve a verification request"""
    verification_request = get_object_or_404(VerificationRequest, id=request_id)
    
    if request.method == 'POST':
        verification_request.status = 'approved'
        verification_request.reviewed_by = request.user
        verification_request.reviewed_at = timezone.now()
        verification_request.admin_notes = request.POST.get('admin_notes', '')
        verification_request.save()
        
        # Update agency
        agency = verification_request.agency
        agency.is_verified = True
        agency.verified_at = timezone.now()
        agency.verified_by = request.user
        agency.save()
        
        messages.success(request, f'Verification request for {agency.name} has been approved.')
        
        # Send email notification (we'll implement this next)
        send_verification_email(agency, 'approved')
        
        return redirect('admin_dashboard:verification_requests')
    
    return render(request, 'admin_dashboard/approve_verification.html', {
        'verification_request': verification_request
    })

@user_passes_test(is_admin)
def reject_verification(request, request_id):
    """Reject a verification request"""
    verification_request = get_object_or_404(VerificationRequest, id=request_id)
    
    if request.method == 'POST':
        verification_request.status = 'rejected'
        verification_request.reviewed_by = request.user
        verification_request.reviewed_at = timezone.now()
        verification_request.admin_notes = request.POST.get('admin_notes', '')
        verification_request.save()
        
        messages.success(request, f'Verification request for {verification_request.agency.name} has been rejected.')
        
        # Send email notification
        send_verification_email(verification_request.agency, 'rejected', verification_request.admin_notes)
        
        return redirect('admin_dashboard:verification_requests')
    
    return render(request, 'admin_dashboard/reject_verification.html', {
        'verification_request': verification_request
    })

def send_verification_email(agency, status, notes=None):
    """Send email notification about verification status"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    subject = f'Verification Update - {agency.name}'
    
    if status == 'approved':
        template = 'admin_dashboard/emails/verification_approved.html'
    else:
        template = 'admin_dashboard/emails/verification_rejected.html'
    
    context = {
        'agency': agency,
        'notes': notes,
    }
    
    html_message = render_to_string(template, context)
    plain_message = render_to_string(template.replace('.html', '.txt'), context)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[agency.user.email],
            html_message=html_message,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
