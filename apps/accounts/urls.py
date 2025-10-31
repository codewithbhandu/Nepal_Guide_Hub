from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .oauth_views import GoogleOAuthCallbackView, GoogleOAuthStatusView, GoogleDisconnectView
from .forms import CustomAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('tourist-profile/', views.tourist_profile, name='tourist_profile'),
    path('agency-profile/', views.agency_profile, name='agency_profile'),
    
    # Tourist-specific URLs
    path('tourist/home/', views.tourist_home_view, name='tourist_home'),
    path('tourist/packages/', views.tourist_packages_view, name='tourist_packages'),
    path('tourist/guides/', views.tourist_guides_view, name='tourist_guides'),
    path('tourist/agencies/', views.tourist_agencies_view, name='tourist_agencies'),
    path('tourist/bookings/', views.tourist_bookings_view, name='tourist_bookings'),
    path('my-bookings/', views.tourist_bookings_view, name='my_bookings'),
    
    # Package, Guide and Agency Detail URLs
    path('package/<int:package_id>/', views.package_detail_view, name='package_detail'),
    path('guide/<int:guide_id>/', views.guide_detail_view, name='guide_detail'),
    path('agency/<int:agency_id>/', views.agency_detail_view, name='agency_detail'),
    
    # Booking URLs
    path('book/package/<int:package_id>/', views.book_package_view, name='book_package'),
    path('book/guide/<int:guide_id>/', views.book_guide_view, name='book_guide'),
    
    # Payment URL
    path('payment/<str:booking_type>/<int:booking_id>/', views.payment_view, name='payment_view'),
    
    # Google OAuth URLs
    path('oauth/callback/', GoogleOAuthCallbackView.as_view(), name='oauth_callback'),
    path('oauth/status/', GoogleOAuthStatusView.as_view(), name='oauth_status'),
    path('oauth/disconnect/', GoogleDisconnectView.as_view(), name='oauth_disconnect'),
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]