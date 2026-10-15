"""Ressources proposées par les professionnels : brouillon, soumission avec la
charte, relecture par l'administration, publication. Le public (et donc le
RAG de Titou) ne voit jamais que les ressources publiées. Vidéos YouTube."""

import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from apps.comptes.models import Administrateur, Professionnel, StatutValidationPro, Utilisateur
from apps.notifications.models import NotificationEmail

from .models import Ressource, StatutRessource, extraire_id_youtube

MP3 = b'ID3\x04\x00\x00\x00\x00\x00\x00' + b'\x00' * 64


def professionnel(nom='Awa Ndiaye', statut=StatutValidationPro.VALIDE, email=None):
    return Professionnel.objects.create(
        email=email or f"{nom.split()[0].lower()}@pro.sn", nom=nom, specialite='SOPHROLOGUE', ville='Dakar',
        langue='français', tarif_indicatif=10000, statut_validation=statut,
    )


class ExtraireIdYoutubeTests(SimpleTestCase):
    def test_les_formats_youtube_sont_reconnus(self):
        for lien in (
            'https://www.youtube.com/watch?v=aXItOY0sLRY',
            'https://youtube.com/watch?feature=share&v=aXItOY0sLRY',
            'https://youtu.be/aXItOY0sLRY?t=12',
            'https://www.youtube.com/shorts/aXItOY0sLRY',
            'https://www.youtube.com/embed/aXItOY0sLRY',
            'm.youtube.com/watch?v=aXItOY0sLRY',
        ):
            self.assertEqual(extraire_id_youtube(lien), 'aXItOY0sLRY', lien)

    def test_les_autres_liens_sont_refuses(self):
        for lien in (
            'https://vimeo.com/123456',
            'https://www.youtube.com.exemple.sn/watch?v=aXItOY0sLRY',
            'https://exemple.sn/?v=aXItOY0sLRY',
            'https://youtu.be/court',  # identifiant de moins de 11 caractères
            'https://www.youtube.com/watch?v=aXItOY0sLRY"><script>',
            'javascript:alert(1)',
            '',
        ):
            self.assertIsNone(extraire_id_youtube(lien), lien)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), EMAIL_NOTIFICATIONS=False)
