import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_job_is_custom_resume_generated'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobuniquekey',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
