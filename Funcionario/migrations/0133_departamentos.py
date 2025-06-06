# Generated by Django 4.2.16 on 2025-05-28 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0132_alter_atividade_departamento_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Departamentos",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nome",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="Nome do Departamento"
                    ),
                ),
                (
                    "sigla",
                    models.CharField(
                        blank=True,
                        max_length=10,
                        null=True,
                        unique=True,
                        verbose_name="Sigla",
                    ),
                ),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
            ],
            options={
                "verbose_name": "Departamento",
                "verbose_name_plural": "Departamentos",
                "ordering": ["nome"],
            },
        ),
    ]
