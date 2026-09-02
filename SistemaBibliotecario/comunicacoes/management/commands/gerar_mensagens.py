from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from comunicacoes.services import (
    enfileirar_atraso,
    enfileirar_prazo_emprestimo,
    enfileirar_reserva_disponivel,
)
from emprestimos.models import Emprestimo
from emprestimos.services import atualizar_atrasos
from reservas.models import Reserva


class Command(BaseCommand):
    help = "Sincroniza mensagens pendentes sem duplicá-las."

    def handle(self, *args, **options):
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

        for emprestimo in proximos_do_prazo:
            enfileirar_prazo_emprestimo(emprestimo=emprestimo)
        for emprestimo in atrasados:
            enfileirar_atraso(emprestimo=emprestimo)
        for reserva in reservas:
            enfileirar_reserva_disponivel(reserva=reserva)

        self.stdout.write(self.style.SUCCESS("Mensagens sincronizadas."))
