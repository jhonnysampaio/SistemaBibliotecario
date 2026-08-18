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
            "data_prevista": forms.DateInput(attrs={"type" : "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["aluno"].queryset = Aluno.objects.filter(ativo=True)
        self.fields["livro"].queryset = Livro.objects.filter(
            ativo=True,
            quantidade_disponivel__gt=0,
        ).select_related("categoria")
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )

    def clean_data_prevista(self):
        data = self.cleaned_data["data_prevista"]
        if data < timezone.localdate():
            raise forms.ValidationError(
                "A devolução não pode estar no passado."
            )
        return data
