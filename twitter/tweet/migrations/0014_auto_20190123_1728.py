# Generated by Django 2.0.3 on 2019-01-23 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tweet', '0013_auto_20190123_1723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='behance',
            field=models.URLField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='facebook',
            field=models.URLField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='google',
            field=models.URLField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='twitter',
            field=models.URLField(blank=True, max_length=256, null=True),
        ),
    ]
