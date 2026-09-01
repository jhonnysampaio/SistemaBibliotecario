from django.db import models
from .validators import somente_digitos, validar_cpf
from django.conf import settings
from django.utils import timezone

# Create your models here.

def ano_letivo_atual():
    return timezone.localdate().year


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

    ano_letivo = models.PositiveSmallIntegerField(default=ano_letivo_atual)

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

    
    
class HistoricoProgressao(models.Model):
    aluno = models.ForeignKey(
        Aluno, on_delete=models.PROTECT, related_name="progressoes"
    )

    ano_origem = models.PositiveSmallIntegerField()
    ano_destino = models.PositiveSmallIntegerField()
    serie_anterior = models.CharField(max_length=20)
    serie_nova = models.CharField(max_length=20, blank=True)
    concluido = models.BooleanField(default=False)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-criado_em",)
        constraints = [
            models.UniqueConstraint(
                fields=("aluno", "ano_destino"),
                name="historico_progressao_unica_por_ano"
            )
        ]