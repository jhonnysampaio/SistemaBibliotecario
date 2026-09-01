from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Categoria, Livro

from .models import Mensagem
from .services import enfileirar_pendencia_ano_letivo


class MensagemPendenciaAnualTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "biblioteca-comunicacoes",
            password="senha-forte",
        )
        self.aluno = Aluno.objects.create(
            matricula="COM-2026-001",
            nome="Aluno Comunicação",
            serie="1º ano",
            turma="A",
            turno="M",
            cpf="12345678910",
            email="aluno@example.com",
        )
        categoria = Categoria.objects.create(nome="Comunicações")
        livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Livro pendente",
            autor="Autora",
            editora="Editora",
            categoria=categoria,
            cdd="800",
            local_estante="A-01",
            etiqueta="COM-001",
        )
        self.emprestimo = Emprestimo.objects.create(
            aluno=self.aluno,
            livro=livro,
            data_prevista=timezone.localdate(),
            registrado_por=self.user,
        )

    def test_enfileiramento_e_idempotente(self):
        primeira = enfileirar_pendencia_ano_letivo(
            emprestimo=self.emprestimo
        )
        segunda = enfileirar_pendencia_ano_letivo(
            emprestimo=self.emprestimo
        )

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(Mensagem.objects.count(), 1)
        self.assertEqual(
            primeira.tipo,
            Mensagem.Tipo.PENDENCIA_ANUAL,
        )
        self.assertEqual(primeira.status, Mensagem.Status.PENDENTE)

    def test_aluno_sem_email_nao_gera_mensagem(self):
        self.aluno.email = ""
        self.aluno.save(update_fields=["email"])

        mensagem = enfileirar_pendencia_ano_letivo(
            emprestimo=self.emprestimo
        )

        self.assertIsNone(mensagem)
        self.assertFalse(Mensagem.objects.exists())

    def test_view_cria_mensagem_por_post(self):
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="emprestimos",
                codename="view_emprestimo",
            ),
            Permission.objects.get(
                content_type__app_label="alunos",
                codename="change_aluno",
            ),
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "alunos:solicitar_devolucao",
                args=[self.emprestimo.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("alunos:fechamento_ano_letivo"),
        )
        self.assertEqual(Mensagem.objects.count(), 1)

    def test_view_nao_aceita_get(self):
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="emprestimos",
                codename="view_emprestimo",
            )
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "alunos:solicitar_devolucao",
                args=[self.emprestimo.pk],
            )
        )

        self.assertEqual(response.status_code, 405)
