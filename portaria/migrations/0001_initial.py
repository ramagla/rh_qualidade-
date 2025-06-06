# Generated by Django 4.2.16 on 2025-05-20 15:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("Funcionario", "0116_alter_atividade_departamento_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PessoaPortaria",
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
                    "tipo",
                    models.CharField(
                        choices=[
                            ("visitante", "Visitante"),
                            ("entregador", "Entregador"),
                            ("colaborador", "Colaborador"),
                        ],
                        max_length=20,
                    ),
                ),
                ("nome", models.CharField(max_length=100)),
                (
                    "documento",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        verbose_name="Documento de Identidade",
                    ),
                ),
                (
                    "empresa",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Empresa/Origem",
                    ),
                ),
                (
                    "colaborador",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="Funcionario.funcionario",
                    ),
                ),
            ],
        ),
    ]
