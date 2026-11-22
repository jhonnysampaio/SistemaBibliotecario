from django.db import models
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

# Create your models here.
def expiracao_padrao():
    return timezone.now() + timedelta(hours=2)

class ImportacaoPlanilha(models.Model):
    class Tipo(models.TextChoices):
        ALUNOS = "alunos", "Alunos"
        LIVROS = "livros", "Livros"

    class Status(models.TextChoices):
        VALIDADA = "validada", "Validada"
        CONCLUIDA = "concluida", "Concluida"
        FALHOU = "falhou", "Falhou"
        EXPIRADA = "expirada", "Expirada"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="importacoes",
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.VALIDADA)
    nome_arquivo = models.CharField(max_length=120)

    # Linhas normalizadas e validadas. Apagadas ao concluir(dados pessoais).
    linhas = models.JSONField(default=list)
    total_linhas = models.PositiveIntegerField(default=0)
    total_validas = models.PositiveIntegerField(default=0)
    total_invalidas = models.PositiveIntegerField(default=0)
    total_importadas = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField(default=expiracao_padrao)
    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "importação de planilha"
        verbose_name_plural = "importações de planilhas"

    @property
    def expirada(self):
        return timezone.now() >= self.expira_em

    def __str__(self):
        return "%s - %s (%s)" % (self.get_tipo_display(), self.nome_arquivo,
                                 self.get_status_display())