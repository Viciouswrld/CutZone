from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Appointment

from .forms import ReviewForm
from .models import Review


@login_required
def leave_review(request, appointment_pk):
    """Customers may review only their own completed appointments — once."""
    appt = get_object_or_404(
        Appointment.objects.select_related("barber", "service"),
        pk=appointment_pk,
        customer=request.user,
    )

    if appt.status != Appointment.STATUS_COMPLETED:
        messages.error(request, "You can only review completed appointments.")
        return redirect("bookings:detail", pk=appt.pk)

    if hasattr(appt, "review"):
        messages.info(request, "You have already reviewed this appointment.")
        return redirect("bookings:detail", pk=appt.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appt
            review.customer = request.user
            review.save()
            messages.success(request, "Thank you for your review!")
            return redirect("bookings:detail", pk=appt.pk)
    else:
        form = ReviewForm()

    return render(request, "reviews/leave_review.html", {"form": form, "appt": appt})
