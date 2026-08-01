from django import forms
from .models import Alunos

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Alunos

        fields = [
            "matricula",
            "nome",
            "serie",
            "turma",
            "turno",
            "cpf",
            "telefone"
        ]

        widgets = {
            "matricula" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "nome" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "serie" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "turma" : forms.TextInput(attrs={
                "class" : "form-control"
            }),
            "turno" : forms.Select(attrs={
                "class" : "form-selct"
            }),
            "cpf" : forms.TextInput(attrs={
                "class" : "form-control",
                "placeholder" : "000.000.000-00"
            }),
            "telefone" : forms.TextInput(attrs={
                "class" : "form-control",
                "placeholder" : "(00) 00000-0000"
            })

        }