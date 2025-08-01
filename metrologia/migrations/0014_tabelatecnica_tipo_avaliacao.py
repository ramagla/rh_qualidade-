# Generated by Django 5.1.2 on 2024-12-16 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "metrologia",
            "0013_calibracao_certificado_anexo_tabelatecnica_faixa_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="tabelatecnica",
            name="tipo_avaliacao",
            field=models.CharField(
                choices=[("deslocamento", "Deslocamento"), ("carga", "Carga")],
                default="deslocamento",
                max_length=20,
                verbose_name="Tipo de Avaliação",
            ),
        ),
    ]
