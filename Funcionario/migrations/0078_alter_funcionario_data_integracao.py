# Generated by Django 5.1.2 on 2024-12-04 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0077_alter_funcionario_responsavel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funcionario",
            name="data_integracao",
            field=models.DateField(blank=True, null=True),
        ),
    ]
