# Generated by Django 4.1.7 on 2023-04-15 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_customer_order_shippingaddress_orderproduct'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city_name', models.CharField(max_length=255, verbose_name='Название города')),
            ],
            options={
                'verbose_name': 'Город',
                'verbose_name_plural': 'Города',
            },
        ),
        migrations.RemoveField(
            model_name='customer',
            name='email',
        ),
        migrations.RemoveField(
            model_name='customer',
            name='name',
        ),
        migrations.AddField(
            model_name='customer',
            name='first_name',
            field=models.CharField(default='', max_length=255, verbose_name='Имя покупателя'),
        ),
        migrations.AddField(
            model_name='customer',
            name='last_name',
            field=models.CharField(default='', max_length=255, verbose_name='Фамилия покупателя'),
        ),
        migrations.AlterField(
            model_name='shippingaddress',
            name='city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.city', verbose_name='Города'),
        ),
    ]
