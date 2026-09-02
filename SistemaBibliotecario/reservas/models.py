from django.db import models


class Reserva(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO = "AGUARDANDO", "Aguardando"
        DISPONIVEL = "DISPONIVEL", "Disponível"
        ATENDIDA = "ATENDIDA", "Atendida"
        CANCELADA = "CANCELADA", "Cancelada"
        EXPIRADA = "EXPIRADA", "Expirada"

    aluno = models.ForeignKey(
        "alunos.Aluno", on_delete=models.PROTECT, related_name="reservas"
    )
    livro = models.ForeignKey(
        "livros.Livro", on_delete=models.PROTECT, related_name="reservas"
    )
    status = models.CharField(
        max_length=12, choices=Status.choices,
        default=Status.AGUARDANDO, db_index=True
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    disponibilizada_em = models.DateTimeField(null=True, blank=True)
    notificada_em = models.DateTimeField(null=True, blank=True)
    disponivel_ate = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("criada_em", "pk")
        constraints = [
            models.UniqueConstraint(
                fields=("aluno", "livro"),
                condition=models.Q(
                    status__in=("AGUARDANDO", "DISPONIVEL")
                ),
                name="reserva_ativa_unica_aluno_livro",
            )
        ]

    def __str__(self):
        return f"{self.aluno} - {self.livro} ({self.get_status_display()})"
