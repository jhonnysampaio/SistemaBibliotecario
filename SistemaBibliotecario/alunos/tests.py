from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from .forms import AlunoForm
from .models import Aluno


class AlunoFormTests(TestCase):
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
