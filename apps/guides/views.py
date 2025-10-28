from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Guide

def guide_list(request):
    guides = Guide.objects.filter(is_available=True, agency__is_verified=True)

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        guides = guides.filter(
            Q(name__icontains=search_query)
            | Q(bio__icontains=search_query)
            | Q(places_covered__icontains=search_query)
            | Q(agency__name__icontains=search_query)
        )

    # Filtering
    specialty = request.GET.get('specialty')
    language = request.GET.get('language')
    experience = request.GET.get('experience')  # e.g., "1-3", "3-5", "10+"
    min_rate = request.GET.get('min_rate')
    max_rate = request.GET.get('max_rate')

    if specialty:
        guides = guides.filter(specialties__contains=[specialty])
    if language:
        guides = guides.filter(languages__contains=[language])
    if experience:
        if experience == '1-3':
            guides = guides.filter(experience_years__gte=1, experience_years__lte=3)
        elif experience == '3-5':
            guides = guides.filter(experience_years__gte=3, experience_years__lte=5)
        elif experience == '5-10':
            guides = guides.filter(experience_years__gte=5, experience_years__lte=10)
        elif experience == '10+':
            guides = guides.filter(experience_years__gte=10)
    if min_rate:
        guides = guides.filter(daily_rate__gte=min_rate)
    if max_rate:
        guides = guides.filter(daily_rate__lte=max_rate)

    # Sorting
    sort_by = request.GET.get('sort', 'rating')
    if sort_by == 'price_low':
        guides = guides.order_by('daily_rate')
    elif sort_by == 'price_high':
        guides = guides.order_by('-daily_rate')
    elif sort_by == 'experience':
        guides = guides.order_by('-experience_years')
    else:
        guides = guides.order_by('-rating', '-total_ratings')

    # Pagination
    paginator = Paginator(guides, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'guides': page_obj,
        'specialties': Guide.SPECIALTIES,
        'languages': Guide.LANGUAGES,
    }
    return render(request, 'guides/guide_list.html', context)

def guide_detail(request, id):
    guide = get_object_or_404(Guide, id=id, is_available=True, agency__is_verified=True)
    
    # Get guide's packages (if any)
    packages = guide.agency.packages.filter(is_active=True)[:4]
    
    context = {
        'guide': guide,
        'packages': packages,
    }
    return render(request, 'guides/guide_detail.html', context)