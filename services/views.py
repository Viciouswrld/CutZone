from django.db.models import Q
from django.shortcuts import render

from .models import Service


def service_list(request):
    """Public services page with simple search."""
    query = request.GET.get("q", "").strip()
    services = Service.objects.filter(is_active=True)
    if query:
        services = services.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    return render(
        request,
        "services/service_list.html",
        {"services": services, "query": query},
    )
