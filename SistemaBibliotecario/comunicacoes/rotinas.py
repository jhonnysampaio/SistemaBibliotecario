from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from emprestimos.models import Emprestimo
from emprestimos.services import atualizar_atrasos
from notificacoes.services import gerar_alertas_para
from reservas.models import Reserva
from reservas.services import liberar_proximas_reservas

from .envio import enviar_mensagem_por_id
from .models import Mensagem
from .services import (
    enfileirar_atraso,
    enfileirar_prazo_emprestimo,
    enfileirar_reserva_disponivel,
)


def expirar_reservas_vencidas():
    agora = timezone.now()
    livros = list(
        Reserva.objects.filter(
            status=Reserva.Status.DISPONIVEL,
            disponivel_ate__lt=agora,
        )
        .values_list("livro_id", flat=True)
        .distinct()
    )

    total = 0
    for livro_id in livros:
        antes = Reserva.objects.filter(
            livro_id=livro_id,
            status=Reserva.Status.EXPIRADA,
        ).count()
        liberar_proximas_reservas(livro_id=livro_id)
        depois = Reserva.objects.filter(
            livro_id=livro_id,
            status=Reserva.Status.EXPIRADA,
        ).count()
        total += depois - antes
    return total


def sincronizar_mensagens_temporais():
    atualizar_atrasos()
    hoje = timezone.localdate()
    limite_prazo = hoje + timedelta(
        days=settings.AVISO_PRAZO_EMPRESTIMO_DIAS
    )
    proximos_do_prazo = Emprestimo.objects.filter(
        situacao=Emprestimo.Situacao.ATIVO,
        data_prevista__range=(hoje, limite_prazo),
    ).select_related("aluno", "livro")
    atrasados = Emprestimo.objects.filter(
        situacao=Emprestimo.Situacao.ATRASADO
    ).select_related("aluno", "livro")
    reservas = Reserva.objects.filter(
        status=Reserva.Status.DISPONIVEL
    ).select_related("aluno", "livro")

    totais = {"prazos": 0, "atrasos": 0, "reservas": 0}
    for emprestimo in proximos_do_prazo:
        if enfileirar_prazo_emprestimo(emprestimo=emprestimo):
            totais["prazos"] += 1
    for emprestimo in atrasados:
        if enfileirar_atraso(emprestimo=emprestimo):
            totais["atrasos"] += 1
    for reserva in reservas:
        if enfileirar_reserva_disponivel(reserva=reserva):
            totais["reservas"] += 1
    return totais


def sincronizar_alertas_internos():
    total = 0
    for usuario in get_user_model().objects.filter(is_active=True):
        gerar_alertas_para(usuario)
        total += 1
    return total


def reenviar_mensagens_pendentes(*, limite=50):
    ids = list(
        Mensagem.objects.filter(
            status__in=(
                Mensagem.Status.PENDENTE,
                Mensagem.Status.FALHA,
            ),
            tentativas__lt=3,
        )
        .order_by("criada_em", "pk")
        .values_list("pk", flat=True)[:limite]
    )
    enviadas = 0
    for mensagem_id in ids:
        if enviar_mensagem_por_id(mensagem_id):
            enviadas += 1
    return enviadas


def executar_rotinas_do_servidor():
    expiradas = expirar_reservas_vencidas()
    mensagens = sincronizar_mensagens_temporais()
    alertas = sincronizar_alertas_internos()
    reenviadas = reenviar_mensagens_pendentes()
    return {
        "reservas_expiradas": expiradas,
        "alertas": alertas,
        "mensagens_reenviadas": reenviadas,
        **mensagens,
    }


def proxima_execucao_temporal():
    agora = timezone.now()
    agora_local = timezone.localtime(agora)
    amanha = agora_local.date() + timedelta(days=1)
    meia_noite_local = timezone.make_aware(
        datetime.combine(amanha, time.min),
        timezone.get_current_timezone(),
    )

    proxima_reserva = (
        Reserva.objects.filter(
            status=Reserva.Status.DISPONIVEL,
            disponivel_ate__gt=agora,
        )
        .order_by("disponivel_ate")
        .values_list("disponivel_ate", flat=True)
        .first()
    )
    if proxima_reserva is not None:
        proxima_reserva += timedelta(seconds=1)
        return min(meia_noite_local, proxima_reserva)
    return meia_noite_local
