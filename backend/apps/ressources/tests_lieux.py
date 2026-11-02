"""Lieux de détente : modèle, migration des anciens accès, validation des photos."""

import tempfile
from collections import Counter
from datetime import date
from io import StringIO

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings

from rest_framework.test import APITestCase

from apps.comptes.models import Administrateur, Utilisateur

from .admin import FiltrePhotoEnvoyee, LieuDetenteAdmin
from .lieux_senegal import LIEUX_SENEGAL
from .models import AccesLieu, CategorieLieu, LieuDetente, Region, valider_image_lieu
from .tests_pro import professionnel

JPEG = b'\xff\xd8\xff\xe0' + b'0' * 20
PNG = b'\x89PNG\r\n\x1a\n' + b'0' * 20
WEBP = b'RIFF\x10\x00\x00\x00WEBP' + b'0' * 20


def lieu(**champs):
    valeurs = {
        'nom': 'Lieu', 'ville': 'Dakar', 'description': 'Un lieu.', 'region': Region.DAKAR,
        'categorie': CategorieLieu.PLAGES, 'acces': AccesLieu.LIBRE,
    }
    return LieuDetente.objects.create(**{**valeurs, **champs})


class ModeleLieuTests(TestCase):
    def test_acces_libre_est_calcule_depuis_acces(self):
        attendus = {
            AccesLieu.GRATUIT: True,
            AccesLieu.LIBRE: True,
            AccesLieu.PAYANT: False,
            AccesLieu.MIXTE: False,
            AccesLieu.RESTREINT: False,
        }
        for acces, attendu in attendus.items():
            with self.subTest(acces=acces):
                self.assertIs(LieuDetente(acces=acces).acces_libre, attendu)

    def test_les_14_regions_et_10_categories_existent(self):
        self.assertEqual(len(Region.choices), 14)
        self.assertEqual(len(CategorieLieu.choices), 10)
        self.assertIn('Thiès', Region.values)
        self.assertIn('Plages & littoral', CategorieLieu.values)

    def test_un_meme_nom_est_permis_dans_deux_regions_mais_pas_deux_fois_dans_une(self):
        lieu(nom='Lac de Guiers', region=Region.SAINT_LOUIS)
        lieu(nom='Lac de Guiers', region=Region.LOUGA)
        with self.assertRaises(IntegrityError), transaction.atomic():
            lieu(nom='Lac de Guiers', region=Region.LOUGA)

    def test_les_lignes_sans_region_echappent_a_la_contrainte(self):
        lieu(nom='Ancien', region='')
        lieu(nom='Ancien', region='')
        self.assertEqual(LieuDetente.objects.filter(nom='Ancien').count(), 2)


class ValidationImageTests(TestCase):
    def test_accepte_jpeg_png_et_webp(self):
        for nom, contenu in (('a.jpg', JPEG), ('a.jpeg', JPEG), ('a.PNG', PNG), ('a.webp', WEBP)):
            with self.subTest(nom=nom):
                valider_image_lieu(SimpleUploadedFile(nom, contenu))

    def test_refuse_une_extension_non_prise_en_charge(self):
        with self.assertRaisesMessage(ValidationError, 'JPEG, PNG ou WebP'):
            valider_image_lieu(SimpleUploadedFile('a.svg', b'<svg xmlns="http://www.w3.org/2000/svg"/>'))

    def test_refuse_un_fichier_renomme(self):
        with self.assertRaisesMessage(ValidationError, "n'est pas une image"):
            valider_image_lieu(SimpleUploadedFile('a.jpg', b'<html><script>alert(1)</script></html>'))

    def test_refuse_un_contenu_qui_ne_correspond_pas_a_l_extension(self):
        with self.assertRaisesMessage(ValidationError, "n'est pas une image"):
            valider_image_lieu(SimpleUploadedFile('a.png', JPEG))

    @override_settings(IMAGE_LIEU_MAX_OCTETS=10)
    def test_refuse_un_fichier_trop_lourd(self):
        with self.assertRaisesMessage(ValidationError, 'dépasse'):
            valider_image_lieu(SimpleUploadedFile('a.jpg', JPEG))


