from django import forms

from .models import Aluno
from .validators import somente_digitos


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno

        fields = [
            "matricula",
            "nome",
            "serie",
            "turma",
            "turno",
            "cpf",
            "telefone",
            "email",
            "ativo",
        ]

        widgets = {
            "cpf": forms.TextInput(attrs={"placeholder": "000.000.000-00"}),
            "telefone": forms.TextInput(
                attrs={"placeholder": "(00) 00000-0000"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"

    def clean_matricula(self):
        return self.cleaned_data["matricula"].strip().upper()

    def clean_cpf(self):
        return somente_digitos(self.cleaned_data["cpf"])
