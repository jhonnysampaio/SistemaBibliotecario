from django.db import models

# Create your models here.

class Alunos(models.Model):
    """
    nome
    serie
    turma
    turno
    matrícula
    cpf
    número de telefone
    """

    matricula = models.CharField(max_length=12)
    nome = models.CharField(max_length=100)
    serie = models.CharField(max_length=10)
    turma = models.CharField(max_length=10)
    turno = models.CharField(max_length=10)
    cpf = models.CharField(max_length=11)
    telefone = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Aluno"

    def __str__(self):
        return self.nome
