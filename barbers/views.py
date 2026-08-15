from django.db.models import Avg, Count, Q
from django.shortcuts import render

from .models import Barber


def barber_list(request):
    """Public barbers page with simple search."""
    query = request.GET.get("q", "").strip()
    barbers = Barber.objects.filter(is_active=True).annotate(
        avg_rating=Avg(
            "appointments__review__rating",
            filter=Q(appointments__review__is_approved=True),
        ),
        review_count=Count(
            "appointments__review",
            filter=Q(appointments__review__is_approved=True),
        ),
    )
    if query:
        barbers = barbers.filter(
            Q(name__icontains=query) | Q(specialization__icontains=query)
        )
    return render(
        request,
        "barbers/barber_list.html",
        {"barbers": barbers, "query": query},
    )
