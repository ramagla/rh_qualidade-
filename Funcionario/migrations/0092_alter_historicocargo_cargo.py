# Generated by Django 5.1.2 on 2024-12-13 12:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0091_alter_historicocargo_cargo_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicocargo",
            name="cargo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="historico_cargos",
                to="Funcionario.cargo",
            ),
        ),
    ]
