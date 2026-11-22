from django.urls import path
from . import views

app_name = "importacao"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("<slug:tipo>/enviar/",views.enviar, name="enviar"),
    path("<slug:tipo>/modelo/", views.modelo, name="modelo"),
    path("<int:pk>/previa/", views.previa, name="previa"),
    path("<int:pk>/confirmar/", views.confirmar, name="confirmar"),
]