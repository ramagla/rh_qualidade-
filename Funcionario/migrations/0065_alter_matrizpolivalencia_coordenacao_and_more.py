# Generated by Django 5.1.2 on 2024-11-27 13:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0064_remove_atividade_descricao"),
    ]

    operations = [
        migrations.AlterField(
            model_name="matrizpolivalencia",
            name="coordenacao",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="coordenacao_matriz",
                to="Funcionario.funcionario",
                verbose_name="Coordenação",
            ),
        ),
        migrations.AlterField(
            model_name="matrizpolivalencia",
            name="departamento",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="Departamento"
            ),
        ),
        migrations.AlterField(
            model_name="matrizpolivalencia",
            name="elaboracao",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="elaboracao_matriz",
                to="Funcionario.funcionario",
                verbose_name="Elaboração",
            ),
        ),
        migrations.AlterField(
            model_name="matrizpolivalencia",
            name="validacao",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="validacao_matriz",
                to="Funcionario.funcionario",
                verbose_name="Validação",
            ),
        ),
    ]