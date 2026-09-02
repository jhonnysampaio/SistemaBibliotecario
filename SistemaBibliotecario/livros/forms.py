from django import forms

from .models import Categoria, Livro
from .services import preparar_livro_com_estoque, salvar_livro_com_estoque
from .validators import normalizar_isbn


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria

        fields = (
            "nome",
            "descricao",
            "ativa",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(
                field.widget,
                forms.CheckboxInput
            ):

                field.widget.attrs[
                    "class"
                ] = "form-check-input"

            else:

                field.widget.attrs[
                    "class"
                ] = "form-control"


class LivroForm(forms.ModelForm):

    class Meta:
        model = Livro

        fields = (
            "isbn",
            "titulo",
            "subtitulo",
            "autor",
            "ano_publicacao",
            "editora",
            "categoria",
            "cdd",
            "local_estante",
            "etiqueta",
            "quantidade_total",
            "ativo",
        )

        widgets = {

            "ano_publicacao":
                forms.NumberInput(
                    attrs={
                        "min": 1000,
                    }
                ),

            "quantidade_total":
                forms.NumberInput(
                    attrs={
                        "min": 1,
                    }
                ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        self.fields[
            "categoria"
        ].queryset = (

            Categoria.objects
            .filter(ativa=True)
            .order_by("nome")

        )

        self.fields[
            "categoria"
        ].empty_label = (
            "Selecione uma categoria"
        )


        for field in self.fields.values():

            if isinstance(
                field.widget,
                forms.CheckboxInput
            ):

                field.widget.attrs[
                    "class"
                ] = "form-check-input"

            elif isinstance(
                field.widget,
                forms.Select
            ):

                field.widget.attrs[
                    "class"
                ] = "form-select"

            else:

                field.widget.attrs[
                    "class"
                ] = "form-control"


        self.fields[
            "categoria"
        ].widget.attrs.update(
            {
                "id": "id_categoria",
            }
        )


    def clean_isbn(self):

        return normalizar_isbn(
            self.cleaned_data[
                "isbn"
            ]
        )


    def clean_quantidade_total(self):

        novo_total = (
            self.cleaned_data[
                "quantidade_total"
            ]
        )

        if self.instance.pk:

            original = (
                Livro.objects.get(
                    pk=self.instance.pk
                )
            )

            emprestados = (
                original.quantidade_total
                - original.quantidade_disponivel
            )

            if (
                novo_total
                < emprestados
            ):

                raise forms.ValidationError(
                    f"Há {emprestados} exemplar(es) "
                    "emprestado(s). O total não pode "
                    "ficar abaixo desse número."
                )

        return novo_total


    def save(
        self,
        commit=True
    ):

        livro = super().save(
            commit=False
        )

        if commit:

            salvar_livro_com_estoque(
                livro=livro
            )

            self.save_m2m()

        else:

            preparar_livro_com_estoque(
                livro=livro
            )

        return livro