from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import SearchForm, ContactForm, NewsletterForm

def home(request):
    # Get tourist-specific context if user is logged in as tourist
    context = {
        'is_tourist': request.user.is_authenticated and request.user.user_type == 'tourist',
        'featured_packages': [],  # Placeholder for now
        'top_agencies': [],       # Placeholder for now
        'top_guides': [],         # Placeholder for now
    }
    
    if context['is_tourist']:
        try:
            tourist = request.user.tourist
            context['tourist'] = tourist
            context['show_tourist_features'] = True
        except:
            context['show_tourist_features'] = False
    
    return render(request, 'core/home.html', context)

def search(request):
    form = SearchForm(request.GET) if 'query' in request.GET else SearchForm()
    results = {
        'packages': [],
        'guides': [],
        'agencies': [],
    }
    
    query = ''
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        # Placeholder search results for now
        # When models are implemented, this will search actual data
    
    context = {
        'form': form,
        'results': results,
        'query': query,
        'is_tourist': request.user.is_authenticated and request.user.user_type == 'tourist',
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