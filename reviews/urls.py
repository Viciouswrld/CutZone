from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("leave/<int:appointment_pk>/", views.leave_review, name="leave"),
]
