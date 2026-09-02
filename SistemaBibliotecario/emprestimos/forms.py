from django import forms
from django.utils import timezone

from alunos.models import Aluno
from livros.models import Livro
from .models import Emprestimo


class EmprestimoForm(forms.ModelForm):

    class Meta:
        model = Emprestimo

        fields = [
            "aluno",
            "livro",
            "data_prevista",
            "observacoes",
        ]

        widgets = {
            "aluno": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "livro": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "data_prevista": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),

            "observacoes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Observações sobre o empréstimo...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["aluno"].queryset = (
            Aluno.objects
            .filter(ativo=True)
            .order_by("nome")
        )

        self.fields["livro"].queryset = (
            Livro.objects
            .filter(
                ativo=True,
                quantidade_disponivel__gt=0,
            )
            .select_related("categoria")
            .order_by("titulo")
        )

        self.fields["aluno"].empty_label = "Selecione um aluno"
        self.fields["livro"].empty_label = "Selecione um livro"

    def clean_data_prevista(self):
        data = self.cleaned_data["data_prevista"]

        if data < timezone.localdate():
            raise forms.ValidationError(
                "A devolução não pode estar no passado."
            )

        return data