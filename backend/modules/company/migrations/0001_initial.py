from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
                ('linkedin_url', models.TextField(blank=True, null=True)),
                ('type', models.TextField(blank=True, choices=[('topCompany', 'Top company'), ('blacklist', 'Blacklist')], null=True)),
                ('cooling_period_end_at', models.DateTimeField(blank=True, null=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'companies',
            },
        ),
    ]
