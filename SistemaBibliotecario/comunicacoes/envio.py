from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Mensagem


def reivindicar_mensagem(*, mensagem_id=None):
    with transaction.atomic():
        limite_trava = timezone.now() - timedelta(minutes=30)
        Mensagem.objects.filter(
            status=Mensagem.Status.PROCESSANDO,
            ultima_tentativa_em__lt=limite_trava,
        ).update(
            status=Mensagem.Status.FALHA,
            erro="Processamento interrompido.",
        )

        candidatas = Mensagem.objects.filter(
            status__in=(
                Mensagem.Status.PENDENTE,
                Mensagem.Status.FALHA,
            ),
            tentativas__lt=3,
        )
        if mensagem_id is not None:
            candidatas = candidatas.filter(pk=mensagem_id)

        candidata = candidatas.order_by("criada_em", "pk").first()
        if candidata is None:
            return None

        agora = timezone.now()
        atualizadas = Mensagem.objects.filter(
            pk=candidata.pk,
            status__in=(
                Mensagem.Status.PENDENTE,
                Mensagem.Status.FALHA,
            ),
        ).update(
            status=Mensagem.Status.PROCESSANDO,
            tentativas=candidata.tentativas + 1,
            ultima_tentativa_em=agora,
            erro="",
        )
        if atualizadas != 1:
            return None

        candidata.refresh_from_db()
        return candidata


def enviar_mensagem(mensagem):
    try:
        corpo_html = mensagem.corpo_html or render_to_string(
            "comunicacoes/email/mensagem.html",
            {
                "pre_cabecalho": mensagem.assunto,
                "categoria": mensagem.get_tipo_display(),
                "titulo": mensagem.assunto,
                "texto": mensagem.corpo,
            },
        )
        enviados = send_mail(
            mensagem.assunto,
            mensagem.corpo,
            None,
            [mensagem.destinatario],
            fail_silently=False,
            html_message=corpo_html,
        )
        if enviados != 1:
            raise RuntimeError("O backend não confirmou o envio.")
    except Exception as error:
        mensagem.status = Mensagem.Status.FALHA
        mensagem.erro = str(error)[:2000]
        enviada = False
    else:
        mensagem.status = Mensagem.Status.ENVIADA
        mensagem.enviada_em = timezone.now()
        mensagem.erro = ""
        enviada = True
        if mensagem.reserva_id:
            mensagem.reserva.notificada_em = mensagem.enviada_em
            mensagem.reserva.save(
                update_fields=["notificada_em", "atualizada_em"]
            )

    mensagem.save(
        update_fields=[
            "status",
            "enviada_em",
            "erro",
            "atualizada_em",
        ]
    )
    return enviada


def enviar_mensagem_por_id(mensagem_id):
    mensagem = reivindicar_mensagem(mensagem_id=mensagem_id)
    if mensagem is None:
        return False
    return enviar_mensagem(mensagem)
