"""
Time-slot generation and booking validation for CutZone.

The rules implemented here:

1. The shop is open 08:00–19:00 (settings.CUTZONE_OPEN_TIME / CLOSE_TIME).
2. A barber only works within his own schedule for that weekday.
3. A slot must fit the full service duration before closing/end of shift
   (e.g. a 60-minute service cannot start at 18:30).
4. A slot must not overlap any existing pending/confirmed appointment
   for that barber.
5. Slots in the past are never offered.

All of this is enforced on the backend — the frontend only displays what
this module returns.
"""

import datetime

from django.conf import settings

from bookings.models import Appointment


def shop_open_time() -> datetime.time:
    h, m = map(int, settings.CUTZONE_OPEN_TIME.split(":"))
    return datetime.time(h, m)


def shop_close_time() -> datetime.time:
    h, m = map(int, settings.CUTZONE_CLOSE_TIME.split(":"))
    return datetime.time(h, m)


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    """True when two [start, end) intervals overlap."""
    return start_a < end_b and start_b < end_a


def get_available_slots(barber, service, date, exclude_appointment=None):
    """
    Return a list of datetime.time objects that are valid start times for
    `service` with `barber` on `date`.

    `exclude_appointment` lets rescheduling ignore the appointment being
    moved so its own slot counts as free.
    """
    if barber is None or service is None or date is None:
        return []

    if not barber.is_active or not service.is_active:
        return []

    today = datetime.date.today()
    if date < today:
        return []

    # 1. Barber's schedule for this weekday.
    schedule = barber.schedule_for_day(date.weekday())
    if schedule is None:
        return []

    # 2. Working window = intersection of shop hours and barber's shift.
    open_t = max(shop_open_time(), schedule.start_time)
    close_t = min(shop_close_time(), schedule.end_time)
    if open_t >= close_t:
        return []

    duration = datetime.timedelta(minutes=service.duration_minutes)
    step = datetime.timedelta(minutes=settings.CUTZONE_SLOT_STEP_MINUTES)

    # 3. Existing active appointments for this barber on this date.
    existing = Appointment.objects.filter(
        barber=barber, date=date, status__in=Appointment.ACTIVE_STATUSES
    )
    if exclude_appointment is not None:
        existing = existing.exclude(pk=exclude_appointment.pk)
    busy = [
        (
            datetime.datetime.combine(date, a.start_time),
            datetime.datetime.combine(date, a.end_time),
        )
        for a in existing
    ]

    now = datetime.datetime.now()
    slots = []
    cursor = datetime.datetime.combine(date, open_t)
    closing = datetime.datetime.combine(date, close_t)

    while cursor + duration <= closing:
        slot_end = cursor + duration
        # Skip past times (for today).
        if cursor > now:
            if not any(_overlaps(cursor, slot_end, b0, b1) for b0, b1 in busy):
                slots.append(cursor.time())
        cursor += step

    return slots


def validate_booking(barber, service, date, start_time, exclude_appointment=None):
    """
    Full backend validation of a booking request.
    Returns a list of error strings — empty list means the booking is valid.
    """
    errors = []

    if not service or not service.is_active:
        errors.append("This service is not available for booking.")
    if not barber or not barber.is_active:
        errors.append("This barber is not available for booking.")
    if errors:
        return errors

    if date is None or start_time is None:
        return ["Please choose a valid date and time."]

    start_dt = datetime.datetime.combine(date, start_time)
    end_dt = start_dt + datetime.timedelta(minutes=service.duration_minutes)

    # Past bookings.
    if start_dt <= datetime.datetime.now():
        errors.append("You cannot book an appointment in the past.")

    # Shop hours.
    if start_time < shop_open_time():
        errors.append("The shop opens at 8:00 AM.")
    if end_dt.time() > shop_close_time() or end_dt.date() != date:
        errors.append(
            "This service would finish after closing time (7:00 PM). "
            "Please choose an earlier slot."
        )

    # Barber schedule.
    schedule = barber.schedule_for_day(date.weekday())
    if schedule is None:
        errors.append(f"{barber.name} does not work on {date:%A}s.")
    else:
        if start_time < schedule.start_time or end_dt.time() > schedule.end_time:
            errors.append(
                f"{barber.name} works {schedule.start_time:%I:%M %p}–"
                f"{schedule.end_time:%I:%M %p} on {date:%A}s."
            )

    # Overlap check against existing active appointments.
    existing = Appointment.objects.filter(
        barber=barber, date=date, status__in=Appointment.ACTIVE_STATUSES
    )
    if exclude_appointment is not None:
        existing = existing.exclude(pk=exclude_appointment.pk)
    for appt in existing:
        b0 = datetime.datetime.combine(date, appt.start_time)
        b1 = datetime.datetime.combine(date, appt.end_time)
        if _overlaps(start_dt, end_dt, b0, b1):
            errors.append(
                "That time slot has just been taken. Please pick another time."
            )
            break

    return errors
