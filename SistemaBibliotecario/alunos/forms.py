from django import forms
from django.utils import timezone

from .models import Aluno
from .validators import somente_digitos


class AlunoForm(forms.ModelForm):
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={"placeholder": "000.000.000-00"}
        ),
    )

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


class FechamentoAnoLetivoForm(forms.Form):
    ano_destino = forms.IntegerField(
        label="Ano letivo de destino",
        min_value=2000,
        max_value=2100,
        initial=lambda: timezone.localdate().year + 1,
        widget=forms.NumberInput(
            attrs={"class": "form-control"}
        ),
    )
    confirmar = forms.BooleanField(
        label="Confirmo o fechamento do ano letivo",
        required=True,
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        ),
    )
