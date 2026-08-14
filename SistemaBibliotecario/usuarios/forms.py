from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil

User = get_user_model()

class UsuarioForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email" )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe um usuário com este email")
        return email

class DadosUsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ("cargo", "telefone")