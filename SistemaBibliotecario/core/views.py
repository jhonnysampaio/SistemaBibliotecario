from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def pesquisa(request):
    return render(
        request,
        "core/pesquisa.html",
        {"q": request.GET.get("q", "").strip()},
    )
