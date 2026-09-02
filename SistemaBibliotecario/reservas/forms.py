from django import forms

from alunos.models import Aluno
from livros.models import Livro

from .models import Reserva


class ReservaForm(forms.ModelForm):

    class Meta:
        model = Reserva

        fields = (
            "aluno",
            "livro",
        )

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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lista apenas alunos ativos
        self.fields["aluno"].queryset = (
            Aluno.objects
            .filter(ativo=True)
            .order_by("nome")
        )

        # Lista apenas livros ativos
        self.fields["livro"].queryset = (
            Livro.objects
            .filter(ativo=True)
            .select_related("categoria")
            .order_by("titulo")
        )

        # Textos iniciais dos campos
        self.fields["aluno"].empty_label = "Selecione um aluno"
        self.fields["livro"].empty_label = "Selecione um livro"