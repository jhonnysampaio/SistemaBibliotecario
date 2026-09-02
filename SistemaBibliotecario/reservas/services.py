from datetime import timedelta
from django.db import IntegrityError, transaction
from django.utils import timezone
from emprestimos.models import Emprestimo
from livros.models import Livro

from .models import Reserva


class RegraReservaError(Exception):
    pass


@transaction.atomic
def criar_reserva(*, aluno, livro):
    livro = Livro.objects.select_for_update().get(pk=livro.pk)
    if not aluno.ativo:
        raise RegraReservaError("Aluno inativo não pode reservar.")
    if not livro.ativo:
        raise RegraReservaError("Não é possível reservar um livro inativo.")
    if Emprestimo.objects.filter(
        aluno=aluno,
        livro=livro,
        situacao__in=(
            Emprestimo.Situacao.ATIVO,
            Emprestimo.Situacao.ATRASADO,
        ),
    ).exists():
        raise RegraReservaError("O aluno já possui este livro emprestado.")

    destinadas = Reserva.objects.filter(
        livro=livro, status=Reserva.Status.DISPONIVEL
    ).count()
    if livro.quantidade_disponivel - destinadas > 0:
        raise RegraReservaError(
            "Há exemplar livre; registre um empréstimo em vez de reservar."
        )
    try:
        with transaction.atomic():
            return Reserva.objects.create(aluno=aluno, livro=livro)
    except IntegrityError as error:
        raise RegraReservaError(
            "O aluno já possui uma reserva ativa deste livro."
        ) from error


@transaction.atomic
def liberar_proximas_reservas(*, livro_id, prazo_horas=48):
    agora = timezone.now()
    livro = Livro.objects.select_for_update().get(pk=livro_id)

    Reserva.objects.select_for_update().filter(
        livro=livro,
        status=Reserva.Status.DISPONIVEL,
        disponivel_ate__lt=agora,
    ).update(status=Reserva.Status.EXPIRADA)

    destinadas = Reserva.objects.filter(
        livro=livro, status=Reserva.Status.DISPONIVEL
    ).count()
    vagas = max(0, livro.quantidade_disponivel - destinadas)
    liberadas = []

    while vagas:
        proxima = (
            Reserva.objects.select_for_update()
            .filter(livro=livro, status=Reserva.Status.AGUARDANDO)
            .order_by("criada_em", "pk")
            .first()
        )
        if proxima is None:
            break
        proxima.status = Reserva.Status.DISPONIVEL
        proxima.disponibilizada_em = agora
        proxima.disponivel_ate = agora + timedelta(hours=prazo_horas)
        proxima.save(
            update_fields=[
                "status",
                "disponibilizada_em",
                "disponivel_ate",
                "atualizada_em",
            ]
        )
        liberadas.append(proxima)
        vagas -= 1
    return liberadas


@transaction.atomic
def cancelar_reserva(*, reserva):
    reserva = (
        Reserva.objects.select_for_update()
        .select_related("livro")
        .get(pk=reserva.pk)
    )
    if reserva.status not in(
        Reserva.Status.AGUARDANDO, Reserva.Status.DISPONIVEL
    ):
        raise RegraReservaError("Esta reserva não pode mais ser cancelada.")
    livro_id = reserva.livro_id
    reserva.status = Reserva.Status.CANCELADA
    reserva.save(update_fields=["status", "atualizada_em"])
    liberar_proximas_reservas(livro_id=livro_id)
    return reserva


def posicao_fila(reserva):
    if reserva.status != Reserva.Status.AGUARDANDO:
        return None
    anteriores = Reserva.objects.filter(
        livro=reserva.livro,
        status=Reserva.Status.AGUARDANDO,
        criada_em__lt=reserva.criada_em,
    ).count()
    empatadas = Reserva.objects.filter(
        livro=reserva.livro,
        status=Reserva.Status.AGUARDANDO,
        criada_em=reserva.criada_em,
        pk__lt=reserva.pk,
    ).count()
    return anteriores + empatadas + 1
