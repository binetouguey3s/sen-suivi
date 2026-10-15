import apps.ressources.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ressources', '0003_ressource_url_audio'),
    ]

    operations = [
        migrations.AddField(
            model_name='ressource',
            name='fichier_audio',
            field=models.FileField(
                blank=True,
                help_text='MP3, M4A ou OGG, 20 Mo au plus.',
                upload_to='audio/',
                validators=[apps.ressources.models.valider_fichier_audio],
                verbose_name='fichier audio envoyé',
            ),
        ),
    ]
