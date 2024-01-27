# Generated by Django 5.0.1 on 2024-01-26 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_rename_newpermission_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': [('view_all', 'Can view all information')],
            },
        ),
        migrations.DeleteModel(
            name='User',
        ),
    ]