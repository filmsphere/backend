# Generated by Django 5.1.6 on 2025-02-28 11:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('movie', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seat',
            name='locked_at',
        ),
    ]
