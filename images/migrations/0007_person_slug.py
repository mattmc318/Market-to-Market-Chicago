# Generated by Django 3.0.5 on 2020-05-09 01:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0006_auto_20200507_1903'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='slug',
            field=models.SlugField(default='none', max_length=70),
            preserve_default=False,
        ),
    ]