from datetime import timedelta
from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from alunos.models import Aluno
from comunicacoes.models import Mensagem
from livros.models import Categoria, Livro
from .forms import EmprestimoForm
from .models import Emprestimo
from .services import(
    RegraEmprestimoError,
    atualizar_atrasos,
    devolver_emprestimo,
    registrar_emprestimo,
    renovar_emprestimo,
)
from django.urls import reverse

# Create your tests here.

class EmprestimoServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("biblioteca", password="senha-forte")
        self.aluno = Aluno.objects.create(
            matricula = "2026001",
            nome = "nome teste",
            serie = "1°",
            turma = "A",
            turno = "M",
            cpf = "12345678910",
        )
        categoria = Categoria.objects.create(nome="Literatura")
        self.livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Livro",
            autor="zezin",
            editora="zezin livros",
            categoria=categoria,
            cdd="123",
            local_estante="A=01",
            etiqueta="LIV-001",
            quantidade_total=1,
            quantidade_disponivel=1,
        )

    def registrar(self):
        return registrar_emprestimo(
            aluno=self.aluno,
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=7),
            usuario=self.user,
        )

    def test_emprestimo_reduz_estoque(self):
        emprestimo = self.registrar()
        self.livro.refresh_from_db()
        self.assertEqual(emprestimo.situacao, emprestimo.Situacao.ATIVO)
        self.assertEqual(self.livro.quantidade_disponivel, 0)

    def test_emprestimo_com_email_cria_mensagem_de_confirmacao(self):
        self.aluno.email = "aluno@example.com"
        self.aluno.save(update_fields=["email"])

        emprestimo = self.registrar()

        self.assertTrue(
            Mensagem.objects.filter(
                tipo=Mensagem.Tipo.EMPRESTIMO,
                aluno=self.aluno,
                emprestimo=emprestimo,
                destinatario=self.aluno.email,
            ).exists()
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="biblioteca@example.com",
    )
    def test_emprestimo_com_email_e_enviado_apos_confirmacao(self):
        self.aluno.email = "aluno@example.com"
        self.aluno.save(update_fields=["email"])

        with self.captureOnCommitCallbacks(execute=True):
            emprestimo = self.registrar()

        mensagem = Mensagem.objects.get(
            tipo=Mensagem.Tipo.EMPRESTIMO,
            emprestimo=emprestimo,
        )
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertEqual(len(mail.outbox), 1)

    def test_sem_estoque_nao_cria_emprestimo(self):
        self.livro.quantidade_disponivel = 0
        self.livro.save(update_fields=["quantidade_disponivel"])
        with self.assertRaises(RegraEmprestimoError):
            self.registrar()
        self.assertEqual(Emprestimo.objects.count(), 0)

    def test_devolucao_recompoe_estoque_sem_apagar_historico(self):
        emprestimo = self.registrar()
        devolver_emprestimo(emprestimo=emprestimo)
        self.livro.refresh_from_db()
        emprestimo.refresh_from_db()
        self.assertEqual(self.livro.quantidade_disponivel, 1)
        self.assertEqual(emprestimo.situacao, Emprestimo.Situacao.DEVOLVIDO)
        self.assertTrue(Emprestimo.objects.filter(pk=emprestimo.pk).exists())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="biblioteca@example.com",
    )
    def test_devolucao_envia_confirmacao_apos_salvar(self):
        self.aluno.email = "aluno@example.com"
        self.aluno.save(update_fields=["email"])
        emprestimo = self.registrar()

        with self.captureOnCommitCallbacks(execute=True):
            devolver_emprestimo(emprestimo=emprestimo)

        mensagem = Mensagem.objects.get(
            tipo=Mensagem.Tipo.DEVOLUCAO,
            emprestimo=emprestimo,
        )
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertIn("devolvido com sucesso", mensagem.corpo_html)
        self.assertEqual(len(mail.outbox), 1)

    def test_devolucao_dupla_e_bloqueada(self):
        emprestimo = self.registrar()
        devolver_emprestimo(emprestimo=emprestimo)
        with self.assertRaises(RegraEmprestimoError):
            devolver_emprestimo(emprestimo=emprestimo)
        self.livro.refresh_from_db()
        self.assertEqual(self.livro.quantidade_disponivel, 1)

    def test_renovacao_estende_prazo(self):
        emprestimo = self.registrar()
        prazo_antigo = emprestimo.data_prevista
        emprestimo = renovar_emprestimo(emprestimo=emprestimo)
        self.assertEqual(emprestimo.data_prevista, prazo_antigo + timedelta(days=7))
        self.assertEqual(emprestimo.renovacoes, 1)

    def test_ultimo_exemplar_nao_pode_ser_emprestado_duas_vezes(self):
        self.registrar()
        outro_aluno = Aluno.objects.create(
            matricula="2026002",
            nome="Outro aluno",
            serie="1°",
            turma="B",
            turno="V",
            cpf="11144477735",
        )

        with self.assertRaises(RegraEmprestimoError):
            registrar_emprestimo(
                aluno=outro_aluno,
                livro=self.livro,
                data_prevista=timezone.localdate() + timedelta(days=7),
                usuario=self.user,
            )

        self.assertEqual(Emprestimo.objects.count(), 1)

    def test_terceira_renovacao_e_rejeitada(self):
        emprestimo = self.registrar()
        emprestimo = renovar_emprestimo(emprestimo=emprestimo)
        emprestimo = renovar_emprestimo(emprestimo=emprestimo)

        with self.assertRaises(RegraEmprestimoError):
            renovar_emprestimo(emprestimo=emprestimo)

        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.renovacoes, 2)

    def test_atraso_e_atualizado_pela_data(self):
        emprestimo = self.registrar()
        hoje = timezone.localdate()
        Emprestimo.objects.filter(pk=emprestimo.pk).update(
            data_inicio=hoje - timedelta(days=2),
            data_prevista=hoje - timedelta(days=1),
        )

        atualizados = atualizar_atrasos()

        emprestimo.refresh_from_db()
        self.assertEqual(atualizados, 1)
        self.assertEqual(emprestimo.situacao, Emprestimo.Situacao.ATRASADO)

    def test_datas_impossiveis_sao_rejeitadas(self):
        with self.assertRaises(RegraEmprestimoError):
            registrar_emprestimo(
                aluno=self.aluno,
                livro=self.livro,
                data_prevista=timezone.localdate() - timedelta(days=1),
                usuario=self.user,
            )

        emprestimo = self.registrar()
        with self.assertRaises(RegraEmprestimoError):
            devolver_emprestimo(
                emprestimo=emprestimo,
                data_devolucao=emprestimo.data_inicio - timedelta(days=1),
            )

