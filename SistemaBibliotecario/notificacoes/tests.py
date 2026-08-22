from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Categoria, Livro

from .models import Notificacao
from .services import gerar_alertas_para


class NotificacaoInterfaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "biblioteca-notificacoes",
            password="senha-forte-123",
        )
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="emprestimos",
                codename="view_emprestimo",
            )
        )
        self.aluno = Aluno.objects.create(
            matricula="2026096",
            nome="Marina Alves",
            serie="8º",
            turma="A",
            turno="M",
            cpf="52998224725",
        )
        categoria = Categoria.objects.create(nome="Literatura")
        self.livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Livro de teste",
            autor="Autora",
            editora="Editora",
            categoria=categoria,
            cdd="800",
            local_estante="A-01",
            etiqueta="NOT-001",
            quantidade_total=1,
            quantidade_disponivel=0,
        )
        self.emprestimo = Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=1),
            registrado_por=self.user,
        )
        self.client.force_login(self.user)

    def test_sino_exibe_total_de_notificacoes_nao_lidas(self):
        Notificacao.objects.create(
            usuario=self.user,
            emprestimo=self.emprestimo,
            tipo=Notificacao.Tipo.PRAZO,
            titulo="Devolução próxima",
            mensagem="Prazo de devolução próximo.",
        )

        response = self.client.get(reverse("dashboard:inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("notificacoes:lista"))
        self.assertContains(response, "Notificações: 1 não lida")

    def test_lista_gera_e_renderiza_alerta(self):
        response = self.client.get(reverse("notificacoes:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Devolução próxima")
        self.assertContains(response, self.aluno.nome)
        self.assertEqual(Notificacao.objects.count(), 1)

    def test_rotina_nao_duplica_alerta(self):
        gerar_alertas_para(self.user)
        gerar_alertas_para(self.user)

        self.assertEqual(Notificacao.objects.count(), 1)

    def test_comando_sincroniza_alertas_para_usuarios_ativos(self):
        saida = StringIO()

        call_command("sincronizar_alertas", stdout=saida)

        self.assertEqual(Notificacao.objects.count(), 1)
        self.assertIn(
            "Alertas verificados para 1 usuário(s).",
            saida.getvalue(),
        )
