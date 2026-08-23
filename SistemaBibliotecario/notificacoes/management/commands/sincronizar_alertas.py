from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from emprestimos.services import atualizar_atrasos
from notificacoes.services import gerar_alertas_para


class Command(BaseCommand):
    help = "Atualiza alertas internos de todos os usuários ativos."

    def handle(self, *args, **options):
        total = 0
        atrasados = atualizar_atrasos()

        for usuario in get_user_model().objects.filter(is_active=True):
            gerar_alertas_para(usuario)
            total += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{atrasados} empréstimo(s) marcado(s) como atrasado(s). "
                f"Alertas verificados para {total} usuário(s)."
            )
        )
