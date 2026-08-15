from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("book/", views.book_appointment, name="book"),
    path("slots/", views.available_slots, name="slots"),
    path("confirmation/<int:pk>/", views.confirmation, name="confirmation"),
    path("my/", views.my_appointments, name="my_appointments"),
    path("<int:pk>/", views.appointment_detail, name="detail"),
    path("<int:pk>/cancel/", views.cancel_appointment, name="cancel"),
    path("<int:pk>/reschedule/", views.reschedule_appointment, name="reschedule"),
]
