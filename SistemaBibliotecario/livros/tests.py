from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from emprestimos.forms import EmprestimoForm

from .forms import LivroForm
from .models import Categoria, Livro
from .services import salvar_livro_com_estoque

# Create your tests here.

class LivroFormTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome="Literatura")
        self.livro = Livro.objects.create(
            isbn = "9780306406157",
            titulo = "Livro de teste",
            autor = "Autor",
            editora = "Editora",
            categoria = self.categoria,
            cdd = "800",
            local_estante = "A-01",
            etiqueta = "LIV-001",
            quantidade_total = 5,
            quantidade_disponivel = 3
        )

    def test_nao_permite_total_menor_que(self):
        form = LivroForm(
            instance = self.livro,
            data = {
                "isbn": "9780306406157",
                "titulo": "Livro de teste",
                "subtitulo": "",
                "autor": "Autor",
                "ano_publicacao": "",
                "editora": "Editora",
                "categoria": self.categoria.pk,
                "cdd": "800",
                "local_estante": "A-01",
                "etiqueta": "LIV-001",
                "quantidade_total": 1,
                "ativo": True,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("quantidade_total", form.errors)

    def test_aumento_preserva_exemplares_emprestados(self):
        form = LivroForm(
            instance = self.livro,
            data = {
                "isbn": "9780306406157",
                "titulo": "Livro de teste",
                "subtitulo": "",
                "autor": "Autor",
                "ano_publicacao": "",
                "editora": "Editora",
                "categoria": self.categoria.pk,
                "cdd": "800",
                "local_estante": "A-01",
                "etiqueta": "LIV-001",
                "quantidade_total": 8,
                "ativo": True,
            },
        )
        self.assertTrue(form.is_valid(), form.errors)
        livro = form.save()
        self.assertEqual(livro.quantidade_disponivel, 6)

    def test_servico_centraliza_atualizacao_do_estoque(self):
        self.livro.quantidade_total = 8

        salvar_livro_com_estoque(livro=self.livro)

        self.livro.refresh_from_db()
        self.assertEqual(self.livro.quantidade_disponivel, 6)

    def dados_formulario(self, **alteracoes):
        dados = {
            "isbn": "9781861972712",
            "titulo": "Outro livro",
            "subtitulo": "",
            "autor": "Outra autora",
            "ano_publicacao": "",
            "editora": "Editora",
            "categoria": self.categoria.pk,
            "cdd": "800",
            "local_estante": "A-02",
            "etiqueta": "LIV-002",
            "quantidade_total": 1,
            "ativo": True,
        }
        dados.update(alteracoes)
        return dados

    def test_rejeita_isbn_invalido(self):
        form = LivroForm(data=self.dados_formulario(isbn="123"))

        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

    def test_rejeita_isbn_duplicado(self):
        form = LivroForm(data=self.dados_formulario(isbn=self.livro.isbn))

        self.assertFalse(form.is_valid())
        self.assertIn("isbn", form.errors)

    def test_categoria_em_uso_nao_pode_ser_excluida(self):
        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_livro_sem_estoque_nao_aparece_em_novo_emprestimo(self):
        self.livro.quantidade_disponivel = 0
        self.livro.save(update_fields=["quantidade_disponivel"])

        form = EmprestimoForm()

        self.assertNotIn(self.livro, form.fields["livro"].queryset)


class LivroConstraintTests(TestCase):
    def test_banco_rejeita_disponivel_acima_do_total(self):
        categoria = Categoria.objects.create(nome="Teste")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Livro.objects.create(
                    isbn="9780306406157",
                    titulo="Inconsistente",
                    autor="Autora",
                    editora="Editora",
                    categoria=categoria,
                    cdd="800",
                    local_estante="A",
                    etiqueta="INC-1",
                    quantidade_total=1,
                    quantidade_disponivel=2,
                )
