# Generated by Django 4.0 on 2021-12-22 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='apartment',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Квартира'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='building',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Строение'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='house',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Дом'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='structure',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Корпус'),
        ),
    ]
