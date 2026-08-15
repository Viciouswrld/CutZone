from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "customer", "barber", "service",
        "date", "start_time", "end_time", "status", "price",
    )
    list_filter = ("status", "barber", "service", "date")
    search_fields = ("reference", "customer__username", "customer__email")
    date_hierarchy = "date"
