import datetime

from django import forms

from barbers.models import Barber
from services.models import Service

from .availability import validate_booking


class BookingForm(forms.Form):
    """
    Final booking submission form.

    The customer walks through service → barber → date → time on the
    booking page; this form performs the authoritative backend validation.
    """

    service = forms.ModelChoiceField(queryset=Service.objects.filter(is_active=True))
    barber = forms.ModelChoiceField(queryset=Barber.objects.filter(is_active=True))
    date = forms.DateField(input_formats=["%Y-%m-%d"])
    start_time = forms.TimeField(input_formats=["%H:%M"])
    notes = forms.CharField(required=False, max_length=300, widget=forms.Textarea)

    def __init__(self, *args, exclude_appointment=None, **kwargs):
        self.exclude_appointment = exclude_appointment
        super().__init__(*args, **kwargs)

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < datetime.date.today():
            raise forms.ValidationError("You cannot book a date in the past.")
        if date > datetime.date.today() + datetime.timedelta(days=60):
            raise forms.ValidationError("Bookings are only open 60 days ahead.")
        return date

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get("service")
        barber = cleaned.get("barber")
        date = cleaned.get("date")
        start_time = cleaned.get("start_time")

        if service and barber and date and start_time:
            errors = validate_booking(
                barber, service, date, start_time,
                exclude_appointment=self.exclude_appointment,
            )
            for err in errors:
                self.add_error(None, err)
        return cleaned
