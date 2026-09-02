from django.db import migrations, models


def normalizar_serie(apps, schema_editor):
    Aluno = apps.get_model("alunos", "Aluno")
    HistoricoProgressao = apps.get_model(
        "alunos",
        "HistoricoProgressao",
    )
    equivalencias = {
        "1°": "1º ano",
        "1º": "1º ano",
        "1ª": "1º ano",
        "1ª série": "1º ano",
        "2°": "2º ano",
        "2º": "2º ano",
        "2ª": "2º ano",
        "2ª série": "2º ano",
        "3°": "3º ano",
        "3º": "3º ano",
        "3ª": "3º ano",
        "3ª série": "3º ano",
    }

    for anterior, nova in equivalencias.items():
        Aluno.objects.filter(serie=anterior).update(serie=nova)
        HistoricoProgressao.objects.filter(
            serie_anterior=anterior
        ).update(serie_anterior=nova)
        HistoricoProgressao.objects.filter(
            serie_nova=anterior
        ).update(serie_nova=nova)


class Migration(migrations.Migration):

    dependencies = [
        ("alunos", "0004_adiciona_ano_letivo_e_historico"),
    ]

    operations = [
        migrations.RunPython(
            normalizar_serie,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="aluno",
            name="serie",
            field=models.CharField(
                choices=[
                    ("1º ano", "1ª série"),
                    ("2º ano", "2ª série"),
                    ("3º ano", "3ª série"),
                ],
                max_length=20,
                verbose_name="série",
            ),
        ),
        migrations.AlterField(
            model_name="aluno",
            name="turma",
            field=models.CharField(
                choices=[
                    ("A", "A"),
                    ("B", "B"),
                    ("C", "C"),
                    ("Téc", "Téc"),
                ],
                max_length=20,
            ),
        ),
    ]
