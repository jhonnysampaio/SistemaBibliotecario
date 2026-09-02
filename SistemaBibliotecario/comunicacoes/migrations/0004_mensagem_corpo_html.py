from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunicacoes", "0003_alter_mensagem_tipo"),
    ]

    operations = [
        migrations.AddField(
            model_name="mensagem",
            name="corpo_html",
            field=models.TextField(blank=True),
        ),
    ]
