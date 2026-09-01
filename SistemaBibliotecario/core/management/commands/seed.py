from django.core.management.base import BaseCommand
from alunos.models import Aluno
from livros.models import Livro, Categoria

class Command(BaseCommand):
    help = "Cria dados de demonstração sem apagar dados existentes."

    def handle(self, *args, **options):
        literatura, _ = Categoria.objects.get_or_create(
            nome="Literatura",
            defaults={"descricao": "Romances, contos e poesia."},
        )
        ciencias, _ = Categoria.objects.get_or_create(
            nome="Ciências",
            defaults={"descricao": "Ciências da natureza e divulgação."},
        )

        livros = [
            {
                "isbn": "9780306406157",
                "titulo": "Cosmos da Escola",
                "autor": "Carla Mendes",
                "editora": "Horizonte",
                "categoria": ciencias,
                "cdd": "500",
                "local_estante": "C-01",
                "etiqueta": "CIE-001",
                "quantidade_total": 4,
                "quantidade_disponivel": 4,
            },
            {
                "isbn": "9783161484100",
                "titulo": "Histórias do Pátio",
                "autor": "Rafael Lima",
                "editora": "Ipê",
                "categoria": literatura,
                "cdd": "869",
                "local_estante": "L-03",
                "etiqueta": "LIT-001",
                "quantidade_total": 3,
                "quantidade_disponivel": 3,
            },
        ]
        for dados in livros:
            isbn = dados.pop("isbn")
            Livro.objects.get_or_create(isbn=isbn, defaults=dados)

        alunos =[
            {
                "matricula": "2026001",
                "nome": "Marina Alves",
                "serie": "1º ano",
                "turma": "A",
                "turno": "M",
                "cpf": "52998224725",
            },
            {
                "matricula": "2026002",
                "nome": "Pedro Santos",
                "serie": "2º ano",
                "turma": "B",
                "turno": "V",
                "cpf": "11144477735",

            },
        ]
        for dados in alunos:
            matricula = dados.pop("matricula")
            Aluno.objects.get_or_create(
                matricula=matricula,
                defaults=dados,
            )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
