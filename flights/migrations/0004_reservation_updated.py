# Generated by Django 2.0.3 on 2018-05-13 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flights', '0003_auto_20180513_1916'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
