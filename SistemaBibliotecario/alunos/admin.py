from django.contrib import admin
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
        "cpf",
        "telefone",
        "email",
        "ativo",
        "criado_em",
        "atualizado_em"
    )
    list_filter = ("serie", "turno", "ativo")
    search_fields = ("matricula", "nome", "cpf")
