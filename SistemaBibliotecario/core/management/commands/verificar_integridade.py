from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q, F, Count
from emprestimos.models import Emprestimo
from livros.models import Livro

class Command(BaseCommand):
    help = "Verifica chaves e reconcilia quantidade disponível esperada."

    def handle(self, *args, **options):
        problemas = 0

        if connection.vendor == "sqlite":
            with connection.cursor() as cursor:
                resultado = cursor.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
                chaves = cursor.execute(
                    "PRAGMA foreign_key_check"
                ).fetchall()
            self.stdout.write(f"SQLite integrity_check: {resultado}")
            self.stdout.write(f"Falhas de chave estrangeira: {chaves}")
            problemas += 0 if resultado == "ok" and not chaves else 1

        livros = Livro.objects.annotate(
            abertos=Count(
                "emprestimos",
                filter=Q(
                    emprestimos__situacao__in=(
                        Emprestimo.Situacao.ATIVO,
                        Emprestimo.Situacao.ATRASADO,
                    )
                ),
            )
        )
        for livro in livros:
            esperado = livro.quantidade_total - livro.abertos
            if livro.quantidade_disponivel != esperado:
                problemas += 1
                self.stderr.write(
                    f"Livro {livro.pk}: disponível="
                    f"{livro.quantidade_disponivel}, esperado={esperado}"
                )

        if problemas:
            self.stderr.write(
                self.style.ERROR(f"{problemas} problema(s) encontrado(s).")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Integridade confirmada."))