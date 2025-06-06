# Generated by Django 4.2.16 on 2025-05-16 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0106_cargo_aprovador_cargo_aprovador_data_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="nota",
            name="suplente",
        ),
        migrations.AddField(
            model_name="nota",
            name="perfil",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Nenhum"),
                    ("suplente", "Suplente"),
                    ("treinado", "Treinado"),
                ],
                default="",
                max_length=10,
                verbose_name="Perfil",
            ),
        ),
    ]
