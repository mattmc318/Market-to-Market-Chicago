# Generated by Django 2.2.6 on 2020-03-11 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_auto_20200310_1830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='image',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='people/'),
        ),
    ]