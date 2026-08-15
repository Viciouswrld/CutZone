"""
Custom admin dashboard for CutZone (separate from Django's /admin/).

Every view is protected with @staff_member_required so normal customers
cannot access any management page.
"""

import calendar
import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from barbers.models import Barber, BarberSchedule
from bookings.models import Appointment
from core.models import ContactMessage
from reviews.models import Review
from services.models import Service

from .forms import BarberForm, ScheduleFormSet, ServiceForm

staff_required = staff_member_required(login_url="accounts:login")


# --------------------------------------------------------------------------- #
# Dashboard home — statistics
# --------------------------------------------------------------------------- #
@staff_required
def home(request):
    today = datetime.date.today()
    appts = Appointment.objects.all()

    revenue = (
        appts.filter(status=Appointment.STATUS_COMPLETED).aggregate(
            total=Sum("price")
        )["total"]
        or 0
    )

    todays = (
        appts.filter(date=today)
        .select_related("customer", "barber", "service")
        .order_by("start_time")
    )
    upcoming = (
        appts.filter(
            date__gt=today, status__in=Appointment.ACTIVE_STATUSES
        )
        .select_related("customer", "barber", "service")
        .order_by("date", "start_time")[:8]
    )

    context = {
        "total_customers": User.objects.filter(is_staff=False).count(),
        "total_barbers": Barber.objects.count(),
        "total_services": Service.objects.count(),
        "total_appointments": appts.count(),
        "todays_count": todays.count(),
        "pending_count": appts.filter(status=Appointment.STATUS_PENDING).count(),
        "completed_count": appts.filter(status=Appointment.STATUS_COMPLETED).count(),
        "cancelled_count": appts.filter(status=Appointment.STATUS_CANCELLED).count(),
        "revenue": revenue,
        "todays": todays,
        "upcoming": upcoming,
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
    }
    return render(request, "dashboard/home.html", context)


# --------------------------------------------------------------------------- #
# Appointments — list, filter, search, status changes
# --------------------------------------------------------------------------- #
@staff_required
def appointments(request):
    qs = Appointment.objects.select_related("customer", "barber", "service")

    # Search + filters
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    barber_id = request.GET.get("barber", "")
    service_id = request.GET.get("service", "")
    date = request.GET.get("date", "")
    when = request.GET.get("when", "")  # today / upcoming shortcut

    if q:
        qs = qs.filter(
            Q(reference__icontains=q)
            | Q(customer__username__icontains=q)
            | Q(customer__first_name__icontains=q)
            | Q(customer__last_name__icontains=q)
            | Q(customer__email__icontains=q)
        )
    if status in dict(Appointment.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if barber_id.isdigit():
        qs = qs.filter(barber_id=barber_id)
    if service_id.isdigit():
        qs = qs.filter(service_id=service_id)
    if date:
        try:
            qs = qs.filter(date=datetime.date.fromisoformat(date))
        except ValueError:
            pass
    today = datetime.date.today()
    if when == "today":
        qs = qs.filter(date=today)
    elif when == "upcoming":
        qs = qs.filter(date__gte=today, status__in=Appointment.ACTIVE_STATUSES)

    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "page": page,
        "q": q,
        "status": status,
        "barber_id": barber_id,
        "service_id": service_id,
        "date": date,
        "when": when,
        "barbers": Barber.objects.all(),
        "services": Service.objects.all(),
        "statuses": Appointment.STATUS_CHOICES,
    }
    return render(request, "dashboard/appointments.html", context)


@staff_required
def appointment_set_status(request, pk, new_status):
    """Approve / complete / cancel an appointment from the dashboard."""
    appt = get_object_or_404(Appointment, pk=pk)
    if request.method != "POST":
        return redirect("dashboard:appointments")
    if new_status not in dict(Appointment.STATUS_CHOICES):
        messages.error(request, "Invalid status.")
    else:
        appt.status = new_status
        appt.save()
        messages.success(
            request,
            f"Appointment {appt.reference} marked as {appt.get_status_display()}.",
        )
    return redirect(request.META.get("HTTP_REFERER", "dashboard:appointments"))


