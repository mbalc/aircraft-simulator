# Generated by Django 2.0.3 on 2018-05-13 19:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flights', '0002_auto_20180513_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='ticketCount',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
