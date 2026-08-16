from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from alunos.models import Aluno
from livros.models import Livro
from datetime import date

# Create your models here.

class Emprestimo(models.Model):
    class Situacao(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        ATRASADO = "ATRASADO", "Atrasado"
        DEVOLVIDO = "DEVOLVIDO", "Devolvido"

    aluno = models.ForeignKey(
        Aluno,
        on_delete = models.PROTECT,
        related_name="emprestimos",
        )
    livro = models.ForeignKey(
        Livro,
        on_delete = models.PROTECT,
        related_name="emprestimos"
        )
    data_inicio = models.DateField(default=timezone.localdate)
    data_prevista = models.DateField("devolução prevista")
    data_devolucao = models.DateField(
        "devolução realizada",
        null=True,
        blank=True,
    )
    situacao = models.CharField(
        "situação",
        max_length=10,
        choices=Situacao.choices,
        default=Situacao.ATIVO,
        db_index=True
    )
    renovacoes = models.PositiveSmallIntegerField(default=0)
    observacoes = models.TextField("observações", blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emprestimos_registrados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-criado_em",)
        constraints = [
            models.CheckConstraint(
                condition=Q(data_prevista__gte=F("data_inicio")),
                name="emprestimo_previsao_gte_inicio",
            ),
            models.CheckConstraint(
                condition=Q(data_devolucao__isnull=True)
                | Q(data_devolucao__gte=F("data_inicio")),
                name="emprestimo_devolucao_gte_inicio",
            ),
        ]
        permissions = [
            ("pode_devolver_emprestimo", "Pode registrar devolução"),
            ("pode_renovar_emprestimo", "Pode renovar empréstimo"),
        ]

    @property
    def esta_atrasado(self):
        return(
            self.situacao != self.Situacao.DEVOLVIDO
            and self.data_prevista < timezone.localdate()
        )

    def __str__(self):
        return f"{self.aluno} - {self.livro}"
