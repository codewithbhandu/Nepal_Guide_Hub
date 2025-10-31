from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Package

def package_list(request):
    packages = Package.objects.filter(is_active=True, agency__is_verified=True)

    # Search with PostgreSQL full-text search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        # Use PostgreSQL full-text search with ranking for better relevance
        search_vector = SearchVector('title', weight='A') + \
                        SearchVector('description', weight='B') + \
                        SearchVector('package_type', weight='C') + \
                        SearchVector('best_season', weight='C') + \
                        SearchVector('agency__name', weight='D')
        search_q = SearchQuery(search_query)
        
        packages = packages.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_q)
        ).filter(search=search_q)

    # Filtering
    package_type = request.GET.get('type')
    difficulty = request.GET.get('difficulty')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if package_type:
        packages = packages.filter(package_type=package_type)
    if difficulty:
        packages = packages.filter(difficulty_level=difficulty)
    if min_price:
        packages = packages.filter(price_per_person__gte=min_price)
    if max_price:
        packages = packages.filter(price_per_person__lte=max_price)

    # Sorting
    sort_by = request.GET.get('sort', 'created_at')
    if sort_by == 'price_low':
        packages = packages.order_by('price_per_person')
    elif sort_by == 'price_high':
        packages = packages.order_by('-price_per_person')
    elif sort_by == 'rating':
        packages = packages.order_by('-agency__rating', '-agency__total_ratings', '-created_at')
    elif sort_by == 'relevance' and search_query:
        # Sort by search relevance if search query is present
        packages = packages.order_by('-rank', '-created_at')
    else:
        # If search query exists but no explicit sort, order by relevance
        if search_query:
            packages = packages.order_by('-rank', '-created_at')
        else:
            packages = packages.order_by('-created_at')

    # Pagination
    paginator = Paginator(packages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'package_types': Package.PACKAGE_TYPES,
        'difficulty_levels': Package.DIFFICULTY_LEVELS,
        'current_filters': {
            'type': package_type,
            'difficulty': difficulty,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort_by,
        }
    }
    return render(request, 'packages/package_list.html', context)

def package_detail(request, slug):
    # Redirect to the core public detail view
    from django.shortcuts import redirect
    return redirect('core:package_detail', slug=slug)
