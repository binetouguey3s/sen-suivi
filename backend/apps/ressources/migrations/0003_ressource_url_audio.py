import apps.ressources.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ressources', '0002_lieudetente_acces_libre_lieudetente_latitude_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ressource',
            name='url_audio',
            field=models.CharField(
                blank=True,
                help_text='Obligatoire pour un podcast : « /audio/podcasts/mon-episode.mp3 » ou une adresse https.',
                max_length=300,
                validators=[apps.ressources.models.valider_url_audio],
                verbose_name='fichier audio',
            ),
        ),
    ]
