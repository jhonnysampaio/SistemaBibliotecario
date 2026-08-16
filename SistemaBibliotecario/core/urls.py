from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("pesquisa/", views.pesquisa, name="pesquisa"),
]
