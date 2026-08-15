"""
Booking-system tests for CutZone.

Run with:  python manage.py test bookings
"""

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from barbers.models import Barber, BarberSchedule
from services.models import Service

from .availability import get_available_slots, validate_booking
from .models import Appointment


def next_weekday(weekday=0, min_days_ahead=2):
    """Return the next date that falls on `weekday` (0=Monday)."""
    d = datetime.date.today() + datetime.timedelta(days=min_days_ahead)
    while d.weekday() != weekday:
        d += datetime.timedelta(days=1)
    return d


class BookingRulesTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user("alice", password="pass12345")
        self.other = User.objects.create_user("bob", password="pass12345")
        self.barber = Barber.objects.create(name="Victor")
        for wd in range(7):
            BarberSchedule.objects.create(
                barber=self.barber, weekday=wd, is_working=wd != 6
            )
        self.haircut = Service.objects.create(
            name="Haircut", price=3000, duration_minutes=30
        )
        self.full = Service.objects.create(
            name="Full Package", price=6000, duration_minutes=60
        )
        self.monday = next_weekday(0)

    def make_appt(self, start, service=None, customer=None, status="pending"):
        service = service or self.haircut
        end = (
            datetime.datetime.combine(self.monday, start)
            + datetime.timedelta(minutes=service.duration_minutes)
        ).time()
        return Appointment.objects.create(
            customer=customer or self.customer,
            barber=self.barber,
            service=service,
            date=self.monday,
            start_time=start,
            end_time=end,
            price=service.price,
            status=status,
        )

    # ---- core rules -------------------------------------------------- #
    def test_no_overlapping_bookings(self):
        """Two customers cannot book the same barber at overlapping times."""
        self.make_appt(datetime.time(10, 0))  # 10:00–10:30
        for t in [(9, 45), (10, 0), (10, 15)]:
            errors = validate_booking(
                self.barber, self.haircut, self.monday, datetime.time(*t)
            )
            self.assertTrue(errors, f"{t} should conflict")
        # 10:30 starts exactly when the first booking ends — allowed.
        self.assertFalse(
            validate_booking(
                self.barber, self.haircut, self.monday, datetime.time(10, 30)
            )
        )

    def test_cannot_book_past(self):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        errors = validate_booking(
            self.barber, self.haircut, yesterday, datetime.time(10, 0)
        )
        self.assertTrue(errors)

    def test_cannot_book_outside_hours(self):
        errors = validate_booking(
            self.barber, self.haircut, self.monday, datetime.time(7, 0)
        )
        self.assertTrue(errors)
        # 60-minute service at 18:30 finishes at 19:30 — after closing.
        errors = validate_booking(
            self.barber, self.full, self.monday, datetime.time(18, 30)
        )
        self.assertTrue(errors)
        # 60-minute service at 18:00 finishes exactly at close — allowed.
        self.assertFalse(
            validate_booking(self.barber, self.full, self.monday, datetime.time(18, 0))
        )

    def test_cannot_book_inactive_barber_or_service(self):
        self.barber.is_active = False
        self.barber.save()
        self.assertTrue(
            validate_booking(self.barber, self.haircut, self.monday, datetime.time(10, 0))
        )
        self.barber.is_active = True
        self.barber.save()
        self.haircut.is_active = False
        self.haircut.save()
        self.assertTrue(
            validate_booking(self.barber, self.haircut, self.monday, datetime.time(10, 0))
        )

    def test_cannot_book_on_day_off(self):
        sunday = next_weekday(6)
        self.assertTrue(
            validate_booking(self.barber, self.haircut, sunday, datetime.time(10, 0))
        )
        self.assertEqual(get_available_slots(self.barber, self.haircut, sunday), [])

    def test_slots_respect_duration_and_conflicts(self):
        slots = get_available_slots(self.barber, self.full, self.monday)
        self.assertEqual(slots[-1], datetime.time(18, 0))  # last valid 60-min start
        self.make_appt(datetime.time(10, 0))  # 10:00–10:30 busy
        slots = get_available_slots(self.barber, self.haircut, self.monday)
        strs = [s.strftime("%H:%M") for s in slots]
        for blocked in ("09:45", "10:00", "10:15"):
            self.assertNotIn(blocked, strs)
        self.assertIn("10:30", strs)

    def test_cancelled_appointment_frees_slot(self):
        appt = self.make_appt(datetime.time(10, 0))
        appt.status = Appointment.STATUS_CANCELLED
        appt.save()
        self.assertFalse(
            validate_booking(self.barber, self.haircut, self.monday, datetime.time(10, 0))
        )

    def test_reschedule_cannot_conflict_but_own_slot_ok(self):
        appt = self.make_appt(datetime.time(10, 0))
        self.make_appt(datetime.time(12, 0), customer=self.other)
        # Moving onto the other booking must fail.
        self.assertTrue(
            validate_booking(
                self.barber, self.haircut, self.monday, datetime.time(12, 15),
                exclude_appointment=appt,
            )
        )
        # Keeping its own slot is fine (excluded from the conflict check).
        self.assertFalse(
            validate_booking(
                self.barber, self.haircut, self.monday, datetime.time(10, 0),
                exclude_appointment=appt,
            )
        )

    def test_unique_reference_generated(self):
        a = self.make_appt(datetime.time(9, 0))
        b = self.make_appt(datetime.time(11, 0))
        self.assertTrue(a.reference.startswith("CZ-"))
        self.assertNotEqual(a.reference, b.reference)

    # ---- view-level security ------------------------------------------ #
    def test_customer_cannot_view_others_appointment(self):
        appt = self.make_appt(datetime.time(10, 0))
        self.client.login(username="bob", password="pass12345")
        resp = self.client.get(reverse("bookings:detail", args=[appt.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_booking_requires_login(self):
        resp = self.client.get(reverse("bookings:book"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_dashboard_requires_staff(self):
        self.client.login(username="alice", password="pass12345")
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 302)  # redirected to login

    def test_booking_view_creates_appointment(self):
        self.client.login(username="alice", password="pass12345")
        resp = self.client.post(
            reverse("bookings:book"),
            {
                "service": self.haircut.pk,
                "barber": self.barber.pk,
                "date": self.monday.isoformat(),
                "start_time": "14:00",
                "notes": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        appt = Appointment.objects.get(customer=self.customer, start_time="14:00")
        self.assertEqual(appt.end_time, datetime.time(14, 30))
        self.assertEqual(appt.status, Appointment.STATUS_PENDING)

    def test_double_booking_rejected_at_view_level(self):
        self.make_appt(datetime.time(14, 0), customer=self.other)
        self.client.login(username="alice", password="pass12345")
        resp = self.client.post(
            reverse("bookings:book"),
            {
                "service": self.haircut.pk,
                "barber": self.barber.pk,
                "date": self.monday.isoformat(),
                "start_time": "14:00",
                "notes": "",
            },
        )
        # Stays on the booking page with an error — no new appointment.
        self.assertEqual(
            Appointment.objects.filter(customer=self.customer).count(), 0
        )
