"""Forms used by the custom admin dashboard (staff only)."""

from django import forms
from django.forms import modelformset_factory

from barbers.models import Barber, BarberSchedule
from bookings.models import Appointment
from services.models import Service


def _style(fields):
    for name, field in fields.items():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs["class"] = "form-check-input"
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs["class"] = "form-select"
        else:
            css = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css} form-control".strip()


class BarberForm(forms.ModelForm):
    class Meta:
        model = Barber
        fields = ["name", "photo", "specialization", "bio", "is_active"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "description", "price", "duration_minutes", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)


class BarberScheduleForm(forms.ModelForm):
    class Meta:
        model = BarberSchedule
        fields = ["weekday", "is_working", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self.fields)
        self.fields["weekday"].disabled = True

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_time"), cleaned.get("end_time")
        if cleaned.get("is_working") and start and end and start >= end:
            raise forms.ValidationError("Start time must be before end time.")
        return cleaned


# Formset used to edit all 7 weekday rows of one barber at once.
ScheduleFormSet = modelformset_factory(
    BarberSchedule, form=BarberScheduleForm, extra=0
)


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["status"]
        widgets = {"status": forms.Select(attrs={"class": "form-select form-select-sm"})}
