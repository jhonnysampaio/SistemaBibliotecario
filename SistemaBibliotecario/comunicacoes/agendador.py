import logging
import os
import sys
from threading import Event, Lock, Thread

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone


logger = logging.getLogger("django.server")
_acordar = Event()
_trava_inicio = Lock()
_iniciado = False


def _processo_principal_do_runserver(argv=None, ambiente=None):
    argv = argv if argv is not None else sys.argv
    ambiente = ambiente if ambiente is not None else os.environ
    if len(argv) < 2 or argv[1] != "runserver":
        return False
    if "--noreload" in argv:
        return True
    return ambiente.get("RUN_MAIN") == "true"


def acordar_agendador():
    _acordar.set()


def _executar_agendador():
    from .rotinas import (
        executar_rotinas_do_servidor,
        proxima_execucao_temporal,
    )

    _acordar.wait(2)
    _acordar.clear()
    while True:
        close_old_connections()
        try:
            resultado = executar_rotinas_do_servidor()
            logger.info(
                "Rotinas automáticas de e-mail sincronizadas: %s",
                resultado,
            )
        except Exception:
            logger.exception(
                "Não foi possível executar as rotinas automáticas de e-mail."
            )
        finally:
            close_old_connections()

        try:
            proxima = proxima_execucao_temporal()
            espera = max(1, (proxima - timezone.now()).total_seconds())
        except Exception:
            logger.exception(
                "Não foi possível calcular a próxima rotina de e-mail."
            )
            espera = 300

        if _acordar.wait(espera):
            _acordar.clear()
            continue


def iniciar_agendador():
    global _iniciado

    if not settings.EMAIL_AUTOMACAO_NO_SERVIDOR:
        return False
    if not _processo_principal_do_runserver():
        return False

    with _trava_inicio:
        if _iniciado:
            return False
        _iniciado = True
        Thread(
            target=_executar_agendador,
            name="biblioteca-rotinas-email",
            daemon=True,
        ).start()
    return True
