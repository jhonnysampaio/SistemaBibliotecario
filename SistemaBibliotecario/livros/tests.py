from django.test import TestCase
from .forms import LivroForm
from .models import Categoria, Livro

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