@patch('apps.ressources.views.declencher_workflow')
class RessourcesProTests(APITestCase):
    def setUp(self):
        self.awa = professionnel()
        self.autre = professionnel('Moussa Ba')
        self.admin = Administrateur.objects.create(email='admin@test.sn', nom='Admin')

    def creer(self, compte=None, **champs):
        self.client.force_authenticate(compte or self.awa)
        donnees = {'titre': 'Trois respirations pour décrocher', 'type_ressource': 'EXERCICE', 'thematique': 'Stress',
                   'contenu': 'Un exercice de trois minutes.', 'duree_lecture': 3, **champs}
        return self.client.post('/api/pro/ressources', donnees, format='json')

    def soumettre(self, pk, charte=True):
        return self.client.post(f'/api/pro/ressources/{pk}/soumettre', {'charte_acceptee': charte}, format='json')

    # --- Droits ---------------------------------------------------------------

    def test_un_pro_non_valide_ne_peut_rien_creer(self, _):
        en_attente = professionnel('Fatou Sarr', StatutValidationPro.EN_ATTENTE)
        self.assertEqual(self.creer(en_attente).status_code, 403)
        self.client.force_authenticate(Utilisateur.objects.create(email='u@test.sn', nom='U'))
        self.assertEqual(self.client.get('/api/pro/ressources').status_code, 403)

    def test_creee_en_brouillon_avec_son_auteur(self, workflow):
        reponse = self.creer()
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(reponse.data['statut'], 'BROUILLON')
        self.assertEqual(reponse.data['auteur']['nom'], 'Awa Ndiaye')
        workflow.assert_not_called()  # rien de public n'a changé

    def test_le_statut_ne_se_choisit_pas(self, _):
        reponse = self.creer(statut='PUBLIEE')
        self.assertEqual(reponse.data['statut'], 'BROUILLON')

    def test_un_pro_ne_voit_et_ne_modifie_que_les_siennes(self, _):
        pk = self.creer().data['id']
        self.client.force_authenticate(self.autre)
        self.assertEqual(self.client.get('/api/pro/ressources').data, [])
        self.assertEqual(self.client.get(f'/api/pro/ressources/{pk}').status_code, 404)
        self.assertEqual(self.client.patch(f'/api/pro/ressources/{pk}', {'titre': 'Piraté'}, format='json').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/pro/ressources/{pk}').status_code, 404)

    def test_une_ressource_publiee_n_est_plus_modifiable_par_le_pro(self, _):
        pk = self.creer().data['id']
        Ressource.objects.filter(pk=pk).update(statut=StatutRessource.PUBLIEE)

        reponse = self.client.patch(f'/api/pro/ressources/{pk}', {'titre': 'Nouveau titre'}, format='json')

        self.assertEqual(reponse.status_code, 403)
        self.assertIn("contactez l'administration", reponse.data['detail'])
        self.assertEqual(self.client.delete(f'/api/pro/ressources/{pk}').status_code, 403)

    # --- Soumission -----------------------------------------------------------

    def test_soumission_sans_charte_refusee(self, _):
        pk = self.creer().data['id']
        reponse = self.soumettre(pk, charte=False)
        self.assertEqual(reponse.status_code, 400)
        self.assertEqual(Ressource.objects.get(pk=pk).statut, StatutRessource.BROUILLON)

    def test_soumission_previent_les_administrateurs(self, _):
        pk = self.creer().data['id']

        reponse = self.soumettre(pk)

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertEqual(reponse.data['statut'], 'EN_ATTENTE')
        self.assertIsNotNone(reponse.data['date_soumission'])
        notification = NotificationEmail.objects.get(destinataire=self.admin)
        self.assertIn('Trois respirations pour décrocher', notification.contenu)
        # Plus modifiable pendant la relecture
        self.assertEqual(self.client.patch(f'/api/pro/ressources/{pk}', {'titre': 'Autre'}, format='json').status_code, 403)

    def test_un_titre_trop_court_ou_un_media_manquant_bloque_la_soumission(self, _):
        pk = self.creer(titre='Court').data['id']
        self.assertIn('8 caractères', self.soumettre(pk).data['detail'])
        pk = self.creer(type_ressource='PODCAST').data['id']
        self.assertIn('fichier audio', self.soumettre(pk).data['detail'])

    # --- Visibilité publique (et donc RAG) -------------------------------------

    def test_le_public_ne_voit_jamais_que_les_ressources_publiees(self, _):
        ids = {}
        for statut in StatutRessource.values:
            pk = self.creer(titre=f'Ressource {statut} assez longue').data['id']
            Ressource.objects.filter(pk=pk).update(statut=statut)
            ids[statut] = pk
        self.client.force_authenticate(None)

        visibles = {r['id'] for r in self.client.get('/api/ressources').data}

        self.assertIn(ids['PUBLIEE'], visibles)
        for statut in ('BROUILLON', 'EN_ATTENTE', 'REFUSEE'):
            self.assertNotIn(ids[statut], visibles)
            self.assertEqual(self.client.get(f'/api/ressources/{ids[statut]}').status_code, 404)

    def test_l_administration_voit_tous_les_statuts_sur_demande(self, _):
        pk = self.creer().data['id']
        self.soumettre(pk)
        self.client.force_authenticate(self.admin)
        self.assertNotIn(pk, {r['id'] for r in self.client.get('/api/ressources').data})
        a_valider = self.client.get('/api/ressources?statut=EN_ATTENTE').data
        self.assertEqual([r['id'] for r in a_valider], [pk])
        self.assertIn(pk, {r['id'] for r in self.client.get('/api/ressources?statut=TOUS').data})

    def test_un_utilisateur_ne_peut_pas_voir_les_brouillons_avec_statut(self, _):
        pk = self.creer().data['id']
        self.client.force_authenticate(Utilisateur.objects.create(email='u@test.sn', nom='U'))
        self.assertNotIn(pk, {r['id'] for r in self.client.get('/api/ressources?statut=TOUS').data})

    # --- Relecture ------------------------------------------------------------

    def test_publier_previent_le_pro_et_reindexe(self, workflow):
        pk = self.creer().data['id']
        self.soumettre(pk)
        self.client.force_authenticate(self.admin)

        reponse = self.client.post(f'/api/ressources/{pk}/publier')

        self.assertEqual(reponse.data['statut'], 'PUBLIEE')
        workflow.assert_called_once_with('ressource-modifiee')
        self.assertTrue(NotificationEmail.objects.filter(destinataire=self.awa, objet__contains='est publiée').exists())
        self.client.force_authenticate(None)
        publique = self.client.get(f'/api/ressources/{pk}').data
        self.assertEqual(publique['auteur'], {'id': self.awa.pk, 'nom': 'Awa Ndiaye', 'specialite_affichee': 'Sophrologue'})

    def test_refuser_exige_un_motif_et_previent_le_pro(self, _):
        pk = self.creer().data['id']
        self.soumettre(pk)
        self.client.force_authenticate(self.admin)

        self.assertEqual(self.client.post(f'/api/ressources/{pk}/refuser', {'motif': 'Non.'}, format='json').status_code, 400)
        reponse = self.client.post(f'/api/ressources/{pk}/refuser', {'motif': 'Retirez le nom du médicament au paragraphe 3.'}, format='json')

        self.assertEqual(reponse.data['statut'], 'REFUSEE')
        notification = NotificationEmail.objects.get(destinataire=self.awa)
        self.assertIn('Retirez le nom du médicament', notification.contenu)
        # Le pro peut corriger puis soumettre à nouveau
        self.client.force_authenticate(self.awa)
        self.assertEqual(self.client.patch(f'/api/pro/ressources/{pk}', {'contenu': 'Corrigé.'}, format='json').status_code, 200)
        self.assertEqual(self.soumettre(pk).data['statut'], 'EN_ATTENTE')

    def test_seule_l_administration_publie_ou_refuse(self, _):
        pk = self.creer().data['id']
        self.assertEqual(self.client.post(f'/api/ressources/{pk}/publier').status_code, 403)

    def test_ce_que_cree_l_administration_est_publie_directement(self, workflow):
        self.client.force_authenticate(self.admin)
        reponse = self.client.post('/api/ressources', {'titre': 'Respirer', 'type_ressource': 'ARTICLE', 'thematique': 'Stress',
                                                       'contenu': '…'}, format='json')
        self.assertEqual(reponse.data['statut'], 'PUBLIEE')
        self.assertIsNone(reponse.data['auteur'])
        workflow.assert_called_once()

    # --- Vidéo et audio -------------------------------------------------------

    def test_une_video_expose_son_identifiant_jamais_le_lien_pour_l_integration(self, _):
        reponse = self.creer(type_ressource='VIDEO', url_video='https://youtu.be/aXItOY0sLRY')
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(reponse.data['video_id'], 'aXItOY0sLRY')
        self.assertEqual(self.soumettre(reponse.data['id']).data['statut'], 'EN_ATTENTE')

    def test_un_brouillon_peut_etre_enregistre_incomplet(self, _):
        reponse = self.creer(titre='', contenu='', thematique='')
        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertIn('8 caractères', self.soumettre(reponse.data['id']).data['detail'])
        pk = self.creer(contenu='').data['id']
        self.assertIn('contenu', self.soumettre(pk).data['detail'])

    def test_une_video_sans_lien_ou_avec_un_autre_lien_est_refusee(self, _):
        # Brouillon possible sans lien, mais pas de soumission
        pk = self.creer(type_ressource='VIDEO').data['id']
        self.assertIn('lien YouTube', self.soumettre(pk).data['detail'])
        reponse = self.creer(type_ressource='VIDEO', url_video='https://vimeo.com/123456')
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('Seuls les liens YouTube sont acceptés', str(reponse.data['url_video']))

    def test_le_pro_joint_le_fichier_audio_de_son_podcast(self, _):
        pk = self.creer(type_ressource='PODCAST').data['id']
        fichier = SimpleUploadedFile('episode.mp3', MP3, content_type='audio/mpeg')

        reponse = self.client.patch(f'/api/pro/ressources/{pk}', {'fichier_audio': fichier}, format='multipart')

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.assertIn('/media/audio/episode', reponse.data['audio'])
        self.assertEqual(self.soumettre(pk).data['statut'], 'EN_ATTENTE')

    def test_un_fichier_audio_trop_lourd_ou_d_un_autre_format_est_refuse(self, _):
        pk = self.creer(type_ressource='PODCAST').data['id']
        png = SimpleUploadedFile('image.png', b'\x89PNG' + b'\x00' * 64, content_type='image/png')
        self.assertEqual(self.client.patch(f'/api/pro/ressources/{pk}', {'fichier_audio': png}, format='multipart').status_code, 400)
        with override_settings(FICHIER_AUDIO_MAX_OCTETS=10):
            lourd = SimpleUploadedFile('episode.mp3', MP3, content_type='audio/mpeg')
            self.assertEqual(self.client.patch(f'/api/pro/ressources/{pk}', {'fichier_audio': lourd}, format='multipart').status_code, 400)
