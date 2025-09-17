from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('package/<int:package_id>/', views.book_package, name='book_package'),
    path('guide/<int:guide_id>/', views.book_guide, name='book_guide'),
    path('<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('<int:booking_id>/rate/', views.add_rating, name='add_rating'),
]