from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

from usuarios.models import Perfil


class Command(BaseCommand):
    help = "Cria grupos padrão e atribui permissões."

    def handle(self, *args, **options):
        apps = ("alunos", "livros", "emprestimos", "reservas")

        bibliotecarios, _ = Group.objects.get_or_create(name="Bibliotecários")
        bibliotecarios.permissions.set(
            Permission.objects.filter(
                Q(content_type__app_label__in=apps)
                | Q(codename__in=("view_user", "add_user", "change_user"))
                | Q(
                    content_type__app_label="comunicacoes",
                    codename="view_mensagem",
                )
            ).exclude(
                Q(
                    content_type__app_label="emprestimos",
                    codename="delete_emprestimo",
                )
                | Q(
                    content_type__app_label="reservas",
                    codename="delete_reserva",
                )
            )
        )

        auxiliares, _ = Group.objects.get_or_create(name="Auxiliares")
        auxiliares.permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=apps,
            ).exclude(
                codename__startswith="delete_"
            )
        )

        direcao, _ = Group.objects.get_or_create(name="Direção")
        direcao.permissions.set(
            Permission.objects.filter(
                Q(
                    content_type__app_label__in=apps,
                    codename__startswith="view_",
                )
                | Q(codename="view_user")
                | Q(
                    content_type__app_label="comunicacoes",
                    codename="view_mensagem",
                )
            )
        )

        grupo_por_cargo = {
            Perfil.Cargo.BIBLIOTECARIO: bibliotecarios,
            Perfil.Cargo.AUXILIAR: auxiliares,
            Perfil.Cargo.DIRECAO: direcao,
        }
        for perfil in Perfil.objects.select_related("usuario"):
            perfil.usuario.groups.add(grupo_por_cargo[perfil.cargo])

        self.stdout.write(
            self.style.SUCCESS(
                "Grupos Bibliotecários, Auxiliares e Direção configurados."
            )
        )
