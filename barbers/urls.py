from django.urls import path

from . import views

app_name = "barbers"

urlpatterns = [
    path("", views.barber_list, name="list"),
]
