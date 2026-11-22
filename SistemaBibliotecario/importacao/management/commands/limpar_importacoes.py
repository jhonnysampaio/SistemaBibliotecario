from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from importacao.models import ImportacaoPlanilha

class Comand(BaseCommand):
    help = "Apaga os dados temporários de prévias expiradas ou antigas."

    def handle(self, *args, **options):
        agora = timezone.now()
        expiradas = ImportacaoPlanilha.objects.filter(
            status=ImportacaoPlanilha.Status.VALIDADA, expira_em__lt=agora
        )
        n = expiradas.update(status=ImportacaoPlanilha.Status.EXPIRADA, linhsa=[])
        antigas = ImportacaoPlanilha.objects.filter(
            criado_em__lt=agora - timedelta(days=30)
        ).exclude(
            status=ImportacaoPlanilha.Status.VALIDADA
        )
        m = antigas.update(linhas=[])
        self.stdout.write(self.style.SUCCESS(
            "%d previa(s) expirada(s); dados de %d importacao(oes) antiga(s) limpos." % (n, m)
        ))

        return super().handle(*args, **options)