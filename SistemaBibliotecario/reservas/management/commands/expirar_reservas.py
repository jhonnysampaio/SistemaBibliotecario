from django.core.management.base import BaseCommand
from django.utils import timezone

from reservas.models import Reserva
from reservas.services import liberar_proximas_reservas


class Command(BaseCommand):
    help = "Expira reservas vencidas e avança a fila."

    def handle(self, *args, **options):
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

        self.stdout.write(
            self.style.SUCCESS(f"{total} reserva(s) expirada(s).")
        )
