from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alunos.models import Aluno
from emprestimos.models import Emprestimo
from emprestimos.services import (
    RegraEmprestimoError,
    devolver_emprestimo,
    registrar_emprestimo,
    renovar_emprestimo,
)
from livros.models import Categoria, Livro

from .forms import ReservaForm
from .models import Reserva
from .services import (
    RegraReservaError,
    cancelar_reserva,
    criar_reserva,
    liberar_proximas_reservas,
    posicao_fila,
)


class ReservaBaseTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user("operador-reservas")
        self.categoria = Categoria.objects.create(nome="Reservas")
        self.livro = Livro.objects.create(
            isbn="9780306406157",
            titulo="Livro com fila",
            autor="Autora",
            editora="Editora",
            categoria=self.categoria,
            cdd="800",
            local_estante="R-01",
            etiqueta="RES-001",
            quantidade_total=2,
            quantidade_disponivel=0,
        )
        self.alunos = [self.criar_aluno(indice) for indice in range(1, 8)]

    def criar_aluno(self, indice, *, ativo=True):
        return Aluno.objects.create(
            matricula=f"RES-{indice:03d}",
            nome=f"Aluno Reserva {indice}",
            serie="1º ano",
            turma="A",
            turno=Aluno.Turno.MATUTINO,
            cpf=f"98{indice:09d}",
            email=f"aluno{indice}@example.com",
            ativo=ativo,
        )


class ReservaServiceTests(ReservaBaseTests):
    def test_reserva_duplicada_e_bloqueada(self):
        criar_reserva(aluno=self.alunos[0], livro=self.livro)

        with self.assertRaisesRegex(RegraReservaError, "reserva ativa"):
            criar_reserva(aluno=self.alunos[0], livro=self.livro)

        self.assertEqual(Reserva.objects.count(), 1)

    def test_aluno_com_emprestimo_aberto_nao_pode_reservar(self):
        Emprestimo.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=7),
            registrado_por=self.usuario,
        )

        with self.assertRaisesRegex(RegraReservaError, "já possui"):
            criar_reserva(aluno=self.alunos[0], livro=self.livro)

        self.assertFalse(Reserva.objects.exists())

    def test_aluno_e_livro_inativos_nao_podem_gerar_reserva(self):
        self.alunos[0].ativo = False
        self.alunos[0].save(update_fields=["ativo"])
        with self.assertRaisesRegex(RegraReservaError, "Aluno inativo"):
            criar_reserva(aluno=self.alunos[0], livro=self.livro)

        self.alunos[0].ativo = True
        self.alunos[0].save(update_fields=["ativo"])
        self.livro.ativo = False
        self.livro.save(update_fields=["ativo"])
        with self.assertRaisesRegex(RegraReservaError, "livro inativo"):
            criar_reserva(aluno=self.alunos[0], livro=self.livro)

    def test_fila_fifo_libera_todas_as_vagas_disponiveis(self):
        self.livro.quantidade_disponivel = 2
        self.livro.save(update_fields=["quantidade_disponivel"])
        fila = [
            Reserva.objects.create(aluno=aluno, livro=self.livro)
            for aluno in self.alunos[:3]
        ]

        liberadas = liberar_proximas_reservas(livro_id=self.livro.pk)

        self.assertEqual(
            [reserva.pk for reserva in liberadas],
            [fila[0].pk, fila[1].pk],
        )
        for reserva in fila:
            reserva.refresh_from_db()
        self.assertEqual(fila[0].status, Reserva.Status.DISPONIVEL)
        self.assertEqual(fila[1].status, Reserva.Status.DISPONIVEL)
        self.assertEqual(fila[2].status, Reserva.Status.AGUARDANDO)
        self.assertIsNotNone(fila[0].disponivel_ate)
        self.assertIsNotNone(fila[1].disponivel_ate)

    def test_reserva_vencida_expira_e_libera_a_proxima(self):
        self.livro.quantidade_disponivel = 1
        self.livro.save(update_fields=["quantidade_disponivel"])
        vencida = Reserva.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            status=Reserva.Status.DISPONIVEL,
            disponibilizada_em=timezone.now() - timedelta(hours=3),
            disponivel_ate=timezone.now() - timedelta(hours=1),
        )
        proxima = Reserva.objects.create(
            aluno=self.alunos[1],
            livro=self.livro,
        )

        liberadas = liberar_proximas_reservas(livro_id=self.livro.pk)

        vencida.refresh_from_db()
        proxima.refresh_from_db()
        self.assertEqual(vencida.status, Reserva.Status.EXPIRADA)
        self.assertEqual(proxima.status, Reserva.Status.DISPONIVEL)
        self.assertEqual([reserva.pk for reserva in liberadas], [proxima.pk])

    def test_cancelamento_avanca_a_fila(self):
        self.livro.quantidade_disponivel = 1
        self.livro.save(update_fields=["quantidade_disponivel"])
        atual = Reserva.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            status=Reserva.Status.DISPONIVEL,
            disponibilizada_em=timezone.now(),
            disponivel_ate=timezone.now() + timedelta(hours=2),
        )
        proxima = Reserva.objects.create(
            aluno=self.alunos[1],
            livro=self.livro,
        )

        cancelar_reserva(reserva=atual)

        atual.refresh_from_db()
        proxima.refresh_from_db()
        self.assertEqual(atual.status, Reserva.Status.CANCELADA)
        self.assertEqual(proxima.status, Reserva.Status.DISPONIVEL)

    def test_posicao_da_fila_respeita_criacao_e_chave_primaria(self):
        primeira = Reserva.objects.create(
            aluno=self.alunos[0], livro=self.livro
        )
        segunda = Reserva.objects.create(
            aluno=self.alunos[1], livro=self.livro
        )
        instante = timezone.now()
        Reserva.objects.filter(pk__in=(primeira.pk, segunda.pk)).update(
            criada_em=instante
        )
        primeira.refresh_from_db()
        segunda.refresh_from_db()

        self.assertEqual(posicao_fila(primeira), 1)
        self.assertEqual(posicao_fila(segunda), 2)


