# Generated by Django 5.0.6 on 2024-11-20 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_order_company'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='custom_order_id',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]