class AdminLieuTests(TestCase):
    def test_filtre_photo_envoyee(self):
        avec = lieu(nom='Avec photo', image='lieux/a.jpg')
        sans = lieu(nom='Sans photo')
        modele_admin = LieuDetenteAdmin(LieuDetente, admin.site)
        requete = RequestFactory().get('/')
        for valeur, attendu in (('oui', avec), ('non', sans)):
            with self.subTest(valeur=valeur):
                filtre = FiltrePhotoEnvoyee(requete, {'photo': [valeur]}, LieuDetente, modele_admin)
                self.assertEqual(list(filtre.queryset(requete, LieuDetente.objects.all())), [attendu])


class MigrationAccesTests(TransactionTestCase):
    avant = [('ressources', '0005_ressources_proposees_par_les_pros')]
    apres = [('ressources', '0006_lieux_senegal')]

    def tearDown(self):
        executeur = MigrationExecutor(connection)
        executeur.migrate(executeur.loader.graph.leaf_nodes())

    def test_les_anciens_acces_sont_convertis(self):
        executeur = MigrationExecutor(connection)
        executeur.migrate(self.avant)
        Ancien = executeur.loader.project_state(self.avant).apps.get_model('ressources', 'LieuDetente')
        libre = Ancien.objects.create(nom='Libre', ville='Dakar', description='.', categorie='Plage', acces_libre=True)
        payant = Ancien.objects.create(nom='Payant', ville='Dakar', description='.', categorie='Parc', acces_libre=False)

        executeur = MigrationExecutor(connection)
        executeur.migrate(self.apres)
        Nouveau = executeur.loader.project_state(self.apres).apps.get_model('ressources', 'LieuDetente')
        self.assertEqual(Nouveau.objects.get(pk=libre.pk).acces, 'LIBRE')
        self.assertEqual(Nouveau.objects.get(pk=payant.pk).acces, 'PAYANT')
        self.assertEqual(Nouveau.objects.get(pk=libre.pk).region, '')


REPARTITION_REGIONS = {
    'Dakar': 16, 'Thiès': 11, 'Saint-Louis': 10, 'Louga': 6, 'Matam': 5, 'Tambacounda': 5, 'Kédougou': 7,
    'Kolda': 4, 'Sédhiou': 4, 'Ziguinchor': 10, 'Fatick': 9, 'Kaolack': 5, 'Kaffrine': 3, 'Diourbel': 3,
}
REPARTITION_ACCES = {'GRATUIT': 9, 'LIBRE': 37, 'PAYANT': 41, 'MIXTE': 8, 'RESTREINT': 3}
ANCIENS_LIEUX = [
    ('Plage de Ngor', 'Dakar', 'Plages publiques (Ngor, Yoff, Virage, Anse Bernard, Malibu)', 'Dakar'),
    ('Île de Gorée', 'Dakar', 'Île de Gorée', 'Dakar'),
    ('Lac Rose', 'Niayes', 'Lac Rose (Lac Retba)', 'Dakar'),
    ('Parc Forestier de Hann', 'Dakar', 'Parc Forestier et Zoologique de Hann', 'Dakar'),
    ('Lagune de la Somone', 'Mbour', 'Lagune de la Somone (RNIC)', 'Thiès'),
    ('Corniche Ouest', 'Dakar', 'Corniche Ouest & parcours sportifs', 'Dakar'),
    ('Popenguine', 'Thiès', 'Réserve Naturelle de Popenguine', 'Thiès'),
    ('Toubab Dialaw', 'Thiès', 'Toubab Dialaw', 'Dakar'),
]


def importer():
    call_command('importer_lieux', stdout=StringIO())


