from datetime import timedelta
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.utils import timezone
from alunos.models import Aluno
from livros.models import Categoria, Livro
from .models import Emprestimo
from .services import(
    RegraEmprestimoError,
    devolver_emprestimo,
    registrar_emprestimo,
    renovar_emprestimo,
)

# Create your tests here.

class EmprestimoServiceTest(TestCase):
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