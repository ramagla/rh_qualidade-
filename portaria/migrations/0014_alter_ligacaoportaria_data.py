# Generated by Django 4.2.16 on 2025-05-21 14:41

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("portaria", "0013_ligacaoportaria"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ligacaoportaria",
            name="data",
            field=models.DateField(
                default=django.utils.timezone.now, verbose_name="Data"
            ),
        ),
    ]
