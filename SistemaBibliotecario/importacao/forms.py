from django import forms

class ArquivoPlanilhaForm(forms.Form):
    arquivo = forms.FileField(
        label="Planilha (.xlsx ou .csv)",
        widget=forms.FileInput(attrs={"class": "form-control", "accept": ".xlsx, .csv"})
    )