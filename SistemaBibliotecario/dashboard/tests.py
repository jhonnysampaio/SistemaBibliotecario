from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Categoria, Livro


class DashboardHomologacaoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "dashboard-teste",
            password="senha-forte-123",
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="emprestimos",
                codename="view_emprestimo",
            )
        )
        self.client.force_login(self.user)

    def criar_dados(self):
        categoria = Categoria.objects.create(nome="Dashboard")
        livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Livro do dashboard",
            autor="Autora",
            editora="Editora",
            categoria=categoria,
            cdd="800",
            local_estante="A-01",
            etiqueta="DASH-001",
            quantidade_total=3,
            quantidade_disponivel=2,
        )
        Aluno.objects.create(
            matricula="DASH-001",
            nome="Aluno ativo",
            serie="8º",
            turma="A",
            turno="M",
            cpf="52998224725",
        )
        aluno_inativo = Aluno.objects.create(
            matricula="DASH-002",
            nome="Aluno inativo",
            serie="8º",
            turma="B",
            turno="V",
            cpf="11144477735",
            ativo=False,
        )
        emprestimo = Emprestimo.objects.create(
            aluno=aluno_inativo,
            livro=livro,
            data_prevista=timezone.localdate() + timedelta(days=1),
            registrado_por=self.user,
        )
        return emprestimo

    def test_metricas_correspondem_ao_banco(self):
        self.criar_dados()

        response = self.client.get(reverse("dashboard:inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["metricas"],
            {
                "titulos": 1,
                "exemplares": 3,
                "disponiveis": 2,
                "alunos": 1,
                "abertos": 1,
                "atrasados": 0,
            },
        )

    def test_grafico_inclui_dias_sem_movimento(self):
        self.criar_dados()

        response = self.client.get(reverse("dashboard:inicio"))
        valores = response.context["grafico_valores"]

        self.assertEqual(len(valores), 7)
        self.assertEqual(sum(valores), 1)
        self.assertEqual(valores.count(0), 6)

    def test_estados_vazios_sao_compreensiveis(self):
        response = self.client.get(reverse("dashboard:inicio"))

        self.assertContains(response, "Nenhum prazo nos próximos dois dias.")
        self.assertContains(response, "Nenhuma atividade.")
