# Generated by Django 4.2.7 on 2024-01-14 21:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_rename_created_at_user_date_joined'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile',
            field=models.CharField(default='https://www.alexgrey.com/img/containers/art_images/Vision-Crystal-1997-Alex-Grey-watermarked.jpg/56918913653b1da5e0cd6ddaee34f455.jpg', max_length=255),
            preserve_default=False,
        ),
    ]
