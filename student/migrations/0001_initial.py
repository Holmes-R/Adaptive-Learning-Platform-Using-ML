# Generated by Django 5.1.4 on 2024-12-25 07:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoginForm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(default=' ', max_length=100)),
                ('user_password', models.CharField(max_length=8)),
                ('confirm_password', models.CharField(max_length=8)),
                ('user_otp', models.CharField(blank=True, max_length=6, null=True)),
                ('generated_otp', models.CharField(blank=True, max_length=6, null=True)),
                ('otp_expiry', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Login Students',
            },
        ),
    ]