from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('package/<int:package_id>/', views.book_package, name='book_package'),
    path('guide/<int:guide_id>/', views.book_guide, name='book_guide'),
    path('<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('<int:booking_id>/rate/', views.add_rating, name='add_rating'),
    path('<str:payment_id>/payment/', views.process_payment, name='process_payment'),
    path('payment/success/<str:transaction_id>/', views.payment_success, name='payment_success'),
    path('payment/failure/<str:transaction_id>/', views.payment_failure, name='payment_failure'),
]