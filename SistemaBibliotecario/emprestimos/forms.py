from django import forms
from .models import Emprestimo

class EmprestimoForm(forms.ModelForm):
    class Meta:
        model = Emprestimo

        fields = [
            "aluno",
            "livro",
            "data_inicio",
            "data_termino"
        ]

        widgets = {
            "aluno" : forms.Select(attrs={
                "class" : "form-select"
            }),
            "livro" : forms.Select(attrs={
                "class" : "form-select"
            }),
            "data_inicio" : forms.DateInput(attrs={
                "class" : "form-control",
                "type" : "date"
            }),
            "data_termino" : forms.DateInput(attrs={
                "class" : "form-control",
                "type" : "date"
            })
        }