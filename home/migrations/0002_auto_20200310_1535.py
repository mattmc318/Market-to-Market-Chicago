# Generated by Django 2.2.6 on 2020-03-10 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='phone',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]