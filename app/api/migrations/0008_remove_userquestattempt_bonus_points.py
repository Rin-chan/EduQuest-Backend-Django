from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_userquestattempt_bonus_points'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userquestattempt',
            name='bonus_points',
        ),
    ]
