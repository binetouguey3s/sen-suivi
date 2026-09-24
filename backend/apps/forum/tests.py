"""Directive de sécurité, section 3B : saisies malveillantes sur le forum.

Le back-end ne transforme pas le texte : il l'enregistre tel quel via l'ORM
(requêtes paramétrées) et le renvoie en JSON. L'échappement HTML a lieu à
l'affichage, dans Angular.
"""

from rest_framework.test import APITestCase

from apps.comptes.models import Utilisateur

from .models import PublicationForum, StatutModeration

SCRIPT = '<script>alert("xss")</script>'
INJECTION_SQL = "'; DROP TABLE forum_publicationforum; --"


class SaisiesMalveillantesForumTests(APITestCase):
    url = '/api/forum/publications'

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create(email='moussa@test.sn', nom='Fall', prenom='Moussa')
        self.client.force_authenticate(self.utilisateur)

    def publier_puis_lire(self, titre, contenu):
        reponse = self.client.post(self.url, {'titre': titre, 'contenu': contenu, 'thematique': 'STRESS'})
        self.assertEqual(reponse.status_code, 201)
        PublicationForum.objects.update(statut_moderation=StatutModeration.VISIBLE)
        return self.client.get(self.url)

    def test_script_renvoye_comme_texte_en_json(self):
        reponse = self.publier_puis_lire('Question', SCRIPT)
        self.assertEqual(reponse['Content-Type'], 'application/json')
        publications = reponse.data
        self.assertEqual(publications[0]['contenu'], SCRIPT)

    def test_injection_sql_enregistree_comme_texte(self):
        self.publier_puis_lire(INJECTION_SQL, 'Contenu')
        # La table existe toujours et contient la chaîne telle quelle.
        self.assertTrue(PublicationForum.objects.filter(titre=INJECTION_SQL).exists())

    def test_injection_sql_dans_la_recherche(self):
        self.publier_puis_lire('Stress des examens', 'Contenu')
        reponse = self.client.get(self.url, {'q': "' OR '1'='1"})
        self.assertEqual(reponse.status_code, 200)
        publications = reponse.data
        self.assertEqual(len(publications), 0)
