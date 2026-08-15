from django.contrib import messages
from django.shortcuts import redirect, render

from barbers.models import Barber
from reviews.models import Review
from services.models import Service

from .forms import ContactForm


def home(request):
    """Public homepage."""
    context = {
        "services": Service.objects.filter(is_active=True)[:3],
        "barbers": Barber.objects.filter(is_active=True)[:4],
        "reviews": Review.objects.filter(is_approved=True).select_related(
            "customer", "appointment__barber", "appointment__service"
        )[:6],
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you! Your message has been sent. We will get back to you soon.",
            )
            return redirect("core:contact")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form})


def handler404(request, exception):
    return render(request, "errors/404.html", status=404)


def handler403(request, exception):
    return render(request, "errors/403.html", status=403)


def handler500(request):
    return render(request, "errors/500.html", status=500)
