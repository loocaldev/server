# Generated by Django 5.0.6 on 2024-11-11 01:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_discount_order_discount_value_order_total_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='discount_type',
            field=models.CharField(choices=[('absolute', 'Absoluto'), ('percentage', 'Porcentaje')], default='absolute', max_length=10),
        ),
    ]
