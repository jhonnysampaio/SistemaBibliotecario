from django.db import models
from .validators import somente_digitos, validar_cpf

# Create your models here.

class Aluno(models.Model):
    class Turno(models.TextChoices):
        MATUTINO = "M", "Matutino"
        VESPERTINO = "V", "Vespertino"

    matricula = models.CharField("matrícula" ,max_length=20, unique=True)
    nome = models.CharField(max_length=120, db_index=True)
    serie = models.CharField("série", max_length=20)
    turma = models.CharField(max_length=20)
    turno = models.CharField(max_length=1, choices=Turno.choices)
    cpf = models.CharField(
        "CPF",
        max_length=11,
        unique=True,
        validators=[validar_cpf]
    )
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "aluno"
        verbose_name_plural = "alunos"

    def save(self, *args, **kwargs):
        self.matricula = self.matricula.strip()
        self.cpf = somente_digitos(self.cpf)
        self.nome = " ".join(self.nome.split())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.matricula}"
