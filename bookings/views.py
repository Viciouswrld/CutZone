import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from barbers.models import Barber
from services.models import Service

from .availability import get_available_slots
from .forms import BookingForm
from .models import Appointment


# --------------------------------------------------------------------------- #
# AJAX endpoint: available time slots for barber + service + date
# --------------------------------------------------------------------------- #
@login_required
def available_slots(request):
    """Return JSON list of valid start times. Used by the booking page JS."""
    try:
        service = Service.objects.get(
            pk=request.GET.get("service"), is_active=True
        )
        barber = Barber.objects.get(pk=request.GET.get("barber"), is_active=True)
        date = datetime.date.fromisoformat(request.GET.get("date", ""))
    except (Service.DoesNotExist, Barber.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"slots": [], "error": "Invalid selection."})

    exclude = None
    exclude_pk = request.GET.get("exclude")
    if exclude_pk:
        exclude = Appointment.objects.filter(
            pk=exclude_pk, customer=request.user
        ).first()

    slots = get_available_slots(barber, service, date, exclude_appointment=exclude)
    return JsonResponse(
        {
            "slots": [
                {"value": s.strftime("%H:%M"), "label": s.strftime("%I:%M %p").lstrip("0")}
                for s in slots
            ]
        }
    )


# --------------------------------------------------------------------------- #
# Booking flow
# --------------------------------------------------------------------------- #
@login_required
def book_appointment(request):
    """Service → Barber → Date → Time → Confirm, on one guided page."""
    services = Service.objects.filter(is_active=True)
    barbers = Barber.objects.filter(is_active=True)

    # Pre-selection via ?service= or ?barber= links from public pages.
    preselect_service = request.GET.get("service", "")
    preselect_barber = request.GET.get("barber", "")

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            service = form.cleaned_data["service"]
            barber = form.cleaned_data["barber"]
            date = form.cleaned_data["date"]
            start = form.cleaned_data["start_time"]
            end_dt = datetime.datetime.combine(date, start) + datetime.timedelta(
                minutes=service.duration_minutes
            )
            try:
                # Atomic + unique constraint guards against race conditions.
                with transaction.atomic():
                    appt = Appointment.objects.create(
                        customer=request.user,
                        barber=barber,
                        service=service,
                        date=date,
                        start_time=start,
                        end_time=end_dt.time(),
                        price=service.price,
                        notes=form.cleaned_data.get("notes", ""),
                        status=Appointment.STATUS_PENDING,
                    )
            except IntegrityError:
                messages.error(
                    request,
                    "Sorry — that slot was booked a moment ago. Please pick another time.",
                )
            else:
                messages.success(
                    request,
                    f"Your appointment has been booked! Reference: {appt.reference}",
                )
                return redirect("bookings:confirmation", pk=appt.pk)
        else:
            for err in form.non_field_errors():
                messages.error(request, err)
    else:
        form = BookingForm()

    return render(
        request,
        "bookings/book.html",
        {
            "form": form,
            "services": services,
            "barbers": barbers,
            "preselect_service": preselect_service,
            "preselect_barber": preselect_barber,
            "min_date": datetime.date.today().isoformat(),
            "max_date": (datetime.date.today() + datetime.timedelta(days=60)).isoformat(),
        },
    )


@login_required
def confirmation(request, pk):
    """Printable booking confirmation / receipt."""
    appt = get_object_or_404(
        Appointment.objects.select_related("barber", "service"),
        pk=pk,
        customer=request.user,
    )
    return render(request, "bookings/confirmation.html", {"appt": appt})


@login_required
def my_appointments(request):
    """List of the customer's upcoming + past appointments (history)."""
    appts = (
        Appointment.objects.filter(customer=request.user)
        .select_related("barber", "service")
        .order_by("-date", "-start_time")
    )
    status = request.GET.get("status", "")
    if status in dict(Appointment.STATUS_CHOICES):
        appts = appts.filter(status=status)

    today = datetime.date.today()
    upcoming = [a for a in appts if a.is_upcoming]
    upcoming.sort(key=lambda a: (a.date, a.start_time))
    past = [a for a in appts if not a.is_upcoming]

    return render(
        request,
        "bookings/my_appointments.html",
        {
            "upcoming": upcoming,
            "past": past,
            "status": status,
            "statuses": Appointment.STATUS_CHOICES,
            "today": today,
        },
    )


@login_required
def appointment_detail(request, pk):
    appt = get_object_or_404(
        Appointment.objects.select_related("barber", "service"),
        pk=pk,
        customer=request.user,
    )
    return render(request, "bookings/detail.html", {"appt": appt})


@login_required
def cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, customer=request.user)
    if not appt.can_cancel:
        messages.error(request, "This appointment can no longer be cancelled.")
        return redirect("bookings:detail", pk=appt.pk)

    if request.method == "POST":
        appt.status = Appointment.STATUS_CANCELLED
        appt.save()
        messages.success(
            request, f"Your appointment {appt.reference} has been cancelled."
        )
        return redirect("bookings:my_appointments")

    # GET shows a confirmation page.
    return render(request, "bookings/cancel_confirm.html", {"appt": appt})


@login_required
def reschedule_appointment(request, pk):
    """Move an existing appointment to a new date/time — no duplicates."""
    appt = get_object_or_404(
        Appointment.objects.select_related("barber", "service"),
        pk=pk,
        customer=request.user,
    )
    if not appt.can_reschedule:
        messages.error(request, "This appointment can no longer be rescheduled.")
        return redirect("bookings:detail", pk=appt.pk)

    if request.method == "POST":
        data = request.POST.copy()
        # Service and barber stay the same when rescheduling.
        data["service"] = appt.service_id
        data["barber"] = appt.barber_id
        form = BookingForm(data, exclude_appointment=appt)
        if form.is_valid():
            date = form.cleaned_data["date"]
            start = form.cleaned_data["start_time"]
            end_dt = datetime.datetime.combine(date, start) + datetime.timedelta(
                minutes=appt.service.duration_minutes
            )
            try:
                with transaction.atomic():
                    appt.date = date
                    appt.start_time = start
                    appt.end_time = end_dt.time()
                    appt.status = Appointment.STATUS_PENDING
                    appt.save()
            except IntegrityError:
                messages.error(
                    request,
                    "Sorry — that slot was booked a moment ago. Please pick another time.",
                )
            else:
                messages.success(
                    request,
                    f"Your appointment {appt.reference} has been rescheduled to "
                    f"{date:%A, %d %B %Y} at {start:%I:%M %p}.",
                )
                return redirect("bookings:detail", pk=appt.pk)
        else:
            for err in form.non_field_errors():
                messages.error(request, err)

    return render(
        request,
        "bookings/reschedule.html",
        {
            "appt": appt,
            "min_date": datetime.date.today().isoformat(),
            "max_date": (datetime.date.today() + datetime.timedelta(days=60)).isoformat(),
        },
    )
