from django import forms
from .models import Livro

class LivroForm(forms.ModelForm):
    class Meta:
        model = Livro
        fields = [
                 "isbn", "titulo", "subtitulo", "autor", "data_cadastro",
                 "editora", "categoria", "cdd", "local_estante",
                 "etiqueta", "quantidade_total", "quantidade_disponivel"
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
                "class" : "form-select"
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
            "quantidade_total" : forms.NumberInput(attrs={
                "class" : "form-control"
            }),
            "quantidade_disponivel" : forms.NumberInput(attrs={
                "class" : "form-control"
            })
        }
