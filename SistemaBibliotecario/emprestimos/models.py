from django.db import models
from alunos.models import Alunos
from livros.models import Livros
from datetime import date

# Create your models here.

class Emprestimo(models.Model):
    aluno = models.ForeignKey(Alunos, on_delete = models.DO_NOTHING)
    livro = models.ForeignKey(Livros, on_delete = models.DO_NOTHING)
    data_inicio = models.DateField(default=date.today)
    data_termino = models.DateField()

