from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib import admin
from django.core import mail
from django.core.management import call_command
from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from emprestimos.models import Emprestimo
from livros.models import Categoria, Livro
from reservas.models import Reserva

from .models import Mensagem
from .services import (
    enfileirar_cadastro_aluno,
    enfileirar_atraso,
    enfileirar_devolucao_emprestimo,
    enfileirar_emprestimo_realizado,
    enfileirar_pendencia_ano_letivo,
    enfileirar_prazo_emprestimo,
    enfileirar_reserva_criada,
    enfileirar_reserva_disponivel,
)
from .envio import reivindicar_mensagem
from .agendador import _processo_principal_do_runserver


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


class MensagemAutomaticaBaseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("mensagens-automaticas")
        self.aluno_atraso = Aluno.objects.create(
            matricula="MSG-001",
            nome="Aluno Atraso",
            serie="1º ano",
            turma="A",
            turno=Aluno.Turno.MATUTINO,
            cpf="98000000001",
            email="atraso@example.com",
        )
        self.aluno_reserva = Aluno.objects.create(
            matricula="MSG-002",
            nome="Aluno Reserva",
            serie="2º ano",
            turma="B",
            turno=Aluno.Turno.VESPERTINO,
            cpf="98000000002",
            email="reserva@example.com",
        )
        categoria = Categoria.objects.create(nome="Mensagens automáticas")
        self.livro = Livro.objects.create(
            isbn="9781861972712",
            titulo="Livro das mensagens",
            autor="Autora",
            editora="Editora",
            categoria=categoria,
            cdd="800",
            local_estante="M-01",
            etiqueta="MSG-001",
            quantidade_total=1,
            quantidade_disponivel=1,
        )
        self.emprestimo = Emprestimo.objects.create(
            aluno=self.aluno_atraso,
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=1),
            registrado_por=self.user,
        )
        Emprestimo.objects.filter(pk=self.emprestimo.pk).update(
            data_inicio=timezone.localdate() - timedelta(days=2),
            data_prevista=timezone.localdate() - timedelta(days=1),
        )
        self.emprestimo.refresh_from_db()
        self.reserva = Reserva.objects.create(
            aluno=self.aluno_reserva,
            livro=self.livro,
            status=Reserva.Status.DISPONIVEL,
            disponibilizada_em=timezone.now(),
            disponivel_ate=timezone.now() + timedelta(hours=48),
        )

    def criar_mensagem(self, **campos):
        padrao = {
            "tipo": Mensagem.Tipo.ATRASO,
            "chave": f"teste:{Mensagem.objects.count() + 1}",
            "destinatario": "destino@example.com",
            "assunto": "Assunto de teste",
            "corpo": "Corpo de teste",
        }
        padrao.update(campos)
        return Mensagem.objects.create(**padrao)