class ReservaEmprestimoIntegrationTests(ReservaBaseTests):
    def test_devolucao_disponibiliza_reserva_em_espera(self):
        emprestimo = Emprestimo.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=7),
            registrado_por=self.usuario,
        )
        reserva = Reserva.objects.create(
            aluno=self.alunos[1], livro=self.livro
        )

        devolver_emprestimo(emprestimo=emprestimo)

        self.livro.refresh_from_db()
        reserva.refresh_from_db()
        self.assertEqual(self.livro.quantidade_disponivel, 1)
        self.assertEqual(reserva.status, Reserva.Status.DISPONIVEL)

    def test_reserva_do_aluno_e_atendida_ao_emprestar(self):
        self.livro.quantidade_disponivel = 1
        self.livro.save(update_fields=["quantidade_disponivel"])
        reserva = Reserva.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            status=Reserva.Status.DISPONIVEL,
            disponibilizada_em=timezone.now(),
            disponivel_ate=timezone.now() + timedelta(hours=2),
        )

        emprestimo = registrar_emprestimo(
            aluno=self.alunos[0],
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=7),
            usuario=self.usuario,
        )

        reserva.refresh_from_db()
        self.livro.refresh_from_db()
        self.assertEqual(reserva.status, Reserva.Status.ATENDIDA)
        self.assertEqual(emprestimo.aluno, self.alunos[0])
        self.assertEqual(self.livro.quantidade_disponivel, 0)

    def test_exemplar_destinado_nao_e_emprestado_a_outro_aluno(self):
        self.livro.quantidade_disponivel = 1
        self.livro.save(update_fields=["quantidade_disponivel"])
        Reserva.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            status=Reserva.Status.DISPONIVEL,
            disponibilizada_em=timezone.now(),
            disponivel_ate=timezone.now() + timedelta(hours=2),
        )

        with self.assertRaisesRegex(RegraEmprestimoError, "destinados"):
            registrar_emprestimo(
                aluno=self.alunos[1],
                livro=self.livro,
                data_prevista=timezone.localdate() + timedelta(days=7),
                usuario=self.usuario,
            )

        self.livro.refresh_from_db()
        self.assertEqual(self.livro.quantidade_disponivel, 1)
        self.assertFalse(Emprestimo.objects.exists())

    def test_renovacao_e_bloqueada_quando_ha_outro_aluno_na_fila(self):
        emprestimo = Emprestimo.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            data_prevista=timezone.localdate() + timedelta(days=7),
            registrado_por=self.usuario,
        )
        Reserva.objects.create(aluno=self.alunos[1], livro=self.livro)

        with self.assertRaisesRegex(RegraEmprestimoError, "reserva na fila"):
            renovar_emprestimo(emprestimo=emprestimo)

        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.renovacoes, 0)


class ReservaFormTests(ReservaBaseTests):
    def test_formulario_exibe_somente_alunos_e_livros_ativos(self):
        aluno_inativo = self.criar_aluno(20, ativo=False)
        livro_inativo = Livro.objects.create(
            isbn="9781861972712",
            titulo="Livro inativo",
            autor="Autor",
            editora="Editora",
            categoria=self.categoria,
            cdd="800",
            local_estante="R-02",
            etiqueta="RES-002",
            ativo=False,
        )

        form = ReservaForm()

        self.assertNotIn(aluno_inativo, form.fields["aluno"].queryset)
        self.assertNotIn(livro_inativo, form.fields["livro"].queryset)
        self.assertIn(self.alunos[0], form.fields["aluno"].queryset)
        self.assertIn(self.livro, form.fields["livro"].queryset)


