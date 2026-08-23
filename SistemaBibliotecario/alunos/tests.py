from io import StringIO

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from emprestimos.forms import EmprestimoForm
from emprestimos.models import Emprestimo
from livros.models import Categoria, Livro

from .forms import AlunoForm
from .models import Aluno


class AlunoFormTests(TestCase):
    def test_aceita_cpf_formatado_e_salva_somente_digitos(self):
        form = AlunoForm(
            data={
                "matricula": "2026002",
                "nome": "Marina Alves",
                "serie": "8º",
                "turma": "A",
                "turno": "M",
                "cpf": "529.982.247-25",
                "telefone": "",
                "email": "",
                "ativo": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        aluno = form.save()

        self.assertEqual(aluno.cpf, "52998224725")

    def test_rejeita_cpf_invalido(self):
        form = AlunoForm(
            data={
                "matricula": "2026001",
                "nome": "Ana Souza",
                "serie": "8º",
                "turma": "A",
                "turno": "M",
                "cpf": "111.111.111-11",
                "telefone": "",
                "email": "",
                "ativo": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("cpf", form.errors)

    def test_rejeita_matricula_duplicada(self):
        Aluno.objects.create(
            matricula="2026003",
            nome="Aluno existente",
            serie="8º",
            turma="A",
            turno="M",
            cpf="52998224725",
        )
        form = AlunoForm(
            data={
                "matricula": "2026003",
                "nome": "Outro aluno",
                "serie": "9º",
                "turma": "B",
                "turno": "V",
                "cpf": "11144477735",
                "telefone": "",
                "email": "",
                "ativo": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("matricula", form.errors)


class AlunoViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "biblioteca",
            password="senha-forte-123",
        )
        self.aluno = Aluno.objects.create(
            matricula="2026001",
            nome="Ana Souza",
            serie="8º",
            turma="A",
            turno="M",
            cpf="52998224725",
        )

    def test_lista_exige_login(self):
        response = self.client.get(reverse("alunos:lista"))

        self.assertEqual(response.status_code, 302)

    def test_usuario_com_permissao_visualiza_lista(self):
        permission = Permission.objects.get(codename="view_aluno")
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        response = self.client.get(reverse("alunos:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Souza")

    def test_exclusao_nao_aceita_get(self):
        permission = Permission.objects.get(codename="delete_aluno")
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("alunos:excluir", args=[self.aluno.pk])
        )

        self.assertEqual(response.status_code, 405)

    def test_paginacao_preserva_termo_e_filtro(self):
        permission = Permission.objects.get(codename="view_aluno")
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)
        for indice in range(25):
            Aluno.objects.create(
                matricula=f"BUSCA-{indice:02d}",
                nome=f"Aluno Busca {indice:02d}",
                serie="8º",
                turma="A",
                turno="M",
                cpf=f"{indice + 1000:011d}",
            )

        response = self.client.get(
            reverse("alunos:lista"),
            {"q": "Busca", "situacao": "ativos"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "q=Busca&amp;situacao=ativos&amp;page=2",
        )

    def test_aluno_com_historico_nao_e_excluido(self):
        self.user.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="alunos",
                codename__in=("view_aluno", "delete_aluno"),
            )
        )
        self.client.force_login(self.user)
        categoria = Categoria.objects.create(nome="Histórico")
        livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Livro histórico",
            autor="Autora",
            editora="Editora",
            categoria=categoria,
            cdd="800",
            local_estante="A-01",
            etiqueta="HIST-001",
        )
        Emprestimo.objects.create(
            aluno=self.aluno,
            livro=livro,
            data_prevista=timezone.localdate(),
            registrado_por=self.user,
        )

        response = self.client.post(
            reverse("alunos:excluir", args=[self.aluno.pk])
        )

        self.assertRedirects(response, reverse("alunos:lista"))
        self.assertTrue(Aluno.objects.filter(pk=self.aluno.pk).exists())

    def test_auxiliar_sem_permissao_recebe_403_ao_excluir(self):
        call_command("configurar_permissoes", stdout=StringIO())
        self.user.groups.add(Group.objects.get(name="Auxiliares"))
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("alunos:excluir", args=[self.aluno.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Aluno.objects.filter(pk=self.aluno.pk).exists())

    def test_aluno_inativo_nao_aparece_em_novo_emprestimo(self):
        self.aluno.ativo = False
        self.aluno.save(update_fields=["ativo"])

        form = EmprestimoForm()

        self.assertNotIn(self.aluno, form.fields["aluno"].queryset)
