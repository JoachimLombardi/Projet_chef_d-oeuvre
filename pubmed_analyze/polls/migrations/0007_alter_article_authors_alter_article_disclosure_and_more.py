# Generated by Django 4.2.15 on 2024-09-06 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0006_alter_article_author_affiliation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='authors',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='disclosure',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='doi',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='title',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='title_review',
            field=models.TextField(null=True),
        ),
    ]