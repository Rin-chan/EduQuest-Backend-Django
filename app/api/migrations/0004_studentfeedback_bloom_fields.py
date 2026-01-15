from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_useranswerattempt_is_correct'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentfeedback',
            name='quest_summary',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='studentfeedback',
            name='subtopic_feedback',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='studentfeedback',
            name='study_tips',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='studentfeedback',
            name='recommendations',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='studentfeedback',
            name='question_feedback',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='studentfeedback',
            name='strengths',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='studentfeedback',
            name='weaknesses',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
