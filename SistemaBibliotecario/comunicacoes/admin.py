from django.contrib import admin

from .models import Mensagem


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = (
        "tipo",
        "destinatario",
        "aluno",
        "emprestimo",
        "reserva",
        "status",
        "tentativas",
        "enviada_em",
        "atualizada_em",
    )
    list_filter = ("tipo", "status")
    search_fields = (
        "destinatario",
        "assunto",
        "aluno__nome",
    )
    readonly_fields = (
        "chave",
        "corpo_html",
        "status",
        "tentativas",
        "ultima_tentativa_em",
        "enviada_em",
        "erro",
        "criada_em",
        "atualizada_em",
    )

    def get_readonly_fields(self, request, obj=None):
        campos = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == Mensagem.Status.ENVIADA:
            campos.extend(("destinatario", "corpo"))
        return tuple(campos)
