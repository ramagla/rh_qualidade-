# Generated by Django 5.1.2 on 2024-12-06 16:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0087_alter_funcionario_cargo_responsavel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funcionario",
            name="responsavel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="funcionarios_gerenciados",
                to="Funcionario.funcionario",
            ),
        ),
    ]