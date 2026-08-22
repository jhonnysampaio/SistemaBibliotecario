from django.db import models
from django.conf import settings
from emprestimos.models import Emprestimo

# Create your models here.

class Notificacao(models.Model):
    class Tipo(models.TextChoices):
        PRAZO = "PRAZO", "Prazo proximo"
        ATRASO = "ATRASO", "Emprestimo atrasado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    emprestimo = models.ForeignKey(
        Emprestimo,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    titulo = models.CharField(max_length=120)
    mensagem = models.CharField(max_length=255)
    lida = models.BooleanField(default=False, db_index=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-criada_em",)
        constraints = [
            models.UniqueConstraint(
                fields=("usuario", "emprestimo", "tipo"),
                name="notificacao_unica_usuario_emprestimo_tipo",
            )
        ]
    def __str__(self):
        return self.titulo
    