from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from .forms import DadosUsuarioForm, PerfilForm, UsuarioForm
from .models import Perfil

# Create your views here.

User = get_user_model()

@login_required
def perfil(request):
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == "POST":
        dados_form = DadosUsuarioForm(request.POST, instance=request.user)
        telefone_form = PerfilForm(request.POST, instance=perfil_obj)
        telefone_form.fields.pop("cargo")

        if dados_form.is_valid() and telefone_form.is_valid():
            dados_form.save()
            telefone_form.save()
            messages.success(request, "Perfil atualizado.")
            return redirect("usuarios:perfil")
    else:
        dados_form = DadosUsuarioForm(instance=request.user)
        telefone_form = PerfilForm(instance=perfil_obj)
        telefone_form.fields.pop("cargo")
    return render(
        request,
        "usuarios/perfil.html",
        {"dados_form": dados_form, "perfil_form": telefone_form}
    )

@login_required
def alterar_senha(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Senha alterada com sucesso.")
        return redirect("usuarios:perfil")
    return render(request, "usuarios/alterar_senha.html", {"form": form})

@permission_required("auth.view_user", raise_exception=True)
def lista(request):
    usuarios = User.objects.select_related("perfil").order_by("first_name", "username")
    return render(request, "usuarios/lista.html", {"usuarios": usuarios})

@permission_required("auth.add_user", raise_exception=True)
def criar(request):
    form = UsuarioForm(request.POST or None)
    perfil_form = PerfilForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and perfil_form.is_valid():
        user = form.save()
        perfil = user.perfil
        perfil.cargo = perfil_form.cleaned_data["cargo"]
        perfil.telefone = perfil_form.cleaned_data["telefone"]
        perfil.save()
        grupo_por_cargo = {
            Perfil.Cargo.BIBLIOTECARIO: "Bibliotecários",
            Perfil.Cargo.AUXILIAR: "Auxiliares",
            Perfil.Cargo.DIRECAO: "Direção",
        }
        grupo = Group.objects.filter(
            name=grupo_por_cargo[perfil.cargo]
        ).first()
        if grupo:
            user.groups.add(grupo)
        messages.success(request, "Usuario Criado com sucesso.")
        return redirect("usuarios:lista")
    return render(
        request,
        "usuarios/form.html",
        {"form": form, "perfil_form": perfil_form}
    )

@permission_required("auth.change_user", raise_exception=True)
def alternar_ativo(request, pk):
    if request.method != "POST":
        return redirect("usuarios:lista")
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "Você não pode desativar a própria conta.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        messages.success(request, "Situação do usuário atualizada.")
    return redirect("usuarios:lista")