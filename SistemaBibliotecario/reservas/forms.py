from django import forms

from alunos.models import Aluno
from livros.models import Livro

from .models import Reserva


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ("aluno", "livro")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aluno"].queryset = Aluno.objects.filter(ativo=True)
        self.fields["livro"].queryset = Livro.objects.filter(
            ativo=True
        ).select_related("categoria")
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select"
        self.fields["aluno"].widget.attrs.update(
            {
                "data-searchable-select": "true",
                "data-search-placeholder": (
                    "Pesquisar aluno por nome ou matrícula"
                ),
                "data-search-empty": "Nenhum aluno encontrado.",
            }
        )
        self.fields["livro"].widget.attrs.update(
            {
                "data-searchable-select": "true",
                "data-search-placeholder": (
                    "Pesquisar livro por título ou autor"
                ),
                "data-search-empty": "Nenhum livro encontrado.",
            }
        )
