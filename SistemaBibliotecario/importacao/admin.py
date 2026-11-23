from django.contrib import admin
from .models import ImportacaoPlanilha

# Register your models here.

@admin.register(ImportacaoPlanilha)
class ImportacaoPlanilhaAdmin(admin.ModelAdmin):
    list_display = ("nome_arquivo", "tipo", "status", "usuario", "criado_em")
    list_filter = ("tipo", "status")
    exclude = ("linhas",)               # nao expor dados pessoais
    readonly_fields = ("usuario", "tipo", "status", "nome_arquivo", "total_linhas",
                       "total_validas", "total_invalidas", "total_importadas",
                       "criado_em", "expira_em", "concluido_em")

    def has_add_permission(self, request):
        return False