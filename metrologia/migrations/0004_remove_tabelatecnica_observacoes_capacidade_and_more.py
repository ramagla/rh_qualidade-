# Generated by Django 5.1.2 on 2024-12-10 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metrologia", "0003_tabelatecnica_exatidao_requerida"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tabelatecnica",
            name="observacoes_capacidade",
        ),
        migrations.AddField(
            model_name="tabelatecnica",
            name="tolerancia_em_percentual",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="Tolerância em (%)"
            ),
        ),
        migrations.AlterField(
            model_name="tabelatecnica",
            name="unidade_medida",
            field=models.CharField(
                choices=[
                    ("mm", "Milímetros"),
                    ("kg.cm", "Kilograma-centímetro"),
                    ("kgf", "Kilograma-força"),
                    ("°C", "Graus Celsius"),
                    ("°", "Graus"),
                    ("UR", "Unidade Relativa"),
                    ("HCR", "HCR"),
                    ("HRB", "HRB"),
                    ("%", "Percentual"),
                ],
                max_length=10,
                verbose_name="Unidade de Medida",
            ),
        ),
    ]
