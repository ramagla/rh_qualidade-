# Generated by Django 4.2.16 on 2025-05-20 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portaria", "0003_alter_pessoaportaria_tipo"),
    ]

    operations = [
        migrations.AddField(
            model_name="pessoaportaria",
            name="foto",
            field=models.ImageField(blank=True, null=True, upload_to="fotos_portaria/"),
        ),
        migrations.AlterField(
            model_name="pessoaportaria",
            name="documento",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="RG"
            ),
        ),
    ]
