from django.urls import path
from . import views

app_name = "alunos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("novo/", views.criar, name="criar"),
    path(
        "fechamento-ano-letivo/",
        views.fechamento_ano_letivo,
        name="fechamento_ano_letivo",
    ),
    path(
        "fechamento-ano-letivo/solicitar-devolucao/<int:pk>/",
        views.solicitar_devolucao,
        name="solicitar_devolucao",
    ),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
]
