# Generated by Django 5.1.2 on 2024-12-03 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0075_documento_revisaodoc"),
    ]

    operations = [
        migrations.AddField(
            model_name="revisaodoc",
            name="status",
            field=models.CharField(
                choices=[("ativo", "Ativo"), ("inativo", "Inativo")],
                default="ativo",
                max_length=10,
            ),
        ),
    ]