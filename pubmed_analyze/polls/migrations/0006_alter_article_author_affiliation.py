# Generated by Django 4.2.15 on 2024-09-06 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0005_alter_article_abstract'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='author_affiliation',
            field=models.TextField(null=True),
        ),
    ]