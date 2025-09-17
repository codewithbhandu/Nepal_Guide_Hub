from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking, Rating
from .forms import BookingForm, RatingForm
from apps.packages.models import Package
from apps.guides.models import Guide
from apps.accounts.models import Agency

@login_required
def book_package(request, package_id):
    if request.user.user_type != 'tourist':
        messages.error(request, 'Only tourists can make bookings.')
        return redirect('core:home')
    
    package = get_object_or_404(Package, id=package_id, is_active=True, agency__is_verified=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tourist = request.user.tourist
            booking.package = package
            booking.agency = package.agency
            booking.total_amount = package.price_per_person * booking.number_of_people
            booking.save()
            
            # Send confirmation email (optional)
            try:
                send_mail(
                    'Booking Confirmation',
                    f'Your booking for {package.title} has been received. We will contact you soon.',
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 'Booking submitted successfully! You will be contacted soon.')
            return redirect('bookings:booking_detail', booking_id=booking.id)
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'package': package,
    }
    return render(request, 'bookings/book_package.html', context)

@login_required
def book_guide(request, guide_id):
    if request.user.user_type != 'tourist':
        messages.error(request, 'Only tourists can make bookings.')
        return redirect('core:home')
    
    guide = get_object_or_404(Guide, id=guide_id, is_available=True, agency__is_verified=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tourist = request.user.tourist
            booking.guide = guide
            booking.agency = guide.agency
            
            # Calculate duration and total amount
            duration = (booking.end_date - booking.travel_date).days + 1
            booking.total_amount = guide.daily_rate * duration
            booking.save()
            
            messages.success(request, 'Guide booking submitted successfully!')
            return redirect('bookings:booking_detail', booking_id=booking.id)
    else:
        form = BookingForm()
    
    context = {
        'form': form,
        'guide': guide,
    }
    return render(request, 'bookings/book_guide.html', context)

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check permissions
    if request.user.user_type == 'tourist' and booking.tourist.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    elif request.user.user_type == 'agency' and booking.agency.user != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    context = {
        'booking': booking,
    }
    return render(request, 'bookings/booking_detail.html', context)

@login_required
def my_bookings(request):
    if request.user.user_type == 'tourist':
        bookings = Booking.objects.filter(tourist=request.user.tourist).order_by('-created_at')
    elif request.user.user_type == 'agency':
        bookings = Booking.objects.filter(agency=request.user.agency).order_by('-created_at')
    else:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'bookings/my_bookings.html', context)

@login_required
def add_rating(request, booking_id):
    if request.user.user_type != 'tourist':
        messages.error(request, 'Only tourists can add ratings.')
        return redirect('core:home')
    
    booking = get_object_or_404(Booking, id=booking_id, tourist=request.user.tourist, status='completed')
    
    if request.method == 'POST':
        rating_type = request.POST.get('rating_type')
        form = RatingForm(request.POST)
        
        if form.is_valid():
            rating = form.save(commit=False)
            rating.tourist = request.user.tourist
            rating.booking = booking
            rating.rating_type = rating_type
            
            if rating_type == 'guide' and booking.guide:
                rating.guide = booking.guide
            elif rating_type == 'agency':
                rating.agency = booking.agency
            elif rating_type == 'package' and booking.package:
                rating.package = booking.package
            
            rating.save()
            messages.success(request, 'Rating added successfully!')
            return redirect('bookings:booking_detail', booking_id=booking.id)
    else:
        form = RatingForm()
    
    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'bookings/add_rating.html', context)