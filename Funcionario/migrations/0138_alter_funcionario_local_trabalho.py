# Generated by Django 4.2.16 on 2025-05-28 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0137_migrar_funcionarios_para_departamentos"),
    ]

    operations = [
        migrations.AlterField(
            model_name="funcionario",
            name="local_trabalho",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
