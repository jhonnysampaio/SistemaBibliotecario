from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="usuarios/login.html",
            redirect_authenticated_user=True
        ),
        name="login"
    ),
    path(
        "sair/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("perfil/", views.perfil, name="perfil"),
    path("alterar-senha/", views.alterar_senha, name="alterar_senha"),
    path("usuarios/", views.lista, name="lista"),
    path("usuarios/novo/", views.criar, name="criar"),
    path("usuarios/<int:pk>/alternar-ativo/", views.alternar_ativo, name="alternar_ativo")
]