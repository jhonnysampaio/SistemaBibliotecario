from django.db import models


class Mensagem(models.Model):
    class Tipo(models.TextChoices):
        CADASTRO = "CADASTRO", "Cadastro de aluno"
        EMPRESTIMO = "EMPRESTIMO", "Empréstimo realizado"
        DEVOLUCAO = "DEVOLUCAO", "Devolução realizada"
        PRAZO = "PRAZO", "Empréstimo perto do prazo"
        ATRASO = "ATRASO", "Empréstimo atrasado"
        RESERVA_CRIADA = "RESERVA_CRIADA", "Reserva realizada"
        RESERVA = "RESERVA", "Reserva disponível"
        PENDENCIA_ANUAL = "PENDENCIA_ANUAL", "Pendência anual"

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PROCESSANDO = "PROCESSANDO", "Processando"
        ENVIADA = "ENVIADA", "Enviada"
        FALHA = "FALHA", "Falha"

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDENTE,
        db_index=True,
    )
    chave = models.CharField(max_length=160, unique=True)
    destinatario = models.EmailField()
    assunto = models.CharField(max_length=160)
    corpo = models.TextField()
    corpo_html = models.TextField(blank=True)
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
    reserva = models.ForeignKey(
        "reservas.Reserva",
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
    atualizada_em = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ("criada_em",)

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.destinatario}"
