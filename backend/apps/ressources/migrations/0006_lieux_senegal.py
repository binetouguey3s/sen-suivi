import apps.ressources.models
from django.db import migrations, models


def acces_depuis_booleen(apps, schema_editor):
    LieuDetente = apps.get_model('ressources', 'LieuDetente')
    LieuDetente.objects.filter(acces_libre=True).update(acces='LIBRE')
    LieuDetente.objects.filter(acces_libre=False).update(acces='PAYANT')


def booleen_depuis_acces(apps, schema_editor):
    LieuDetente = apps.get_model('ressources', 'LieuDetente')
    LieuDetente.objects.update(acces_libre=False)
    LieuDetente.objects.filter(acces__in=['GRATUIT', 'LIBRE']).update(acces_libre=True)


REGIONS = [
    ('Dakar', 'Dakar'), ('Thiès', 'Thiès'), ('Saint-Louis', 'Saint-Louis'), ('Louga', 'Louga'),
    ('Matam', 'Matam'), ('Tambacounda', 'Tambacounda'), ('Kédougou', 'Kédougou'), ('Kolda', 'Kolda'),
    ('Sédhiou', 'Sédhiou'), ('Ziguinchor', 'Ziguinchor'), ('Fatick', 'Fatick'), ('Kaolack', 'Kaolack'),
    ('Kaffrine', 'Kaffrine'), ('Diourbel', 'Diourbel'),
]
CATEGORIES = [
    ('Plages & littoral', 'Plages & littoral'), ('Parcs & jardins', 'Parcs & jardins'),
    ('Parcs nationaux & réserves', 'Parcs nationaux & réserves'), ('Lacs & lagunes', 'Lacs & lagunes'),
    ('Îles', 'Îles'), ('Forêts', 'Forêts'), ('Cascades & montagnes', 'Cascades & montagnes'),
    ('Fleuves & mangroves', 'Fleuves & mangroves'), ('Désert & dunes', 'Désert & dunes'),
    ('Patrimoine & culture', 'Patrimoine & culture'),
]
ACCES = [
    ('GRATUIT', 'Gratuit'), ('LIBRE', 'Accès libre'), ('PAYANT', 'Payant'),
    ('MIXTE', 'Mixte'), ('RESTREINT', 'Restreint'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('ressources', '0005_ressources_proposees_par_les_pros'),
    ]

    operations = [
        migrations.AddField(
            model_name='lieudetente',
            name='acces',
            field=models.CharField(choices=ACCES, default='LIBRE', max_length=10, verbose_name='accès'),
        ),
        migrations.RunPython(acces_depuis_booleen, booleen_depuis_acces),
        migrations.RemoveField(
            model_name='lieudetente',
            name='acces_libre',
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='region',
            field=models.CharField(blank=True, choices=REGIONS, max_length=20, verbose_name='région'),
        ),
        migrations.AlterField(
            model_name='lieudetente',
            name='ville',
            field=models.CharField(max_length=100, verbose_name='localité'),
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='type_lieu',
            field=models.CharField(blank=True, max_length=150, verbose_name='type de lieu'),
        ),
        migrations.AlterField(
            model_name='lieudetente',
            name='categorie',
            field=models.CharField(choices=CATEGORIES, max_length=100, verbose_name='catégorie'),
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='precisions',
            field=models.TextField(blank=True, help_text='Tarif, pirogue, permis…', verbose_name='précisions'),
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='vigilance',
            field=models.TextField(blank=True, verbose_name='points de vigilance'),
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='meilleure_periode',
            field=models.CharField(blank=True, max_length=100, verbose_name='meilleure période'),
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='derniere_verification',
            field=models.DateField(blank=True, null=True, verbose_name='dernière vérification'),
        ),
        migrations.AddField(
            model_name='lieudetente',
            name='image',
            field=models.FileField(
                blank=True,
                help_text='Photo réelle du lieu, au Sénégal. JPEG, PNG ou WebP, 5 Mo au plus.',
                upload_to='lieux/',
                validators=[apps.ressources.models.valider_image_lieu],
                verbose_name='photo',
            ),
        ),
        migrations.AddConstraint(
            model_name='lieudetente',
            constraint=models.UniqueConstraint(
                condition=models.Q(('region', ''), _negated=True),
                fields=('nom', 'region'),
                name='lieu_unique_par_nom_et_region',
            ),
        ),
    ]