class NovosEventosMensagemTests(MensagemAutomaticaBaseTests):
    def test_cadastro_de_aluno_e_enfileirado_sem_dados_sensiveis(self):
        primeira = enfileirar_cadastro_aluno(aluno=self.aluno_atraso)
        segunda = enfileirar_cadastro_aluno(aluno=self.aluno_atraso)

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(primeira.tipo, Mensagem.Tipo.CADASTRO)
        self.assertEqual(primeira.destinatario, self.aluno_atraso.email)
        self.assertNotIn(self.aluno_atraso.cpf, primeira.corpo)
        self.assertNotIn(self.aluno_atraso.cpf, primeira.corpo_html)
        self.assertIn("Bem-vindo à biblioteca", primeira.corpo_html)
        self.assertIn("#0f3029", primeira.corpo_html)
        self.assertEqual(
            Mensagem.objects.filter(tipo=Mensagem.Tipo.CADASTRO).count(),
            1,
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="biblioteca@example.com",
    )
    def test_cadastro_envia_email_imediatamente_apos_confirmar_transacao(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            mensagem = enfileirar_cadastro_aluno(aluno=self.aluno_atraso)

        mensagem.refresh_from_db()
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertEqual(mensagem.tentativas, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.aluno_atraso.email])
        self.assertEqual(len(mail.outbox[0].alternatives), 1)

    @patch("comunicacoes.envio.send_mail")
    def test_falha_no_envio_imediato_nao_remove_cadastro(
        self,
        send_mail_mock,
    ):
        send_mail_mock.side_effect = OSError("SMTP indisponível")

        with self.captureOnCommitCallbacks(execute=True):
            mensagem = enfileirar_cadastro_aluno(aluno=self.aluno_atraso)

        mensagem.refresh_from_db()
        self.assertTrue(Aluno.objects.filter(pk=self.aluno_atraso.pk).exists())
        self.assertEqual(mensagem.status, Mensagem.Status.FALHA)
        self.assertEqual(mensagem.tentativas, 1)
        self.assertEqual(mensagem.erro, "SMTP indisponível")

    def test_emprestimo_realizado_e_enfileirado_uma_vez(self):
        primeira = enfileirar_emprestimo_realizado(
            emprestimo=self.emprestimo
        )
        segunda = enfileirar_emprestimo_realizado(
            emprestimo=self.emprestimo
        )

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(primeira.tipo, Mensagem.Tipo.EMPRESTIMO)
        self.assertIn(self.livro.titulo, primeira.corpo)
        self.assertIn(
            self.emprestimo.data_prevista.strftime("%d/%m/%Y"),
            primeira.corpo,
        )
        self.assertIn("Boa leitura!", primeira.corpo_html)
        self.assertIn(self.livro.titulo, primeira.corpo_html)

    def test_prazo_proximo_considera_a_data_prevista_na_chave(self):
        primeira = enfileirar_prazo_emprestimo(
            emprestimo=self.emprestimo
        )
        segunda = enfileirar_prazo_emprestimo(
            emprestimo=self.emprestimo
        )

        self.assertEqual(primeira.pk, segunda.pk)
        self.assertEqual(primeira.tipo, Mensagem.Tipo.PRAZO)
        self.assertEqual(
            primeira.chave,
            f"prazo:{self.emprestimo.pk}:{self.emprestimo.data_prevista}",
        )
        self.assertIn("O prazo está chegando", primeira.corpo_html)
        self.assertIn("#d5a447", primeira.corpo_html)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="biblioteca@example.com",
    )
    def test_demais_eventos_enviam_email_assim_que_sao_criados(self):
        self.emprestimo.data_devolucao = timezone.localdate()
        casos = (
            (
                Mensagem.Tipo.EMPRESTIMO,
                lambda: enfileirar_emprestimo_realizado(
                    emprestimo=self.emprestimo
                ),
            ),
            (
                Mensagem.Tipo.DEVOLUCAO,
                lambda: enfileirar_devolucao_emprestimo(
                    emprestimo=self.emprestimo
                ),
            ),
            (
                Mensagem.Tipo.PRAZO,
                lambda: enfileirar_prazo_emprestimo(
                    emprestimo=self.emprestimo
                ),
            ),
            (
                Mensagem.Tipo.ATRASO,
                lambda: enfileirar_atraso(emprestimo=self.emprestimo),
            ),
            (
                Mensagem.Tipo.RESERVA_CRIADA,
                lambda: enfileirar_reserva_criada(reserva=self.reserva),
            ),
            (
                Mensagem.Tipo.RESERVA,
                lambda: enfileirar_reserva_disponivel(
                    reserva=self.reserva
                ),
            ),
        )

        for tipo, enfileirar in casos:
            with self.subTest(tipo=tipo):
                with self.captureOnCommitCallbacks(execute=True) as callbacks:
                    mensagem = enfileirar()

                mensagem.refresh_from_db()
                self.assertEqual(len(callbacks), 1)
                self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
                self.assertEqual(mensagem.tentativas, 1)

        self.assertEqual(len(mail.outbox), len(casos))


class AgendadorServidorTests(TestCase):
    def test_inicia_apenas_no_processo_principal_do_runserver(self):
        self.assertFalse(
            _processo_principal_do_runserver(
                argv=["manage.py", "test"],
                ambiente={},
            )
        )
        self.assertFalse(
            _processo_principal_do_runserver(
                argv=["manage.py", "runserver"],
                ambiente={},
            )
        )
        self.assertTrue(
            _processo_principal_do_runserver(
                argv=["manage.py", "runserver"],
                ambiente={"RUN_MAIN": "true"},
            )
        )
        self.assertTrue(
            _processo_principal_do_runserver(
                argv=["manage.py", "runserver", "--noreload"],
                ambiente={},
            )
        )


