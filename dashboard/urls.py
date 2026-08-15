from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    # Appointments
    path("appointments/", views.appointments, name="appointments"),
    path(
        "appointments/<int:pk>/status/<str:new_status>/",
        views.appointment_set_status,
        name="appointment_status",
    ),
    path("calendar/", views.calendar_view, name="calendar"),
    # Customers
    path("customers/", views.customers, name="customers"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path(
        "customers/<int:pk>/toggle/",
        views.customer_toggle_active,
        name="customer_toggle",
    ),
    # Barbers
    path("barbers/", views.barbers, name="barbers"),
    path("barbers/add/", views.barber_add, name="barber_add"),
    path("barbers/<int:pk>/edit/", views.barber_edit, name="barber_edit"),
    path("barbers/<int:pk>/toggle/", views.barber_toggle_active, name="barber_toggle"),
    path("barbers/<int:pk>/delete/", views.barber_delete, name="barber_delete"),
    # Schedules
    path("schedules/", views.schedules, name="schedules"),
    path("schedules/<int:barber_pk>/edit/", views.schedule_edit, name="schedule_edit"),
    # Services
    path("services/", views.services, name="services"),
    path("services/add/", views.service_add, name="service_add"),
    path("services/<int:pk>/edit/", views.service_edit, name="service_edit"),
    path(
        "services/<int:pk>/toggle/", views.service_toggle_active, name="service_toggle"
    ),
    path("services/<int:pk>/delete/", views.service_delete, name="service_delete"),
    # Reviews
    path("reviews/", views.reviews, name="reviews"),
    path(
        "reviews/<int:pk>/toggle/",
        views.review_toggle_approved,
        name="review_toggle",
    ),
    path("reviews/<int:pk>/delete/", views.review_delete, name="review_delete"),
    # Contact messages
    path("messages/", views.contact_messages, name="messages"),
    path("messages/<int:pk>/read/", views.message_mark_read, name="message_read"),
    path("messages/<int:pk>/delete/", views.message_delete, name="message_delete"),
]
