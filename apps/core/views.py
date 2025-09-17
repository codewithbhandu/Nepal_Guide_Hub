from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from apps.packages.models import Package
from apps.guides.models import Guide
from apps.accounts.models import Agency
from .forms import SearchForm, ContactForm, NewsletterForm

def home(request):
    # Get featured content
    featured_packages = Package.objects.filter(is_active=True, featured=True, agency__is_verified=True)[:6]
    top_agencies = Agency.objects.filter(is_verified=True).order_by('-rating', '-total_ratings')[:6]
    top_guides = Guide.objects.filter(is_available=True, agency__is_verified=True).order_by('-rating', '-total_ratings')[:6]
    
    context = {
        'featured_packages': featured_packages,
        'top_agencies': top_agencies,
        'top_guides': top_guides,
    }
    return render(request, 'core/home.html', context)

def search(request):
    form = SearchForm(request.GET)
    results = {
        'packages': [],
        'guides': [],
        'agencies': [],
    }
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        search_type = form.cleaned_data.get('search_type', 'all')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        
        if query or min_price or max_price:
            # Search packages
            if search_type in ['all', 'packages']:
                package_query = Q(is_active=True, agency__is_verified=True)
                if query:
                    package_query &= (
                        Q(title__icontains=query) |
                        Q(description__icontains=query) |
                        Q(package_type__icontains=query)
                    )
                if min_price:
                    package_query &= Q(price_per_person__gte=min_price)
                if max_price:
                    package_query &= Q(price_per_person__lte=max_price)
                
                results['packages'] = Package.objects.filter(package_query)[:20]
            
            # Search guides
            if search_type in ['all', 'guides']:
                guide_query = Q(is_available=True, agency__is_verified=True)
                if query:
                    guide_query &= (
                        Q(name__icontains=query) |
                        Q(bio__icontains=query) |
                        Q(places_covered__icontains=query)
                    )
                if min_price:
                    guide_query &= Q(daily_rate__gte=min_price)
                if max_price:
                    guide_query &= Q(daily_rate__lte=max_price)
                
                results['guides'] = Guide.objects.filter(guide_query)[:20]
            
            # Search agencies
            if search_type in ['all', 'agencies']:
                agency_query = Q(is_verified=True)
                if query:
                    agency_query &= (
                        Q(name__icontains=query) |
                        Q(description__icontains=query) |
                        Q(address__icontains=query)
                    )
                
                results['agencies'] = Agency.objects.filter(agency_query)[:20]
    
    context = {
        'form': form,
        'results': results,
        'query': form.cleaned_data.get('query', '') if form.is_valid() else '',
    }
    return render(request, 'core/search.html', context)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})