# --------------------------------------------------------------------------- #
# Calendar view — day / week / month
# --------------------------------------------------------------------------- #
@staff_required
def calendar_view(request):
    """Simple server-rendered calendar of appointments (day/week/month)."""
    mode = request.GET.get("mode", "week")
    if mode not in ("day", "week", "month"):
        mode = "week"

    try:
        anchor = datetime.date.fromisoformat(request.GET.get("date", ""))
    except ValueError:
        anchor = datetime.date.today()

    today = datetime.date.today()

    if mode == "day":
        start, end = anchor, anchor
        prev_d = anchor - datetime.timedelta(days=1)
        next_d = anchor + datetime.timedelta(days=1)
        title = anchor.strftime("%A, %d %B %Y")
    elif mode == "week":
        start = anchor - datetime.timedelta(days=anchor.weekday())
        end = start + datetime.timedelta(days=6)
        prev_d = anchor - datetime.timedelta(days=7)
        next_d = anchor + datetime.timedelta(days=7)
        title = f"Week of {start:%d %b} – {end:%d %b %Y}"
    else:  # month
        start = anchor.replace(day=1)
        last_day = calendar.monthrange(anchor.year, anchor.month)[1]
        end = anchor.replace(day=last_day)
        prev_d = (start - datetime.timedelta(days=1)).replace(day=1)
        next_d = (end + datetime.timedelta(days=1))
        title = anchor.strftime("%B %Y")

    appts = (
        Appointment.objects.filter(date__gte=start, date__lte=end)
        .select_related("customer", "barber", "service")
        .order_by("date", "start_time")
    )

    # Group appointments per day for the template.
    days = []
    d = start
    while d <= end:
        days.append({"date": d, "appointments": [a for a in appts if a.date == d]})
        d += datetime.timedelta(days=1)

    context = {
        "mode": mode,
        "anchor": anchor,
        "today": today,
        "title": title,
        "days": days,
        "prev_date": prev_d.isoformat(),
        "next_date": next_d.isoformat(),
    }
    return render(request, "dashboard/calendar.html", context)


# --------------------------------------------------------------------------- #
# Customers
# --------------------------------------------------------------------------- #
@staff_required
def customers(request):
    q = request.GET.get("q", "").strip()
    qs = (
        User.objects.filter(is_staff=False)
        .annotate(appointment_count=Count("appointments"))
        .order_by("-date_joined")
    )
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/customers.html", {"page": page, "q": q})


@staff_required
def customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    appts = customer.appointments.select_related("barber", "service")
    return render(
        request,
        "dashboard/customer_detail.html",
        {"customer": customer, "appointments": appts},
    )


@staff_required
def customer_toggle_active(request, pk):
    customer = get_object_or_404(User, pk=pk, is_staff=False)
    if request.method == "POST":
        customer.is_active = not customer.is_active
        customer.save()
        state = "activated" if customer.is_active else "deactivated"
        messages.success(request, f"Account '{customer.username}' {state}.")
    return redirect("dashboard:customers")


# --------------------------------------------------------------------------- #
# Barbers
# --------------------------------------------------------------------------- #
@staff_required
def barbers(request):
    return render(
        request, "dashboard/barbers.html", {"barbers": Barber.objects.all()}
    )


@staff_required
def barber_add(request):
    if request.method == "POST":
        form = BarberForm(request.POST, request.FILES)
        if form.is_valid():
            barber = form.save()
            # Give the new barber a default Mon–Sat schedule.
            for weekday in range(7):
                BarberSchedule.objects.create(
                    barber=barber,
                    weekday=weekday,
                    is_working=weekday != 6,  # Sunday off by default
                )
            messages.success(request, f"Barber '{barber.name}' added.")
            return redirect("dashboard:barbers")
    else:
        form = BarberForm()
    return render(
        request, "dashboard/barber_form.html", {"form": form, "title": "Add Barber"}
    )


@staff_required
def barber_edit(request, pk):
    barber = get_object_or_404(Barber, pk=pk)
    if request.method == "POST":
        form = BarberForm(request.POST, request.FILES, instance=barber)
        if form.is_valid():
            form.save()
            messages.success(request, f"Barber '{barber.name}' updated.")
            return redirect("dashboard:barbers")
    else:
        form = BarberForm(instance=barber)
    return render(
        request,
        "dashboard/barber_form.html",
        {"form": form, "title": f"Edit {barber.name}", "barber": barber},
    )


