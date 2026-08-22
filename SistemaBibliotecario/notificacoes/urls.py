from django.urls import path
from . import views

app_name = "notificacoes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/lida/", views.marcar_lida, name="marcar_lida"),
    path("todas-lidas/", views.marcar_todas_lidas, name="marcar_todas_lidas"),
]