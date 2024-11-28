# Generated by Django 5.0.6 on 2024-11-27 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_order_order_status_alter_order_payment_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('online', 'Online'), ('in_person', 'In-person')], default='online', max_length=10, verbose_name='Método de Pago'),
        ),
    ]