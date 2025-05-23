# Generated by Django 4.2.16 on 2025-05-09 19:03

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("qualidade_fornecimento", "0070_alertausuario"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alertausuario",
            name="titulo",
            field=models.CharField(max_length=120),
        ),
        migrations.CreateModel(
            name="AlertaConfigurado",
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
                        choices=[("F045_GERADO", "Geração de F045")],
                        max_length=30,
                        unique=True,
                    ),
                ),
                ("ativo", models.BooleanField(default=True)),
                ("grupos", models.ManyToManyField(blank=True, to="auth.group")),
                (
                    "usuarios",
                    models.ManyToManyField(
                        blank=True,
                        related_name="alertas_configurados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