@staff_required
def barber_toggle_active(request, pk):
    barber = get_object_or_404(Barber, pk=pk)
    if request.method == "POST":
        barber.is_active = not barber.is_active
        barber.save()
        state = "activated" if barber.is_active else "deactivated"
        messages.success(request, f"Barber '{barber.name}' {state}.")
    return redirect("dashboard:barbers")


@staff_required
def barber_delete(request, pk):
    barber = get_object_or_404(Barber, pk=pk)
    if request.method == "POST":
        if barber.appointments.exists():
            # Keep history intact — deactivate instead of deleting.
            barber.is_active = False
            barber.save()
            messages.warning(
                request,
                f"'{barber.name}' has appointment history, so the profile was "
                "deactivated instead of deleted.",
            )
        else:
            barber.delete()
            messages.success(request, f"Barber '{barber.name}' deleted.")
    return redirect("dashboard:barbers")


# --------------------------------------------------------------------------- #
# Barber schedules
# --------------------------------------------------------------------------- #
@staff_required
def schedules(request):
    barbers_qs = Barber.objects.prefetch_related("schedules")
    return render(request, "dashboard/schedules.html", {"barbers": barbers_qs})


@staff_required
def schedule_edit(request, barber_pk):
    barber = get_object_or_404(Barber, pk=barber_pk)

    # Ensure all 7 weekday rows exist so the formset is complete.
    for weekday in range(7):
        BarberSchedule.objects.get_or_create(
            barber=barber, weekday=weekday,
            defaults={"is_working": weekday != 6},
        )

    qs = barber.schedules.order_by("weekday")
    if request.method == "POST":
        formset = ScheduleFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, f"Schedule for {barber.name} updated.")
            return redirect("dashboard:schedules")
    else:
        formset = ScheduleFormSet(queryset=qs)

    return render(
        request,
        "dashboard/schedule_edit.html",
        {"barber": barber, "formset": formset},
    )


# --------------------------------------------------------------------------- #
# Services
# --------------------------------------------------------------------------- #
@staff_required
def services(request):
    return render(
        request, "dashboard/services.html", {"services": Service.objects.all()}
    )


@staff_required
def service_add(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save()
            messages.success(request, f"Service '{service.name}' added.")
            return redirect("dashboard:services")
    else:
        form = ServiceForm()
    return render(
        request, "dashboard/service_form.html", {"form": form, "title": "Add Service"}
    )


@staff_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"Service '{service.name}' updated.")
            return redirect("dashboard:services")
    else:
        form = ServiceForm(instance=service)
    return render(
        request,
        "dashboard/service_form.html",
        {"form": form, "title": f"Edit {service.name}"},
    )


@staff_required
def service_toggle_active(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        service.is_active = not service.is_active
        service.save()
        state = "activated" if service.is_active else "deactivated"
        messages.success(request, f"Service '{service.name}' {state}.")
    return redirect("dashboard:services")


@staff_required
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        if service.appointments.exists():
            service.is_active = False
            service.save()
            messages.warning(
                request,
                f"'{service.name}' has appointment history, so it was "
                "deactivated instead of deleted.",
            )
        else:
            service.delete()
            messages.success(request, f"Service '{service.name}' deleted.")
    return redirect("dashboard:services")


# --------------------------------------------------------------------------- #
# Reviews moderation
# --------------------------------------------------------------------------- #
@staff_required
def reviews(request):
    qs = Review.objects.select_related(
        "customer", "appointment__barber", "appointment__service"
    )
    return render(request, "dashboard/reviews.html", {"reviews": qs})


@staff_required
def review_toggle_approved(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == "POST":
        review.is_approved = not review.is_approved
        review.save()
        state = "approved" if review.is_approved else "hidden"
        messages.success(request, f"Review by {review.customer.username} {state}.")
    return redirect("dashboard:reviews")


@staff_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == "POST":
        review.delete()
        messages.success(request, "Review deleted.")
    return redirect("dashboard:reviews")


# --------------------------------------------------------------------------- #
# Contact messages
# --------------------------------------------------------------------------- #
@staff_required
def contact_messages(request):
    msgs = ContactMessage.objects.all()
    return render(request, "dashboard/messages.html", {"contact_messages": msgs})


@staff_required
def message_mark_read(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        msg.is_read = True
        msg.save()
    return redirect("dashboard:messages")


@staff_required
def message_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        msg.delete()
        messages.success(request, "Message deleted.")
    return redirect("dashboard:messages")
