# Generated by Django 5.1.6 on 2025-02-22 16:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_alter_book_options_alter_category_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='bookborrowing',
            name='due_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='应还时间'),
        ),
        migrations.AddField(
            model_name='bookborrowing',
            name='status',
            field=models.CharField(choices=[('borrowed', '借阅中'), ('returned', '已归还'), ('overdue', '已逾期')], default='borrowed', max_length=10, verbose_name='借阅状态'),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='邮箱')),
                ('phone', models.CharField(max_length=11, verbose_name='电话')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatar/', verbose_name='头像')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户信息',
                'verbose_name_plural': '用户信息',
                'db_table': 'books_userprofile',
            },
        ),
    ]
