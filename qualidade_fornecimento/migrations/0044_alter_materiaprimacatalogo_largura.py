# Generated by Django 4.2.16 on 2025-04-16 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qualidade_fornecimento", "0043_materiaprimacatalogo_largura"),
    ]

    operations = [
        migrations.AlterField(
            model_name="materiaprimacatalogo",
            name="largura",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="Largura"
            ),
        ),
    ]
