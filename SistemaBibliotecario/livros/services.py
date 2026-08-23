from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Livro


def _aplicar_disponibilidade(*, livro, original=None):
    emprestados = 0
    if original is not None:
        emprestados = (
            original.quantidade_total
            - original.quantidade_disponivel
        )

    if livro.quantidade_total < emprestados:
        raise ValidationError(
            {
                "quantidade_total": (
                    f"Há {emprestados} exemplar(es) emprestado(s). "
                    "O total não pode ficar abaixo desse número."
                )
            }
        )

    livro.quantidade_disponivel = livro.quantidade_total - emprestados
    return livro


def preparar_livro_com_estoque(*, livro):
    original = None
    if livro.pk:
        original = Livro.objects.only(
            "quantidade_total",
            "quantidade_disponivel",
        ).get(pk=livro.pk)

    return _aplicar_disponibilidade(livro=livro, original=original)


@transaction.atomic
def salvar_livro_com_estoque(*, livro):
    original = None
    if livro.pk:
        original = (
            Livro.objects.select_for_update()
            .only("quantidade_total", "quantidade_disponivel")
            .get(pk=livro.pk)
        )

    _aplicar_disponibilidade(livro=livro, original=original)
    livro.save()
    return livro
