# Generated by Django 4.2.7 on 2024-05-27 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0003_alter_event_emoji'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='emoji',
            field=models.CharField(max_length=35),
        ),
    ]
