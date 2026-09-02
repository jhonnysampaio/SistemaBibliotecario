from django.core.management.base import BaseCommand

from comunicacoes.envio import enviar_mensagem, reivindicar_mensagem


class Command(BaseCommand):
    help = "Envia mensagens reivindicadas da caixa de saída."

    def add_arguments(self, parser):
        parser.add_argument("--limite", type=int, default=50)

    def handle(self, *args, **options):
        for _ in range(options["limite"]):
            mensagem = reivindicar_mensagem()
            if mensagem is None:
                break

            enviar_mensagem(mensagem)
