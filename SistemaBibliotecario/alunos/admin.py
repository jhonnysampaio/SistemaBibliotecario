from django.contrib import admin

from comunicacoes.services import enfileirar_cadastro_aluno

from .models import Aluno

# Register your models here.
 
@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = (
        "matricula",
        "nome",
        "serie",
        "turma",
        "turno",
        "ativo",
    )
    list_filter = ("serie", "turno", "ativo")
    search_fields = ("matricula", "nome", "cpf")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            enfileirar_cadastro_aluno(aluno=obj)
