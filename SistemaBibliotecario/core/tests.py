from io import StringIO

from datetime import timedelta

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Categoria, Livro


class ConfigurarPermissoesTests(TestCase):
    def test_bibliotecarios_nao_recebem_permissao_de_apagar_emprestimos(self):
        call_command("configurar_permissoes", stdout=StringIO())

        grupo = Group.objects.get(name="Bibliotecários")
        self.assertFalse(
            grupo.permissions.filter(
                content_type__app_label="emprestimos",
                codename="delete_emprestimo",
            ).exists()
        )
        self.assertTrue(
            grupo.permissions.filter(
                content_type__app_label="livros",
                codename="delete_livro",
            ).exists()
        )


class PesquisaGlobalTests(TestCase):
    def test_pesquisa_encontra_aluno_livro_e_emprestimo(self):
        user = User.objects.create_user(
            "pesquisa-teste",
            password="senha-forte-123",
        )
        user.user_permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=(
                    "alunos",
                    "livros",
                    "emprestimos",
                ),
                codename__in=(
                    "view_aluno",
                    "view_livro",
                    "view_emprestimo",
                ),
            )
        )
        aluno = Aluno.objects.create(
            matricula="AUR-001",
            nome="Ana Aurora",
            serie="8º",
            turma="A",
            turno="M",
            cpf="52998224725",
        )
        categoria = Categoria.objects.create(nome="Pesquisa")
        livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Atlas Aurora",
            autor="Autora",
            editora="Editora",
            categoria=categoria,
            cdd="800",
            local_estante="A-01",
            etiqueta="AUR-001",
        )
        emprestimo = Emprestimo.objects.create(
            aluno=aluno,
            livro=livro,
            data_prevista=timezone.localdate() + timedelta(days=7),
            registrado_por=user,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("core:pesquisa"),
            {"q": "Aurora"},
        )

        self.assertContains(response, aluno.nome)
        self.assertContains(response, livro.titulo)
        self.assertIn(emprestimo, response.context["emprestimos"])
