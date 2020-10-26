# Generated by Django 3.0.8 on 2020-10-26 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0010_location_no_kitchen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='location',
            name='slug',
            field=models.SlugField(blank=True, default='', editable=False, max_length=80, null=True),
        ),
        migrations.AlterField(
            model_name='neighborhood',
            name='slug',
            field=models.SlugField(blank=True, default='', editable=False, max_length=80, null=True),
        ),
    ]
