from django.core.management.base import BaseCommand

from comunicacoes.rotinas import sincronizar_mensagens_temporais


class Command(BaseCommand):
    help = "Sincroniza mensagens pendentes sem duplicá-las."

    def handle(self, *args, **options):
        sincronizar_mensagens_temporais()
        self.stdout.write(self.style.SUCCESS("Mensagens sincronizadas."))
