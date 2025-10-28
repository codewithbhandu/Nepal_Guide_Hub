from django.urls import path
from . import views

app_name = 'agencies'

urlpatterns = [
    path('', views.agency_list, name='agency_list'),
    path('<int:id>/', views.agency_detail, name='agency_detail'),
    path('dashboard/', views.agency_dashboard, name='dashboard'),
    path('guides/', views.manage_guides, name='manage_guides'),
    path('guides/add/', views.add_guide, name='add_guide'),
    path('guides/<int:guide_id>/edit/', views.edit_guide, name='edit_guide'),
    path('guides/<int:guide_id>/delete/', views.delete_guide, name='delete_guide'),
    path('packages/', views.manage_packages, name='manage_packages'),
    path('packages/add/', views.add_package, name='add_package'),
    path('packages/<int:package_id>/edit/', views.edit_package, name='edit_package'),
    path('packages/<int:package_id>/delete/', views.delete_package, name='delete_package'),
    path('bookings/', views.agency_bookings, name='bookings'),
    path('analytics/', views.agency_analytics, name='analytics'),
    path('api/new-bookings-count/', views.new_bookings_count, name='new_bookings_count'),
]
