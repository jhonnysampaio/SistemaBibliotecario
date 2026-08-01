from django.urls import path
from . import views

urlpatterns = [
    path("cadastrar/", views.cadastrar_livro, name="cadastrar_livro" ),
    path("listar/", views.listar_livro, name="listar_livro"),
    path("editar/<int:livro_id>/", views.editar_livro, name="editar_livro"),
    path("excluir/<int:livro_id>/", views.excluir_livro, name="excluir_livro")
]