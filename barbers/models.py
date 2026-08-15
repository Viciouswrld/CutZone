import datetime

from django.db import models


class Barber(models.Model):
    """A barber working at CutZone."""

    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="barbers/", blank=True, null=True)
    bio = models.TextField(blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def photo_url(self):
        """Return the uploaded photo URL or a placeholder image."""
        if self.photo and hasattr(self.photo, "url"):
            return self.photo.url
        return "/static/images/barber-placeholder.svg"

    def schedule_for_day(self, weekday: int):
        """Return the BarberSchedule for a weekday (0=Monday) or None."""
        return self.schedules.filter(weekday=weekday, is_working=True).first()


class BarberSchedule(models.Model):
    """Weekly working schedule for a barber (one row per weekday)."""

    WEEKDAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    barber = models.ForeignKey(
        Barber, on_delete=models.CASCADE, related_name="schedules"
    )
    weekday = models.IntegerField(choices=WEEKDAYS)
    is_working = models.BooleanField(default=True)
    start_time = models.TimeField(default=datetime.time(8, 0))
    end_time = models.TimeField(default=datetime.time(19, 0))

    class Meta:
        ordering = ["barber", "weekday"]
        unique_together = ("barber", "weekday")

    def __str__(self):
        if not self.is_working:
            return f"{self.barber.name}: {self.get_weekday_display()} — off"
        return (
            f"{self.barber.name}: {self.get_weekday_display()} "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )
