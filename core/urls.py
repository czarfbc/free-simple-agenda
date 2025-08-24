from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # público
    path("", views.booking_page, name="booking_page"),
    path("available-times/", views.available_times, name="available_times"),
    path("book/form/", views.book_form, name="book_form"),
    path("book/", views.create_appointment, name="book"),

    # manager (auth)
    path("manager/login/", views.manager_login, name="manager_login"),
    path("manager/logout/", views.manager_logout, name="manager_logout"),
    path("manager/", views.manager_dashboard, name="manager_dashboard"),

    # manager: cadastros
    path("manager/time-options/", views.manager_time_options,
         name="manager_time_options"),
    path("manager/services/", views.manager_services, name="manager_services"),

    # manager: appointment
    path("manager/appointments/", views.manager_appointments,
         name="manager_appointments"),
]