class DonneesLieuxTests(TestCase):
    """La liste recopiée du PDF correspond à sa page de synthèse."""

    def test_98_sites_avec_la_repartition_de_la_page_2(self):
        self.assertEqual(len(LIEUX_SENEGAL), 98)
        self.assertEqual(dict(Counter(site['region'] for site in LIEUX_SENEGAL)), REPARTITION_REGIONS)
        self.assertEqual(dict(Counter(site['acces'] for site in LIEUX_SENEGAL)), REPARTITION_ACCES)

    def test_chaque_site_est_complet_et_valide(self):
        for site in LIEUX_SENEGAL:
            with self.subTest(nom=site['nom']):
                self.assertIn(site['categorie'], CategorieLieu.values)
                self.assertTrue(site['ville'] and site['type_lieu'] and site['precisions'] and site['description'])

    def test_les_coordonnees_sont_au_senegal_ou_absentes(self):
        for site in LIEUX_SENEGAL:
            with self.subTest(nom=site['nom']):
                self.assertEqual(site['latitude'] is None, site['longitude'] is None)
                if site['latitude'] is not None:
                    self.assertTrue(12.2 <= site['latitude'] <= 16.8)
                    self.assertTrue(-17.6 <= site['longitude'] <= -11.3)

    def test_les_lieux_restreints_sont_ceux_du_pdf(self):
        restreints = {site['nom'] for site in LIEUX_SENEGAL if site['acces'] == 'RESTREINT'}
        self.assertEqual(restreints, {
            'Parc National de Basse Casamance',
            'Réserve Ornithologique de Kalissaye',
            'Réserve écologique expérimentale de Mbour',
        })

    def test_le_parc_dakar_yoff_n_est_pas_ajoute_avant_son_ouverture(self):
        self.assertFalse([site for site in LIEUX_SENEGAL if 'Yoff' in site['nom'] and 'Parc' in site['nom']])

    def test_vigilance_et_periode_sont_rattachees_aux_bons_sites(self):
        par_nom = {site['nom']: site for site in LIEUX_SENEGAL}
        self.assertIn('feux de brousse', par_nom['Cascade et RNC de Dindéfélo']['vigilance'].lower())
        self.assertEqual(par_nom['Parc National des Oiseaux du Djoudj']['meilleure_periode'], 'Novembre à avril')
        self.assertEqual(par_nom['Parc National du Niokolo-Koba']['meilleure_periode'], 'Saison sèche')
        self.assertEqual(par_nom['Plage de Potou']['vigilance'], '')
        self.assertEqual(par_nom['Plage de Potou']['meilleure_periode'], '')


class ImportLieuxTests(TestCase):
    def test_import_sur_une_base_vide(self):
        importer()
        self.assertEqual(LieuDetente.objects.count(), 98)
        self.assertEqual(LieuDetente.objects.filter(derniere_verification=date(2026, 11, 1)).count(), 98)

    def test_un_second_import_ne_cree_aucun_doublon(self):
        importer()
        ids = set(LieuDetente.objects.values_list('id', flat=True))
        importer()
        self.assertEqual(set(LieuDetente.objects.values_list('id', flat=True)), ids)

    def test_les_sites_de_deux_regions_restent_separes(self):
        importer()
        self.assertEqual(LieuDetente.objects.filter(nom='Lac de Guiers', region='Saint-Louis').count(), 1)
        self.assertEqual(LieuDetente.objects.filter(nom='Lac de Guiers (rive ouest)', region='Louga').count(), 1)

    def test_les_8_anciens_lieux_sont_repris_sans_perdre_leur_contenu(self):
        anciens = {
            nom: LieuDetente.objects.create(
                nom=nom, ville=ville, categorie='Plage', description=f'Riche : {nom}', latitude=14.5, longitude=-17.1,
            )
            for nom, ville, _, _ in ANCIENS_LIEUX
        }
        importer()
        self.assertEqual(LieuDetente.objects.count(), 98)
        for ancien_nom, _, nom, region in ANCIENS_LIEUX:
            with self.subTest(nom=nom):
                repris = LieuDetente.objects.get(nom=nom, region=region)
                self.assertEqual(repris.pk, anciens[ancien_nom].pk)
                self.assertEqual(repris.description, f'Riche : {ancien_nom}')
                self.assertEqual(repris.latitude, 14.5)
                self.assertNotEqual(repris.categorie, 'Plage')

    def test_un_ancien_lieu_recree_a_cote_du_nouveau_est_absorbe(self):
        importer()
        LieuDetente.objects.create(nom='Lac Rose', ville='Niayes', categorie='Site naturel', description='Ancien')
        importer()
        self.assertEqual(LieuDetente.objects.count(), 98)
        self.assertFalse(LieuDetente.objects.filter(nom='Lac Rose').exists())

    def test_un_import_conserve_photo_description_et_coordonnees(self):
        importer()
        site = LieuDetente.objects.get(nom='Cascade et RNC de Dindéfélo')
        LieuDetente.objects.filter(pk=site.pk).update(
            image='lieux/dindefelo.jpg', description='Corrigée', latitude=12.1, longitude=-12.1,
        )
        importer()
        site.refresh_from_db()
        self.assertEqual(site.image.name, 'lieux/dindefelo.jpg')
        self.assertEqual(site.description, 'Corrigée')
        self.assertEqual(site.latitude, 12.1)

    def test_un_import_remet_a_jour_les_colonnes_du_pdf(self):
        importer()
        LieuDetente.objects.filter(nom='Plage de Potou').update(acces='PAYANT', precisions='Faux')
        importer()
        site = LieuDetente.objects.get(nom='Plage de Potou')
        self.assertEqual((site.acces, site.precisions), ('LIBRE', 'Accès libre'))


