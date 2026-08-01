from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import AlunoForm 
from .models import Alunos

# Create your views here.

def listar_aluno(request):
    alunos = Alunos.objects.all()

    return render(request, "listar_aluno.html", {"alunos" : alunos})

def cadastrar_aluno(request):
    if request.method == "POST":
        form = AlunoForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("listar_aluno")

    else:
         form = AlunoForm()
         print(form.errors)

    return render(request, "cadastrar_aluno.html",{"form" : form})

def editar_aluno(request, aluno_id):
    aluno = get_object_or_404(Alunos, id=aluno_id)

    if request.method == "POST":
        form = AlunoForm(request.POST, instance=aluno)

        if form.is_valid():
            form.save()

            return redirect("listar_aluno")

    else:
        form = AlunoForm(instance=aluno)

    return render(request, "editar_aluno.html", {
        "form" : form,
        "aluno" : aluno
    })

def excluir_aluno(request, aluno_id):
    aluno = get_object_or_404(Alunos, id=aluno_id)
    aluno.delete()

    return redirect("listar_aluno")