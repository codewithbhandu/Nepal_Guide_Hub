from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('contact/', views.contact, name='contact'),
    # Public detail views
    path('package/<slug:slug>/', views.package_detail, name='package_detail'),
    path('guide/<int:guide_id>/', views.guide_detail, name='guide_detail'), 
    path('agency/<int:agency_id>/', views.agency_detail, name='agency_detail'),
]
