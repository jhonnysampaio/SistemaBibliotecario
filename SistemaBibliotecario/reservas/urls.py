from django.urls import path

from . import views


app_name = "reservas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nova/", views.nova, name="nova"),
    path("<int:pk>/cancelar/", views.cancelar, name="cancelar"),
]
