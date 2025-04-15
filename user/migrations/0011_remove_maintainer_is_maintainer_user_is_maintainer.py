# Generated by Django 5.1.7 on 2025-04-08 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_maintainer_is_maintainer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='maintainer',
            name='is_maintainer',
        ),
        migrations.AddField(
            model_name='user',
            name='is_maintainer',
            field=models.BooleanField(default=False),
        ),
    ]
