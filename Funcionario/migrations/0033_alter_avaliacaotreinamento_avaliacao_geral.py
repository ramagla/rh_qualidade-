# Generated by Django 5.1.2 on 2024-11-07 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "Funcionario",
            "0032_remove_avaliacaotreinamento_responsavel_1_cargo_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="avaliacaotreinamento",
            name="avaliacao_geral",
            field=models.IntegerField(
                choices=[
                    (1, "Pouco eficaz"),
                    (2, "Eficaz"),
                    (3, "Razoável"),
                    (4, "Bom"),
                    (5, "Muito eficaz"),
                ]
            ),
        ),
    ]