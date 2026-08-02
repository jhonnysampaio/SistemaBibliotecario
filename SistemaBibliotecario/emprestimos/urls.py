from django.urls import path
from . import views

urlpatterns = [
    path("novo/", views.novo_emprestimo, name="novo_emprestimo"),
    path("listar/", views.listar_emprestimo, name="listar_emprestimo"),
    path("finalizar/<int:emprestimo_id>", views.finalizar_emprestimo, name="finalizar_emprestimo"),
    path("editar/<int:emprestimo_id>", views.editar_emprestimo, name="editar_emprestimo"),
]