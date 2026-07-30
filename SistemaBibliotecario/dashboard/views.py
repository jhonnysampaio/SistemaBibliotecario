from django.shortcuts import render, redirect
from django.http import HttpResponse
from usuarios.models import Usuario

# Create your views here.

def dashboard(request):
    if request.session.get("usuario"):
        usuario = Usuario.objects.get(id = request.session["usuario"]).nome
        return HttpResponse(f"dashboard, {usuario}")

    else:
        return redirect("/auth/login/")