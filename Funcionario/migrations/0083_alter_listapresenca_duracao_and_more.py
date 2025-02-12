# Generated by Django 5.1.2 on 2024-12-06 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0082_alter_documento_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="listapresenca",
            name="duracao",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True
            ),
        ),
        migrations.AlterField(
            model_name="listapresenca",
            name="treinamento",
            field=models.CharField(
                choices=[
                    ("Treinamento", "Treinamento"),
                    ("Curso", "Curso"),
                    ("Divulgacao", "Divulgação"),
                    ("Conscientização", "Conscientização"),
                ],
                max_length=255,
            ),
        ),
    ]