class GerarMensagensTests(MensagemAutomaticaBaseTests):
    def test_gerar_mensagens_duas_vezes_nao_duplica(self):
        primeira_saida = StringIO()
        segunda_saida = StringIO()

        call_command("gerar_mensagens", stdout=primeira_saida)
        call_command("gerar_mensagens", stdout=segunda_saida)

        self.emprestimo.refresh_from_db()
        self.assertEqual(
            self.emprestimo.situacao,
            Emprestimo.Situacao.ATRASADO,
        )
        self.assertEqual(Mensagem.objects.count(), 2)
        self.assertTrue(
            Mensagem.objects.filter(
                chave=(
                    f"atraso:{self.emprestimo.pk}:"
                    f"{self.emprestimo.data_prevista.isoformat()}"
                ),
                emprestimo=self.emprestimo,
            ).exists()
        )
        self.assertTrue(
            Mensagem.objects.filter(
                chave=f"reserva:{self.reserva.pk}:disponivel",
                reserva=self.reserva,
            ).exists()
        )
        self.assertIn("Mensagens sincronizadas", primeira_saida.getvalue())
        self.assertIn("Mensagens sincronizadas", segunda_saida.getvalue())

    def test_gera_um_lembrete_quando_faltam_dois_dias(self):
        hoje = timezone.localdate()
        Emprestimo.objects.filter(pk=self.emprestimo.pk).update(
            data_inicio=hoje,
            data_prevista=hoje + timedelta(days=2),
            situacao=Emprestimo.Situacao.ATIVO,
        )
        self.emprestimo.refresh_from_db()

        call_command("gerar_mensagens", stdout=StringIO())
        call_command("gerar_mensagens", stdout=StringIO())

        mensagens = Mensagem.objects.filter(
            tipo=Mensagem.Tipo.PRAZO,
            emprestimo=self.emprestimo,
        )
        self.assertEqual(mensagens.count(), 1)
        self.assertIn(self.livro.titulo, mensagens.get().corpo)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="biblioteca@example.com",
    )
    def test_prazo_proximo_e_enviado_na_mesma_sincronizacao(self):
        hoje = timezone.localdate()
        self.reserva.delete()
        Emprestimo.objects.filter(pk=self.emprestimo.pk).update(
            data_inicio=hoje,
            data_prevista=hoje + timedelta(days=2),
            situacao=Emprestimo.Situacao.ATIVO,
        )

        with self.captureOnCommitCallbacks(execute=True):
            call_command("gerar_mensagens", stdout=StringIO())

        mensagem = Mensagem.objects.get(
            tipo=Mensagem.Tipo.PRAZO,
            emprestimo=self.emprestimo,
        )
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="biblioteca@example.com",
    )
    def test_atraso_e_enviado_na_mesma_sincronizacao(self):
        self.reserva.delete()

        with self.captureOnCommitCallbacks(execute=True):
            call_command("gerar_mensagens", stdout=StringIO())

        mensagem = Mensagem.objects.get(
            tipo=Mensagem.Tipo.ATRASO,
            emprestimo=self.emprestimo,
        )
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertEqual(len(mail.outbox), 1)

    def test_aluno_sem_email_nao_gera_atraso_nem_reserva(self):
        self.aluno_atraso.email = ""
        self.aluno_atraso.save(update_fields=["email"])
        self.aluno_reserva.email = ""
        self.aluno_reserva.save(update_fields=["email"])

        atraso = enfileirar_atraso(emprestimo=self.emprestimo)
        reserva = enfileirar_reserva_disponivel(reserva=self.reserva)

        self.assertIsNone(atraso)
        self.assertIsNone(reserva)
        self.assertFalse(Mensagem.objects.exists())

    def test_mensagens_usam_chaves_estaveis_e_dados_minimos(self):
        atraso = enfileirar_atraso(emprestimo=self.emprestimo)
        reserva = enfileirar_reserva_disponivel(reserva=self.reserva)

        self.assertEqual(
            atraso.chave,
            f"atraso:{self.emprestimo.pk}:{self.emprestimo.data_prevista}",
        )
        self.assertEqual(
            reserva.chave,
            f"reserva:{self.reserva.pk}:disponivel",
        )
        self.assertNotIn(self.aluno_atraso.cpf, atraso.corpo)
        self.assertNotIn(self.aluno_reserva.cpf, reserva.corpo)
        self.assertIn(self.livro.titulo, atraso.corpo)
        self.assertIn(self.livro.titulo, reserva.corpo)
        self.assertIn("Precisamos da sua atenção", atraso.corpo_html)
        self.assertIn("#b64a44", atraso.corpo_html)
        self.assertIn("Seu livro está esperando", reserva.corpo_html)
        self.assertIn("#769781", reserva.corpo_html)


