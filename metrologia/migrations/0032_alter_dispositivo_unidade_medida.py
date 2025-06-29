# Generated by Django 4.2.16 on 2025-06-06 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metrologia", "0031_alter_tabelatecnica_unidade_medida"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dispositivo",
            name="unidade_medida",
            field=models.CharField(
                choices=[
                    ("mm", "Milímetros"),
                    ("cm", "Centímetros"),
                    ("m", "Metros"),
                    ("kg", "Quilogramas"),
                    ("°C", "Graus Celsius"),
                    ("%", "Percentual"),
                    ("Ø", "Diâmetro"),
                    ("°", "Graus"),
                ],
                max_length=10,
                verbose_name="Unidade de Medida",
            ),
        ),
    ]
