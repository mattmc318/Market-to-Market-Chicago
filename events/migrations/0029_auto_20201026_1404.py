# Generated by Django 3.0.8 on 2020-10-26 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0028_event_holiday'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=80, null=True),
        ),
    ]