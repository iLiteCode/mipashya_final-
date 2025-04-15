# Generated by Django 5.1.5 on 2025-04-02 07:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('krishna', '0002_alter_hotels_name'),
        ('user', '0003_hotelstaff_userf_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotelstaff',
            name='hotel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='krishna.hotels'),
        ),
    ]
