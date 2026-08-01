from django import forms
from .models import Livros

class LivroForm(forms.ModelForm):
    class Meta:
        model = Livros
        fields = [
                 "isbn", "titulo", "subtitulo", "autor", "data_cadastro",
                 "editora", "categoria", "cdd", "local_estante",
                 "etiqueta", "quant_total", "exemp_disponiveis"
                 ]

        widgets = {
            "isbn" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "titulo" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "subtitulo" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "autor" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "data_cadastro" : forms.DateInput(attrs={
                "class" : "form-control",
                "type" : "date"
            }),
            "editora" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "categoria" : forms.Select(attrs={
                "class" : "form-control"
            }),
            "cdd" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "local_estante" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "etiqueta" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "quant_total" : forms.NumberInput(attrs={
                "class" : "form-control"
            }),
            "exemp_disponiveis" : forms.NumberInput(attrs={
                "class" : "form-control"
            })
        }