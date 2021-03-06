# Generated by Django 2.2.6 on 2020-01-15 01:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0023_auto_20200114_1843'),
    ]

    operations = [
        migrations.CreateModel(
            name='Weekday',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('weekday', models.PositiveSmallIntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
                ('info', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='events.RepeatInfo')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='RecurringEventWeekday',
        ),
    ]
