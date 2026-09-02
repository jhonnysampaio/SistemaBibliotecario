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
