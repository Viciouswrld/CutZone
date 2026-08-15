import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from barbers.models import Barber
from services.models import Service


class Appointment(models.Model):
    """A customer booking with a barber for a specific service and time."""

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    # Statuses that block a time slot from being booked by someone else.
    ACTIVE_STATUSES = [STATUS_PENDING, STATUS_CONFIRMED]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="appointments"
    )
    barber = models.ForeignKey(
        Barber, on_delete=models.PROTECT, related_name="appointments"
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT, related_name="appointments"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Snapshot the price so history is preserved if the service price changes.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-start_time"]
        constraints = [
            # Database-level safeguard: one barber cannot have two active
            # appointments starting at the same date & time.
            models.UniqueConstraint(
                fields=["barber", "date", "start_time"],
                condition=models.Q(status__in=["pending", "confirmed"]),
                name="unique_active_barber_slot",
            )
        ]

    def __str__(self):
        return f"{self.reference} — {self.customer.username} with {self.barber.name}"

    # ------------------------------------------------------------------ #
    # Reference generation: CZ-<year>-<sequential number>
    # ------------------------------------------------------------------ #
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        year = datetime.date.today().year
        prefix = f"CZ-{year}-"
        last = (
            Appointment.objects.filter(reference__startswith=prefix)
            .order_by("-reference")
            .first()
        )
        next_number = 1
        if last:
            try:
                next_number = int(last.reference.split("-")[-1]) + 1
            except ValueError:
                next_number = Appointment.objects.count() + 1
        return f"{prefix}{next_number:04d}"

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @property
    def duration_minutes(self):
        start = datetime.datetime.combine(self.date, self.start_time)
        end = datetime.datetime.combine(self.date, self.end_time)
        return int((end - start).total_seconds() // 60)

    @property
    def is_upcoming(self):
        now = datetime.datetime.now()
        start = datetime.datetime.combine(self.date, self.start_time)
        return start >= now and self.status in self.ACTIVE_STATUSES

    @property
    def is_past(self):
        now = datetime.datetime.now()
        start = datetime.datetime.combine(self.date, self.start_time)
        return start < now

    @property
    def can_cancel(self):
        return self.status in self.ACTIVE_STATUSES and not self.is_past

    @property
    def can_reschedule(self):
        return self.status in self.ACTIVE_STATUSES and not self.is_past

    @property
    def can_review(self):
        return (
            self.status == self.STATUS_COMPLETED
            and not hasattr(self, "review")
        )
