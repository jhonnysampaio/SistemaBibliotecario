from django.contrib import admin
from .models import Emprestimo

# Register your models here.

@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "aluno",
        "livro",
        "data_inicio",
        "data_prevista",
        "situacao"
    )
    list_filter = ("situacao", "data_inicio", "data_prevista")
    search_fields = (
        "aluno__nome",
        "aluno__matricula",
        "livro__titulo",
    )
    autocomplete_fields = ("aluno", "livro")
    readonly_fields = (
        "situacao",
        "data_devolucao",
        "renovacoes",
        "criado_em",
        "atualizado_em",
    )

    