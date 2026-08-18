from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from livros.models import Livro

from .models import Emprestimo


class RegraEmprestimoError(Exception):
    pass


@transaction.atomic
def registrar_emprestimo(
    *,
    aluno,
    livro,
    data_prevista,
    usuario,
    observacoes="",
):
    if not aluno.ativo:
        raise RegraEmprestimoError("O aluno está inativo.")
    if data_prevista < timezone.localdate():
        raise RegraEmprestimoError("A data prevista não pode estar no passado.")
    if Emprestimo.objects.filter(
        aluno=aluno,
        livro=livro,
        situacao__in=[
            Emprestimo.Situacao.ATIVO,
            Emprestimo.Situacao.ATRASADO,
        ],
    ).exists():
        raise RegraEmprestimoError(
            "Este aluno já possui um empréstimo aberto deste livro."
        )

    livro = Livro.objects.select_for_update().get(pk=livro.pk)
    atualizado = Livro.objects.filter(
        pk=livro.pk,
        ativo=True,
        quantidade_disponivel__gt=0,
    ).update(
        quantidade_disponivel=F("quantidade_disponivel") - 1
    )
    if atualizado == 0:
        raise RegraEmprestimoError("Não há exemplar disponível.")

    emprestimo = Emprestimo(
        aluno=aluno,
        livro=livro,
        data_prevista=data_prevista,
        observacoes=observacoes,
        registrado_por=usuario,
    )
    try:
        emprestimo.full_clean()
        emprestimo.save()
    except ValidationError as error:
        raise RegraEmprestimoError(
            "Os dados do empréstimo são inválidos."
        ) from error

    return emprestimo


@transaction.atomic
def devolver_emprestimo(*, emprestimo, data_devolucao=None):
    emprestimo = (
        Emprestimo.objects.select_for_update()
        .select_related("livro")
        .get(pk=emprestimo.pk)
    )
    if emprestimo.situacao == Emprestimo.Situacao.DEVOLVIDO:
        raise RegraEmprestimoError("Este empréstimo já foi devolvido.")

    data_devolucao = data_devolucao or timezone.localdate()
    if data_devolucao < emprestimo.data_inicio:
        raise RegraEmprestimoError(
            "A devolução não pode ser anterior ao empréstimo."
        )

    Livro.objects.select_for_update().get(pk=emprestimo.livro_id)
    atualizado = Livro.objects.filter(
        pk=emprestimo.livro_id,
        quantidade_disponivel__lt=F("quantidade_total"),
    ).update(
        quantidade_disponivel=F("quantidade_disponivel") + 1
    )
    if atualizado == 0:
        raise RegraEmprestimoError(
            "O estoque está inconsistente; a devolução foi cancelada."
        )

    emprestimo.situacao = Emprestimo.Situacao.DEVOLVIDO
    emprestimo.data_devolucao = data_devolucao
    emprestimo.save(
        update_fields=["situacao", "data_devolucao", "atualizado_em"]
    )
    return emprestimo


@transaction.atomic
def renovar_emprestimo(*, emprestimo, dias=7):
    emprestimo = Emprestimo.objects.select_for_update().get(pk=emprestimo.pk)
    if emprestimo.situacao == Emprestimo.Situacao.DEVOLVIDO:
        raise RegraEmprestimoError("Empréstimo já devolvido.")
    if emprestimo.data_prevista < timezone.localdate():
        raise RegraEmprestimoError("Empréstimo atrasado não pode ser renovado.")
    if emprestimo.renovacoes >= 2:
        raise RegraEmprestimoError("Limite de renovações atingido.")

    emprestimo.data_prevista += timedelta(days=dias)
    emprestimo.renovacoes = F("renovacoes") + 1
    emprestimo.save(
        update_fields=["data_prevista", "renovacoes", "atualizado_em"]
    )
    emprestimo.refresh_from_db()
    return emprestimo


def atualizar_atrasos():
    hoje = timezone.localdate()
    return Emprestimo.objects.filter(
        situacao=Emprestimo.Situacao.ATIVO,
        data_prevista__lt=hoje,
    ).update(situacao=Emprestimo.Situacao.ATRASADO)
