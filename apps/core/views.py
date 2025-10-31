from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import SearchForm, ContactForm, NewsletterForm

def home(request):
    # Import models to get actual data
    from apps.packages.models import Package
    from apps.guides.models import Guide
    from apps.accounts.models import Agency
    
    # Get featured content
    featured_packages = Package.objects.filter(is_active=True, featured=True, agency__is_verified=True)[:6]
    top_agencies = Agency.objects.filter(is_verified=True)[:6]
    top_guides = Guide.objects.filter(is_available=True, agency__is_verified=True)[:6]
    
    # Get tourist-specific context if user is logged in as tourist
    context = {
        'is_tourist': request.user.is_authenticated and request.user.user_type == 'tourist',
        'featured_packages': featured_packages,
        'top_agencies': top_agencies,
        'top_guides': top_guides,
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
    form = SearchForm(request.GET) if request.GET else SearchForm()
    results = {
        'packages': [],
        'guides': [],
        'agencies': [],
    }

    query = ''
    if form.is_valid():
        from apps.packages.models import Package
        from apps.guides.models import Guide
        from apps.accounts.models import Agency

        query = (form.cleaned_data.get('query') or '').strip()
        search_type = form.cleaned_data.get('search_type') or 'all'
        package_type_filter = form.cleaned_data.get('package_type') or ''
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')

        # Tokenize query for simple term-weighted search
        tokens = [t for t in query.lower().split() if t]

        def score_text(text: str, weights: dict) -> int:
            if not query:
                return 0
            text_l = (text or '').lower()
            score = 0
            # Exact phrase boost
            if query and query in text_l:
                score += weights.get('phrase', 5)
            # Token matches
            for tok in tokens:
                if tok in text_l:
                    score += weights.get('token', 2)
            return score

        # Build base filters
        package_q = Q(is_active=True, agency__is_verified=True)
        if package_type_filter:
            package_q &= Q(package_type=package_type_filter)
        if min_price is not None:
            package_q &= Q(price_per_person__gte=min_price)
        if max_price is not None:
            package_q &= Q(price_per_person__lte=max_price)

        if search_type in ('all', 'packages'):
            pkg_text_q = Q()
            if query:
                pkg_text_q |= Q(title__icontains=query)
                pkg_text_q |= Q(description__icontains=query)
                pkg_text_q |= Q(best_season__icontains=query)
                pkg_text_q |= Q(package_type__icontains=query)
                pkg_text_q |= Q(agency__name__icontains=query)
            packages_qs = Package.objects.filter(package_q & (pkg_text_q if query else package_q)).select_related('agency')[:100]
            ranked_packages = []
            for p in packages_qs:
                s = 0
                s += score_text(p.title, {'phrase': 10, 'token': 3})
                s += score_text(p.description, {'phrase': 6, 'token': 2})
                s += score_text(p.best_season, {'phrase': 3, 'token': 1})
                s += score_text(p.agency.name, {'phrase': 4, 'token': 2})
                # Metadata boosts
                if p.featured:
                    s += 5
                s += min(max(p.views_count // 50, 0), 20)
                ranked_packages.append((s, p))
            ranked_packages.sort(key=lambda x: x[0], reverse=True)
            results['packages'] = [p for _, p in ranked_packages[:30]]

        if search_type in ('all', 'guides'):
            guide_q = Q(is_available=True, agency__is_verified=True)
            guide_text_q = Q()
            if query:
                guide_text_q |= Q(name__icontains=query)
                guide_text_q |= Q(bio__icontains=query)
                guide_text_q |= Q(places_covered__icontains=query)
                guide_text_q |= Q(certifications__icontains=query)
                guide_text_q |= Q(agency__name__icontains=query)
            guides_qs = Guide.objects.filter(guide_q & (guide_text_q if query else guide_q)).select_related('agency')[:100]
            ranked_guides = []
            for g in guides_qs:
                s = 0
                s += score_text(g.name, {'phrase': 8, 'token': 3})
                s += score_text(g.bio, {'phrase': 5, 'token': 2})
                s += score_text(g.places_covered, {'phrase': 4, 'token': 2})
                s += score_text(g.agency.name, {'phrase': 3, 'token': 1})
                # Metadata boosts
                s += int(float(g.rating or 0) * 2)
                s += min(max(g.total_ratings // 10, 0), 15)
                ranked_guides.append((s, g))
            ranked_guides.sort(key=lambda x: x[0], reverse=True)
            results['guides'] = [g for _, g in ranked_guides[:30]]

        if search_type in ('all', 'agencies'):
            agency_q = Q(is_verified=True)
            agency_text_q = Q()
            if query:
                agency_text_q |= Q(name__icontains=query)
                agency_text_q |= Q(description__icontains=query)
                agency_text_q |= Q(address__icontains=query)
            agencies_qs = Agency.objects.filter(agency_q & (agency_text_q if query else agency_q))[:100]
            ranked_agencies = []
            for a in agencies_qs:
                s = 0
                s += score_text(a.name, {'phrase': 7, 'token': 3})
                s += score_text(a.description, {'phrase': 4, 'token': 2})
                # Metadata boosts
                s += int(float(a.rating or 0)) * 2
                s += min(max(a.total_ratings // 10, 0), 15)
                s += min(a.packages.count(), 10)
                ranked_agencies.append((s, a))
            ranked_agencies.sort(key=lambda x: x[0], reverse=True)
            results['agencies'] = [a for _, a in ranked_agencies[:30]]

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

# Public detail views
def package_detail(request, slug):
    from apps.packages.models import Package
    from django.shortcuts import get_object_or_404
    
    package = get_object_or_404(Package, slug=slug, is_active=True)
    package.increment_views()  # Track views
    
    context = {
        'package': package,
        'is_authenticated': request.user.is_authenticated,
        'user_type': request.user.user_type if request.user.is_authenticated else None,
    }
    return render(request, 'core/package_detail.html', context)

def guide_detail(request, guide_id):
    from apps.guides.models import Guide
    from django.shortcuts import get_object_or_404
    
    guide = get_object_or_404(Guide, id=guide_id, is_available=True)
    
    context = {
        'guide': guide,
        'is_authenticated': request.user.is_authenticated,
        'user_type': request.user.user_type if request.user.is_authenticated else None,
    }
    return render(request, 'core/guide_detail.html', context)

def agency_detail(request, agency_id):
    from apps.accounts.models import Agency
    from django.shortcuts import get_object_or_404
    
    agency = get_object_or_404(Agency, id=agency_id, is_verified=True)
    
    context = {
        'agency': agency,
        'is_authenticated': request.user.is_authenticated,
        'user_type': request.user.user_type if request.user.is_authenticated else None,
    }
    return render(request, 'core/agency_detail.html', context)
