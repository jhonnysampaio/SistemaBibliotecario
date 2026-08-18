from django.contrib import admin
from .models import Livro, Categoria

# Register your models here.

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa")
    search_fields = ("nome",)

@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "autor",
        "categoria",
        "quantidade_total",
        "quantidade_disponivel",
        "ativo",
    )
    list_filter = ("categoria", "ativo")
    search_fields = ("titulo", "autor", "isbn", "etiqueta")
    readonly_fields = ("quantidade_disponivel",)