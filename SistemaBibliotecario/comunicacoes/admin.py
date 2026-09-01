from django.contrib import admin

from .models import Mensagem


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "destinatario",
        "status",
        "tentativas",
        "criada_em",
    )
    list_filter = ("tipo", "status")
    search_fields = (
        "destinatario",
        "assunto",
        "aluno__nome",
    )
    readonly_fields = (
        "chave",
        "tentativas",
        "ultima_tentativa_em",
        "enviada_em",
        "erro",
        "criada_em",
    )
