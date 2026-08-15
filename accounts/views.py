import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from bookings.models import Appointment

from .forms import ProfileForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, f"Welcome to CutZone, {user.first_name}! Your account is ready."
            )
            return redirect("accounts:dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def post_login_redirect(request):
    """Send staff to the admin dashboard, customers to theirs."""
    if request.user.is_staff:
        return redirect("dashboard:home")
    return redirect("accounts:dashboard")


@login_required
def dashboard(request):
    """Customer dashboard with stats and upcoming appointments."""
    today = datetime.date.today()
    now = datetime.datetime.now().time()
    appts = Appointment.objects.filter(customer=request.user).select_related(
        "barber", "service"
    )

    upcoming = (
        appts.filter(status__in=Appointment.ACTIVE_STATUSES)
        .filter(date__gte=today)
        .order_by("date", "start_time")
    )
    # Remove today's appointments whose start time already passed.
    upcoming = [
        a for a in upcoming if not (a.date == today and a.start_time < now)
    ][:5]

    todays = appts.filter(date=today, status__in=Appointment.ACTIVE_STATUSES)

    context = {
        "upcoming": upcoming,
        "todays": todays,
        "total_count": appts.count(),
        "completed_count": appts.filter(status=Appointment.STATUS_COMPLETED).count(),
        "cancelled_count": appts.filter(status=Appointment.STATUS_CANCELLED).count(),
        "pending_count": appts.filter(status=Appointment.STATUS_PENDING).count(),
    }
    return render(request, "accounts/dashboard.html", context)


@login_required
def profile(request):
    return render(request, "accounts/profile.html")


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, "accounts/profile_edit.html", {"form": form})
