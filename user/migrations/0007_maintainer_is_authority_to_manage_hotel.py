# Generated by Django 5.1.5 on 2025-04-04 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_alter_hotelstaff_staff_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintainer',
            name='is_authority_to_manage_hotel',
            field=models.BooleanField(default=False),
        ),
    ]
