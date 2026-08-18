from django.db import models
from datetime import date
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from .validators import validar_isbn

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=60, unique=True)
    descricao = models.TextField("descrição", blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ("nome",)

    def __str__(self):
        return self.nome

class Livro(models.Model):
    isbn = models.CharField(
        "ISBN",
        max_length=17,
        unique=True,
        validators=[validar_isbn],
        )
    titulo = models.CharField("título" ,max_length=150, db_index=True)
    subtitulo = models.CharField("subtítulo", max_length=150, blank = True)
    autor = models.CharField(max_length=120, db_index=True)
    ano_publicacao = models.PositiveSmallIntegerField(
        "ano de publicação",
        null=True,
        blank=True,
    )
    data_cadastro = models.DateField(default = date.today)
    editora = models.CharField(max_length=100)
    categoria = models.ForeignKey(
        Categoria, on_delete = models.PROTECT,
        related_name="livros",
        )
    cdd = models.CharField("CDD" ,max_length=10)
    local_estante = models.CharField("local na estante" ,max_length=100)
    etiqueta = models.CharField(max_length=50, unique=True)
    quantidade_total = models.PositiveIntegerField(default=1)
    quantidade_disponivel = models.PositiveIntegerField(default=1)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ("titulo",)
        verbose_name = "livro"
        verbose_name_plural = "livros"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade_total__gte=1),
                name="livro_quantidade_total_gte_1"
            ),
            models.CheckConstraint(
                condition=Q(quantidade_disponivel__gte=0),
                name = "livro_disponivel_gte_0"
            ),
            models.CheckConstraint(
                condition=Q(quantidade_disponivel__lte=F("quantidade_total")),
                name="livro_disponivel_lte_total",
            ),
        ]
    def clean(self):
        super().clean()
        if self.quantidade_disponivel > self.quantidade_total:
            raise ValidationError(
                {"quantidade_disponivel": "Disponíveis não pode superar o total."}
            )
    
    def __str__(self):
        return f"{self.titulo} - {self.autor}"

