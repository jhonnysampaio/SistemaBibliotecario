from django.db import models
from alunos.models import Alunos
from livros.models import Livros

# Create your models here.

class Emprestimo(models.Model):
    aluno = models.ForeignKey(Alunos, on_delete = models.DO_NOTHING)
    livro = models.ForeignKey(Livros, on_delete = models.DO_NOTHING)


