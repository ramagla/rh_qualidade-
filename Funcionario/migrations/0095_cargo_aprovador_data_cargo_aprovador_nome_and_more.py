# Generated by Django 5.1.2 on 2024-12-13 18:23

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0094_cargo_educacao_minima_cargo_experiencia_minima_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cargo",
            name="aprovador_data",
            field=models.DateField(
                default=django.utils.timezone.now, verbose_name="Data de Aprovação"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="aprovador_nome",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Nome do Aprovador"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="elaborador_data",
            field=models.DateField(
                default=django.utils.timezone.now, verbose_name="Data de Elaboração"
            ),
        ),
        migrations.AddField(
            model_name="cargo",
            name="elaborador_nome",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Nome do Elaborador"
            ),
        ),
    ]