class ReivindicarMensagemTests(MensagemAutomaticaBaseTests):
    def test_dois_reivindicadores_nao_recebem_a_mesma_mensagem(self):
        mensagem = self.criar_mensagem()

        primeira = reivindicar_mensagem()
        segunda = reivindicar_mensagem()

        self.assertEqual(primeira.pk, mensagem.pk)
        self.assertIsNone(segunda)
        mensagem.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.PROCESSANDO)
        self.assertEqual(mensagem.tentativas, 1)

    def test_processamento_antigo_e_recuperado(self):
        mensagem = self.criar_mensagem(
            status=Mensagem.Status.PROCESSANDO,
            tentativas=1,
            ultima_tentativa_em=timezone.now() - timedelta(minutes=31),
        )

        recuperada = reivindicar_mensagem()

        self.assertEqual(recuperada.pk, mensagem.pk)
        mensagem.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.PROCESSANDO)
        self.assertEqual(mensagem.tentativas, 2)
        self.assertEqual(mensagem.erro, "")

    def test_mensagem_com_tres_tentativas_nao_e_reivindicada(self):
        mensagem = self.criar_mensagem(
            status=Mensagem.Status.FALHA,
            tentativas=3,
        )

        self.assertIsNone(reivindicar_mensagem())
        mensagem.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.FALHA)
        self.assertEqual(mensagem.tentativas, 3)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="biblioteca@example.com",
)
class EnviarMensagensTests(MensagemAutomaticaBaseTests):
    def test_envio_confirmado_atualiza_mensagem_e_reserva(self):
        mensagem = enfileirar_reserva_disponivel(reserva=self.reserva)

        call_command("enviar_mensagens", limite=50)

        mensagem.refresh_from_db()
        self.reserva.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertEqual(mensagem.tentativas, 1)
        self.assertIsNotNone(mensagem.enviada_em)
        self.assertEqual(self.reserva.notificada_em, mensagem.enviada_em)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.aluno_reserva.email])
        self.assertEqual(mail.outbox[0].body, mensagem.corpo)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        alternativa = mail.outbox[0].alternatives[0]
        self.assertEqual(alternativa.mimetype, "text/html")
        self.assertEqual(alternativa.content, mensagem.corpo_html)

    def test_mensagem_antiga_sem_html_recebe_layout_padrao(self):
        mensagem = self.criar_mensagem(corpo_html="")

        call_command("enviar_mensagens", limite=50)

        mensagem.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.ENVIADA)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        alternativa = mail.outbox[0].alternatives[0]
        self.assertEqual(alternativa.mimetype, "text/html")
        self.assertIn(mensagem.assunto, alternativa.content)
        self.assertIn("#0f3029", alternativa.content)

    @patch("comunicacoes.envio.send_mail")
    def test_retorno_zero_do_backend_registra_falha(self, send_mail_mock):
        send_mail_mock.return_value = 0
        mensagem = self.criar_mensagem()

        call_command("enviar_mensagens", limite=50)

        mensagem.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.FALHA)
        self.assertEqual(mensagem.tentativas, 3)
        self.assertIn("não confirmou", mensagem.erro)
        self.assertEqual(send_mail_mock.call_count, 3)

    @patch("comunicacoes.envio.send_mail")
    def test_excecao_smtp_registra_falha_e_limita_tentativas(
        self,
        send_mail_mock,
    ):
        send_mail_mock.side_effect = OSError("SMTP indisponível")
        mensagem = self.criar_mensagem()

        call_command("enviar_mensagens", limite=50)

        mensagem.refresh_from_db()
        self.assertEqual(mensagem.status, Mensagem.Status.FALHA)
        self.assertEqual(mensagem.tentativas, 3)
        self.assertEqual(mensagem.erro, "SMTP indisponível")
        self.assertEqual(send_mail_mock.call_count, 3)


class MensagemAdminTests(MensagemAutomaticaBaseTests):
    def test_mensagem_enviada_protege_destinatario_e_corpo(self):
        mensagem = self.criar_mensagem(status=Mensagem.Status.ENVIADA)
        model_admin = admin.site._registry[Mensagem]

        campos = model_admin.get_readonly_fields(request=None, obj=mensagem)

        self.assertIn("chave", campos)
        self.assertIn("corpo_html", campos)
        self.assertIn("status", campos)
        self.assertIn("destinatario", campos)
        self.assertIn("corpo", campos)

    def test_mensagem_pendente_permite_ajustar_destinatario_e_corpo(self):
        mensagem = self.criar_mensagem(status=Mensagem.Status.PENDENTE)
        model_admin = admin.site._registry[Mensagem]

        campos = model_admin.get_readonly_fields(request=None, obj=mensagem)

        self.assertIn("chave", campos)
        self.assertIn("corpo_html", campos)
        self.assertIn("status", campos)
        self.assertNotIn("destinatario", campos)
        self.assertNotIn("corpo", campos)
