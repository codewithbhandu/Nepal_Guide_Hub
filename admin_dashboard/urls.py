from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('verification-requests/', views.verification_requests, name='verification_requests'),
    path('verification-requests/<int:request_id>/approve/', views.approve_verification, name='approve_verification'),
    path('verification-requests/<int:request_id>/reject/', views.reject_verification, name='reject_verification'),
]
