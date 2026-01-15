from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_question_hint_useranswerattempt_hint_used'),
    ]

    operations = [
        migrations.AddField(
            model_name='userquestattempt',
            name='bonus_points',
            field=models.FloatField(default=0),
        ),
    ]
