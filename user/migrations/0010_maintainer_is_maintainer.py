# Generated by Django 5.1.7 on 2025-04-08 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_user_is_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintainer',
            name='is_maintainer',
            field=models.BooleanField(default=False),
        ),
    ]
