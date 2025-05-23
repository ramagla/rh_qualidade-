# Generated by Django 5.1.2 on 2024-11-28 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0066_alter_nota_suplente"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nota",
            name="pontuacao",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (0, "Observador"),
                    (1, "Aprendiz"),
                    (2, "Assistente"),
                    (3, "Autônomo"),
                    (4, "Instrutor"),
                ],
                verbose_name="Pontuação",
            ),
        ),
    ]
