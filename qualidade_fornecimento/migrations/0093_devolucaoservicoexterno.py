# Generated by Django 4.2.16 on 2025-06-27 12:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0092_inspecao10_disposicao_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DevolucaoServicoExterno",
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
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=10)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "inspecao",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qualidade_fornecimento.inspecao10",
                    ),
                ),
                (
                    "servico",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qualidade_fornecimento.controleservicoexterno",
                    ),
                ),
            ],
        ),
    ]
