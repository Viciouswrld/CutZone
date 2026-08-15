from django.contrib import admin

from .models import Barber, BarberSchedule


class BarberScheduleInline(admin.TabularInline):
    model = BarberSchedule
    extra = 0


@admin.register(Barber)
class BarberAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "specialization")
    inlines = [BarberScheduleInline]


@admin.register(BarberSchedule)
class BarberScheduleAdmin(admin.ModelAdmin):
    list_display = ("barber", "weekday", "is_working", "start_time", "end_time")
    list_filter = ("barber", "is_working")
