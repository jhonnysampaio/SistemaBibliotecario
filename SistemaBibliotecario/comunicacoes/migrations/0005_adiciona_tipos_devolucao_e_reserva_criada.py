from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunicacoes", "0004_mensagem_corpo_html"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mensagem",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("CADASTRO", "Cadastro de aluno"),
                    ("EMPRESTIMO", "Empréstimo realizado"),
                    ("DEVOLUCAO", "Devolução realizada"),
                    ("PRAZO", "Empréstimo perto do prazo"),
                    ("ATRASO", "Empréstimo atrasado"),
                    ("RESERVA_CRIADA", "Reserva realizada"),
                    ("RESERVA", "Reserva disponível"),
                    ("PENDENCIA_ANUAL", "Pendência anual"),
                ],
                max_length=20,
            ),
        ),
    ]
