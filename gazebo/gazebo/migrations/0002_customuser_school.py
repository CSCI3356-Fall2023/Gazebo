# Generated by Django 4.2.6 on 2023-12-16 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gazebo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='school',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
