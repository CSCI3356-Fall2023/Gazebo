# Generated by Django 4.2.6 on 2023-11-09 00:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gazebo", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="days",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="course",
            name="is_open",
            field=models.BooleanField(default=True),
        ),
    ]