class ReservaViewTests(ReservaBaseTests):
    def setUp(self):
        super().setUp()
        self.reserva = Reserva.objects.create(
            aluno=self.alunos[0], livro=self.livro
        )
        self.client.force_login(self.usuario)

    def conceder(self, *codenames):
        permissoes = Permission.objects.filter(
            content_type__app_label="reservas",
            codename__in=codenames,
        )
        self.usuario.user_permissions.add(*permissoes)

    def test_lista_retorna_403_sem_permissao(self):
        response = self.client.get(reverse("reservas:lista"))

        self.assertEqual(response.status_code, 403)

    def test_cancelamento_retorna_403_sem_permissao(self):
        response = self.client.post(
            reverse("reservas:cancelar", args=[self.reserva.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.status, Reserva.Status.AGUARDANDO)

    def test_cancelamento_nao_aceita_get(self):
        self.conceder("change_reserva")

        response = self.client.get(
            reverse("reservas:cancelar", args=[self.reserva.pk])
        )

        self.assertEqual(response.status_code, 405)

    def test_usuario_com_permissao_visualiza_fila(self):
        self.conceder("view_reserva")

        response = self.client.get(reverse("reservas:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alunos[0].nome)
        self.assertContains(response, "1ª")

    def test_nova_reserva_por_post_redireciona_para_lista(self):
        self.conceder("add_reserva", "view_reserva")

        response = self.client.post(
            reverse("reservas:nova"),
            {"aluno": self.alunos[1].pk, "livro": self.livro.pk},
        )

        self.assertRedirects(response, reverse("reservas:lista"))
        self.assertTrue(
            Reserva.objects.filter(
                aluno=self.alunos[1], livro=self.livro
            ).exists()
        )


class ExpirarReservasCommandTests(ReservaBaseTests):
    def test_comando_expira_reserva_e_avanca_fila(self):
        self.livro.quantidade_disponivel = 1
        self.livro.save(update_fields=["quantidade_disponivel"])
        vencida = Reserva.objects.create(
            aluno=self.alunos[0],
            livro=self.livro,
            status=Reserva.Status.DISPONIVEL,
            disponibilizada_em=timezone.now() - timedelta(hours=3),
            disponivel_ate=timezone.now() - timedelta(hours=1),
        )
        proxima = Reserva.objects.create(
            aluno=self.alunos[1], livro=self.livro
        )
        saida = StringIO()

        call_command("expirar_reservas", stdout=saida)

        vencida.refresh_from_db()
        proxima.refresh_from_db()
        self.assertEqual(vencida.status, Reserva.Status.EXPIRADA)
        self.assertEqual(proxima.status, Reserva.Status.DISPONIVEL)
        self.assertIn("1 reserva(s) expirada(s)", saida.getvalue())


class ReservaPermissaoTests(TestCase):
    def test_grupos_recebem_permissoes_sem_exclusao_de_reserva(self):
        call_command("configurar_permissoes", stdout=StringIO())

        bibliotecarios = Group.objects.get(name="Bibliotecários")
        auxiliares = Group.objects.get(name="Auxiliares")
        direcao = Group.objects.get(name="Direção")
        for grupo in (bibliotecarios, auxiliares):
            for codename in ("view_reserva", "add_reserva", "change_reserva"):
                self.assertTrue(
                    grupo.permissions.filter(
                        content_type__app_label="reservas",
                        codename=codename,
                    ).exists()
                )
            self.assertFalse(
                grupo.permissions.filter(
                    content_type__app_label="reservas",
                    codename="delete_reserva",
                ).exists()
            )

        self.assertTrue(
            direcao.permissions.filter(
                content_type__app_label="reservas",
                codename="view_reserva",
            ).exists()
        )
        self.assertFalse(
            direcao.permissions.filter(
                content_type__app_label="reservas",
                codename__in=("add_reserva", "change_reserva", "delete_reserva"),
            ).exists()
        )
        for grupo in (bibliotecarios, direcao):
            self.assertTrue(
                grupo.permissions.filter(
                    content_type__app_label="comunicacoes",
                    codename="view_mensagem",
                ).exists()
            )
        self.assertFalse(
            auxiliares.permissions.filter(
                content_type__app_label="comunicacoes",
                codename="view_mensagem",
            ).exists()
        )
