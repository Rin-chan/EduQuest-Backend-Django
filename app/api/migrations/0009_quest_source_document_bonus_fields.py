from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_remove_userquestattempt_bonus_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='quest',
            name='source_document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quests', to='api.document'),
        ),
        migrations.AddField(
            model_name='userquestattempt',
            name='bonus_points',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='userquestattempt',
            name='bonus_awarded',
            field=models.BooleanField(default=False),
        ),
    ]
