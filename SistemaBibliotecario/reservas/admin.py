from django.contrib import admin

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "aluno",
        "livro",
        "status",
        "criada_em",
        "disponivel_ate",
    )
    list_filter = ("status", "criada_em")
    search_fields = (
        "aluno__nome",
        "aluno__matricula",
        "livro__titulo",
    )
    readonly_fields = (
        "criada_em",
        "atualizada_em",
        "disponibilizada_em",
        "notificada_em",
    )