class SeedLieuxTests(TestCase):
    def test_relancer_le_seed_garde_98_lieux(self):
        call_command('seed_donnees', stdout=StringIO())
        self.assertEqual(LieuDetente.objects.count(), 98)
        call_command('seed_donnees', stdout=StringIO())
        self.assertEqual(LieuDetente.objects.count(), 98)
        self.assertFalse(LieuDetente.objects.filter(nom='Plage de Ngor').exists())


class ApiRechercheLieuxTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        lieu(nom='Lac Rose', ville='Niaga', region=Region.DAKAR, categorie=CategorieLieu.LACS, acces=AccesLieu.MIXTE)
        lieu(nom='Corniche', ville='Ouakam', region=Region.DAKAR, categorie=CategorieLieu.PLAGES, acces=AccesLieu.GRATUIT)
        lieu(nom='Kayar', ville='Kayar', region=Region.THIES, categorie=CategorieLieu.PLAGES, acces=AccesLieu.LIBRE,
             type_lieu='Aire marine, plage de pêche')
        lieu(nom='Bandia', ville='Sindia', region=Region.THIES, categorie=CategorieLieu.RESERVES, acces=AccesLieu.PAYANT)
        lieu(nom='Cascade de Dindéfélo', ville='Dindéfélo', region=Region.KEDOUGOU, categorie=CategorieLieu.CASCADES,
             acces=AccesLieu.PAYANT)
        lieu(nom='Basse Casamance', ville='Oussouye', region=Region.ZIGUINCHOR, categorie=CategorieLieu.RESERVES,
             acces=AccesLieu.RESTREINT)

    def noms(self, **params):
        reponse = self.client.get('/api/lieux', params)
        self.assertEqual(reponse.status_code, 200)
        return {site['nom'] for site in reponse.data}

    def test_sans_filtre_tout_est_renvoye(self):
        self.assertEqual(len(self.noms()), 6)

    def test_filtre_region(self):
        self.assertEqual(self.noms(region='Thiès'), {'Kayar', 'Bandia'})

    def test_filtre_categorie(self):
        self.assertEqual(self.noms(categorie='Plages & littoral'), {'Corniche', 'Kayar'})

    def test_filtre_acces_a_une_valeur(self):
        self.assertEqual(self.noms(acces='RESTREINT'), {'Basse Casamance'})

    def test_filtre_acces_a_plusieurs_valeurs(self):
        self.assertEqual(self.noms(acces=['GRATUIT', 'LIBRE']), {'Corniche', 'Kayar'})

    def test_ouverts_masque_les_lieux_restreints(self):
        self.assertNotIn('Basse Casamance', self.noms(ouverts='1'))
        self.assertEqual(len(self.noms(ouverts='1')), 5)

    def test_ouverts_0_ne_masque_rien(self):
        self.assertEqual(len(self.noms(ouverts='0')), 6)

    def test_ville_reste_accepte(self):
        self.assertEqual(self.noms(ville='Ouakam'), {'Corniche'})

    def test_q_cherche_dans_nom_ville_region_et_type(self):
        self.assertEqual(self.noms(q='Rose'), {'Lac Rose'})
        self.assertEqual(self.noms(q='Sindia'), {'Bandia'})
        self.assertEqual(self.noms(q='Ziguinchor'), {'Basse Casamance'})
        self.assertEqual(self.noms(q='aire marine'), {'Kayar'})

    def test_q_ignore_majuscules_et_accents(self):
        self.assertEqual(self.noms(q='thies'), {'Kayar', 'Bandia'})
        self.assertEqual(self.noms(q='DINDEFELO'), {'Cascade de Dindéfélo'})
        self.assertEqual(self.noms(q='pêche'), {'Kayar'})
        self.assertEqual(self.noms(q='peche'), {'Kayar'})

    def test_q_cherche_chaque_mot_quel_que_soit_le_champ(self):
        self.assertEqual(self.noms(q='lac dakar'), {'Lac Rose'})

    def test_q_vide_ou_sans_resultat(self):
        self.assertEqual(len(self.noms(q='   ')), 6)
        self.assertEqual(self.noms(q='introuvable'), set())

    def test_les_filtres_se_combinent(self):
        self.assertEqual(self.noms(region='Thiès', categorie='Plages & littoral'), {'Kayar'})
        self.assertEqual(self.noms(region='Dakar', acces=['GRATUIT', 'LIBRE'], q='ouakam'), {'Corniche'})
        self.assertEqual(self.noms(categorie='Parcs nationaux & réserves', ouverts='1'), {'Bandia'})

    def test_la_reponse_contient_tous_les_champs(self):
        site = LieuDetente.objects.get(nom='Kayar')
        LieuDetente.objects.filter(pk=site.pk).update(
            precisions='Accès libre', vigilance='Attention', meilleure_periode='Saison sèche',
            derniere_verification=date(2026, 11, 1),
        )
        donnees = self.client.get(f'/api/lieux/{site.pk}').data
        self.assertEqual(donnees['region'], 'Thiès')
        self.assertEqual(donnees['type_lieu'], 'Aire marine, plage de pêche')
        self.assertEqual(donnees['acces'], 'LIBRE')
        self.assertIs(donnees['acces_libre'], True)
        self.assertEqual(donnees['precisions'], 'Accès libre')
        self.assertEqual(donnees['vigilance'], 'Attention')
        self.assertEqual(donnees['meilleure_periode'], 'Saison sèche')
        self.assertEqual(donnees['derniere_verification'], '2026-11-01')
        self.assertIsNone(donnees['image'])

    def test_image_est_une_adresse_complete(self):
        site = LieuDetente.objects.get(nom='Kayar')
        LieuDetente.objects.filter(pk=site.pk).update(image='lieux/kayar.jpg')
        self.assertEqual(self.client.get(f'/api/lieux/{site.pk}').data['image'], 'http://testserver/media/lieux/kayar.jpg')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ApiPhotoLieuTests(APITestCase):
    def setUp(self):
        self.lieu = lieu(nom='Mont Assirik')
        self.url = f'/api/lieux/{self.lieu.pk}/image'
        self.admin = Administrateur.objects.create(email='admin@test.sn', nom='Admin')

    def envoyer(self, nom='photo.jpg', contenu=JPEG):
        return self.client.post(self.url, {'image': SimpleUploadedFile(nom, contenu)}, format='multipart')

    def test_il_faut_etre_connecte(self):
        self.assertEqual(self.envoyer().status_code, 401)
        self.assertEqual(self.client.delete(self.url).status_code, 401)

    def test_utilisateurs_et_professionnels_sont_refuses(self):
        comptes = [
            Utilisateur.objects.create(email='u@test.sn', nom='U'),
            professionnel(),
        ]
        for compte in comptes:
            with self.subTest(compte=compte.email):
                self.client.force_authenticate(compte)
                self.assertEqual(self.envoyer().status_code, 403)
                self.assertEqual(self.client.delete(self.url).status_code, 403)
        self.lieu.refresh_from_db()
        self.assertFalse(self.lieu.image)

    def test_l_administration_envoie_jpeg_png_et_webp(self):
        self.client.force_authenticate(self.admin)
        for nom, contenu in (('a.jpg', JPEG), ('a.png', PNG), ('a.webp', WEBP)):
            with self.subTest(nom=nom):
                reponse = self.envoyer(nom, contenu)
                self.assertEqual(reponse.status_code, 200)
                self.assertRegex(reponse.data['image'], r'^http://testserver/media/lieux/a.*\.' + nom.split('.')[1])

    def test_la_photo_apparait_dans_l_api_publique(self):
        self.client.force_authenticate(self.admin)
        self.envoyer()
        self.client.force_authenticate(None)
        self.assertIn('/media/lieux/', self.client.get(f'/api/lieux/{self.lieu.pk}').data['image'])

    def test_les_faux_fichiers_sont_refuses_avec_un_message(self):
        self.client.force_authenticate(self.admin)
        cas = (
            ('a.svg', b'<svg xmlns="http://www.w3.org/2000/svg"/>', 'JPEG, PNG ou WebP'),
            ('a.jpg', b'<html><script>alert(1)</script></html>', "n'est pas une image"),
        )
        for nom, contenu, message in cas:
            with self.subTest(nom=nom):
                reponse = self.envoyer(nom, contenu)
                self.assertEqual(reponse.status_code, 400)
                self.assertIn(message, str(reponse.data['image']))
        self.lieu.refresh_from_db()
        self.assertFalse(self.lieu.image)

    @override_settings(IMAGE_LIEU_MAX_OCTETS=10)
    def test_un_fichier_trop_lourd_est_refuse(self):
        self.client.force_authenticate(self.admin)
        reponse = self.envoyer()
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('dépasse', str(reponse.data['image']))

    def test_sans_fichier_la_requete_est_refusee(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(self.url, {}, format='multipart').status_code, 400)

    def test_un_envoi_refuse_conserve_la_photo_en_place(self):
        self.client.force_authenticate(self.admin)
        self.envoyer()
        self.lieu.refresh_from_db()
        en_place = self.lieu.image.name
        self.assertEqual(self.envoyer('a.jpg', b'pas une image').status_code, 400)
        self.lieu.refresh_from_db()
        self.assertEqual(self.lieu.image.name, en_place)
        self.assertTrue(default_storage.exists(en_place))

    def test_remplacer_supprime_l_ancien_fichier(self):
        self.client.force_authenticate(self.admin)
        self.envoyer()
        self.lieu.refresh_from_db()
        ancien = self.lieu.image.name
        self.envoyer('b.png', PNG)
        self.lieu.refresh_from_db()
        self.assertNotEqual(self.lieu.image.name, ancien)
        self.assertFalse(default_storage.exists(ancien))
        self.assertTrue(default_storage.exists(self.lieu.image.name))

    def test_retirer_supprime_le_fichier(self):
        self.client.force_authenticate(self.admin)
        self.envoyer()
        self.lieu.refresh_from_db()
        ancien = self.lieu.image.name
        reponse = self.client.delete(self.url)
        self.assertEqual(reponse.status_code, 200)
        self.assertIsNone(reponse.data['image'])
        self.assertFalse(default_storage.exists(ancien))

    def test_retirer_sans_photo_ne_casse_rien(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(self.url).status_code, 200)

    def test_lieu_inconnu(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete('/api/lieux/999999/image').status_code, 404)
