# Generated by Django 5.1.2 on 2024-11-12 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("Funcionario", "0042_alter_comunicado_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comunicado",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]