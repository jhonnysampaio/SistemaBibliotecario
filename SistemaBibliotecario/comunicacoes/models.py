from django.db import models


class Mensagem(models.Model):
    class Tipo(models.TextChoices):
        ATRASO = "ATRASO", "Empréstimo atrasado"
        RESERVA = "RESERVA", "Reserva disponível"
        PENDENCIA_ANUAL = "PENDENCIA_ANUAL", "Pendência anual"

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        ENVIADA = "ENVIADA", "Enviada"
        FALHA = "FALHA", "Falha"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDENTE,
        db_index=True,
    )
    chave = models.CharField(max_length=160, unique=True)
    destinatario = models.EmailField()
    assunto = models.CharField(max_length=160)
    corpo = models.TextField()
    aluno = models.ForeignKey(
        "alunos.Aluno",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensagens",
    )
    emprestimo = models.ForeignKey(
        "emprestimos.Emprestimo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mensagens",
    )
    tentativas = models.PositiveSmallIntegerField(default=0)
    ultima_tentativa_em = models.DateTimeField(null=True, blank=True)
    enviada_em = models.DateTimeField(null=True, blank=True)
    erro = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("criada_em",)

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.destinatario}"
