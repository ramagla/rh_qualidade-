# Generated by Django 4.2.16 on 2025-05-14 19:41

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0104_alter_avaliacaotreinamento_avaliacao_geral_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cargo",
            name="aprovador",
        ),
        migrations.RemoveField(
            model_name="cargo",
            name="aprovador_data",
        ),
        migrations.RemoveField(
            model_name="cargo",
            name="descricao_arquivo",
        ),
        migrations.RemoveField(
            model_name="cargo",
            name="elaborador",
        ),
        migrations.RemoveField(
            model_name="cargo",
            name="elaborador_data",
        ),
        migrations.CreateModel(
            name="AssinaturaCargo",
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
                    "papel",
                    models.CharField(
                        choices=[
                            ("elaborador", "Elaborador"),
                            ("aprovador", "Aprovador"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "data_assinatura",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "cargo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assinaturas",
                        to="Funcionario.cargo",
                    ),
                ),
                (
                    "funcionario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="Funcionario.funcionario",
                    ),
                ),
            ],
            options={
                "ordering": ["data_assinatura"],
                "unique_together": {("cargo", "papel")},
            },
        ),
    ]
