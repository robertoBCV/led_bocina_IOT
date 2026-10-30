from django.urls import path

from . import views

app_name = "control"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "api/estado/",
        views.estado_sistema,
        name="estado_sistema"
    ),

    path(
        "api/led/<str:codigo>/",
        views.controlar_led,
        name="controlar_led"
    ),

    path(
        "api/bocina/<str:codigo>/",
        views.controlar_bocina,
        name="controlar_bocina"
    ),
]
