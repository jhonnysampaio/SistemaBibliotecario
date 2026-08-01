from django.shortcuts import render, redirect
from django.http import HttpResponse
from usuarios.models import Usuario
from livros.models import Livros

# Create your views here.

def dashboard(request):
    if request.session.get("usuario"):
        usuario = Usuario.objects.get(id = request.session["usuario"]).nome
        livros = Livros.objects.all()
        return render(request, "dashboard.html", {"livros" : livros})

    else:
        return redirect("/auth/login/")