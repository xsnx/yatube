# Generated by Django 2.2.6 on 2020-07-26 14:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_follow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='image',
        ),
    ]
