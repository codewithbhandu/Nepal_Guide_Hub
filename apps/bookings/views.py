from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking, Rating,Payment
from .forms import BookingForm, RatingForm
from apps.packages.models import Package
from apps.guides.models import Guide
from apps.accounts.models import Agency
import uuid
from .esewa_helper import SimpleEsewaPayment as EsewaPayment

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
             
            # create payment object 
            id = str(uuid.uuid4())[:10]
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_amount,
                transaction_id=id,
                status='pending',
                service_charge=0.0
            )
            messages.success(request, 'Booking submitted successfully! Proceed to payment.')
            return redirect('bookings:process_payment', payment_id=id)
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
            
            # create payment object 
            id = str(uuid.uuid4())[:10]
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_amount,
                transaction_id=id,
                status='pending',
                service_charge=0.0
            )
            messages.success(request, 'Guide booking submitted successfully! Proceed to payment.')
            return redirect('bookings:process_payment', payment_id=id)
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

@login_required
def process_payment(request, payment_id):
    payment = get_object_or_404(Payment, transaction_id=payment_id, booking__tourist__user=request.user)
    
    epayment = EsewaPayment(
        amount=payment.amount,
        tax_amount=0.0,
        total_amount=payment.amount,
        product_service_charge=payment.service_charge,
        transaction_uuid=payment_id,
        product_delivery_charge=0.0,
        success_url=f'http://localhost:8000/bookings/payment/success/{payment.transaction_id}/',
        failure_url=f'http://localhost:8000/bookings/payment/failure/{payment.transaction_id}/',
    )
    epayment.create_signature(transaction_uuid=payment_id)
    context = {
        'payment': payment,
        'form': epayment.generate_form(),
        'package': payment.booking.package,
    }
    return render(request, 'bookings/process_payment.html', context)

@login_required
def payment_success(request, transaction_id):
    payment = get_object_or_404(Payment, transaction_id=transaction_id, status='pending')
    epayment = EsewaPayment(
        amount=payment.amount,
        tax_amount=0,
        total_amount=payment.amount,
        product_service_charge=payment.service_charge,
        product_delivery_charge=0,
        success_url=f'{'http://localhost:8000/bookings/payment/success/{payment.transaction_id}/'}',
        failure_url=f'{'http://localhost:8000/bookings/payment/failure/{payment.transaction_id}/'}',
    )
    epayment.create_signature(transaction_uuid=transaction_id)
    if epayment.is_completed(True):
        payment.status = 'completed'
        payment.booking.status = 'confirmed'
        payment.booking.save()
        payment.save()
    else:
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('bookings:payment_failure', transaction_id=payment.transaction_id)
    
    messages.success(request, 'Payment completed successfully!')
    return redirect('bookings:booking_detail', booking_id=payment.booking.id)



def payment_failure(request, transaction_id):
    payment = get_object_or_404(Payment, transaction_id=transaction_id, status='pending')
    payment.status = 'failed'
    payment.booking.status = 'cancelled'  # Set to cancelled instead of failed
    payment.booking.save()
    payment.save()
    
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('bookings:booking_detail', booking_id=payment.booking.id)
