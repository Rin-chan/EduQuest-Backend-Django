from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_studentfeedback_bloom_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_type',
            field=models.CharField(default='mcq', max_length=50),
        ),
        migrations.AddField(
            model_name='question',
            name='structured_data',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
