from django.urls import path
from . import views

app_name = "emprestimos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.novo, name="novo"),
    path("historico/", views.historico, name="historico"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/devolver/", views.devolver, name="devolver"),
    path("<int:pk>/renovar/", views.renovar, name="renovar"),
]