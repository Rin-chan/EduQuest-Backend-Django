from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_question_type_structured_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='hint',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='useranswerattempt',
            name='hint_used',
            field=models.BooleanField(default=False),
        ),
    ]
