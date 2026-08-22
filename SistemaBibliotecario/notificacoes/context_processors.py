def notificacoes_nao_lidas(request):
    if not request.user.is_authenticated:
        return {"total_notificacoes_nao_lidas": 0}
    return {
        "total_notificacoes_nao_lidas": request.user.notificacoes.filter(
            lida=False
        ).count()
    }