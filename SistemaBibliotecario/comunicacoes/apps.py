from django.apps import AppConfig


class ComunicacoesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "comunicacoes"
    verbose_name = "Comunicações"

    def ready(self):
        from .agendador import iniciar_agendador

        iniciar_agendador()
