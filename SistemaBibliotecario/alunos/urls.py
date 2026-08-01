from django.urls import path
from . import views

urlpatterns = [
    path("cadastrar/", views.cadastrar_aluno, name="cadastrar_aluno"),
    path("listar/", views.listar_aluno, name="listar_aluno"),
    path("editar/<int:aluno_id>/", views.editar_aluno, name="editar_aluno"),
    path("excluir/<int:aluno_id>/", views.excluir_aluno, name="excluir_aluno")
]