class FluxoEmprestimoViewTests(EmprestimoServiceTests):
    def setUp(self):
        super().setUp()
        permissoes = Permission.objects.filter(
            codename__in=(
                "add_emprestimo",
                "view_emprestimo",
                "pode_devolver_emprestimo",
                "pode_renovar_emprestimo",
            )
        )
        self.user.user_permissions.set(permissoes)
        self.client.force_login(self.user)

    def test_fluxo_web_emprestar_e_devolver(self):
        response = self.client.post(
            reverse("emprestimos:novo"),
            {
                "aluno": self.aluno.pk,
                "livro": self.livro.pk,
                "data_prevista": (
                    timezone.localdate() + timedelta(days=7)
                ).isoformat(),
                "observacoes": "",
            },
        )
        emprestimo = Emprestimo.objects.get()
        self.assertRedirects(
            response,
            reverse("emprestimos:detalhe", args=[emprestimo.pk]),
        )

        response = self.client.post(
            reverse("emprestimos:devolver", args=[emprestimo.pk]),
        )
        self.assertRedirects(
            response,
            reverse("emprestimos:detalhe", args=[emprestimo.pk]),
        )
        emprestimo.refresh_from_db()
        self.assertEqual(
            emprestimo.situacao,
            emprestimo.Situacao.DEVOLVIDO,
        )

    def test_por_devolucao_get_retorna_405(self):
        emprestimo = self.registrar()
        response = self.client.get(
            reverse("emprestimos:devolver", args=[emprestimo.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_lista_por_get_nao_atualiza_atrasos(self):
        emprestimo = self.registrar()
        hoje = timezone.localdate()
        Emprestimo.objects.filter(pk=emprestimo.pk).update(
            data_inicio=hoje - timedelta(days=2),
            data_prevista=hoje - timedelta(days=1),
        )

        response = self.client.get(reverse("emprestimos:lista"))

        self.assertEqual(response.status_code, 200)
        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.situacao, Emprestimo.Situacao.ATIVO)


class EmprestimoAdminTests(TestCase):
    def test_admin_nao_permite_excluir_emprestimos(self):
        model_admin = admin.site._registry[Emprestimo]

        self.assertFalse(model_admin.has_delete_permission(request=None))
