# Generated by Django 5.1.2 on 2024-11-12 12:39

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "Funcionario",
            "0040_rename_area_atual_jobrotationevaluation_local_trabalho_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Comunicado",
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
                ("data", models.DateField(default=django.utils.timezone.now)),
                ("assunto", models.CharField(max_length=100)),
                ("descricao", models.TextField()),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("Auditoria", "Auditoria"),
                            ("Conscientizacao", "Conscientização"),
                            ("Melhoria", "Melhoria"),
                            ("Organizacao/Processos", "Organização / Processos"),
                            ("Recursos Humanos", "Recursos Humanos"),
                            ("Visita de Cliente", "Visita de Cliente"),
                        ],
                        max_length=50,
                    ),
                ),
                ("departamento_responsavel", models.CharField(max_length=100)),
            ],
        ),
    ]