"""Historique du chatbot : conservation avec consentement, lecture et effacement.

Les confidences faites au chatbot sont des données de santé : elles ne sont
enregistrées que pour un utilisateur connecté qui l'accepte, ne sont lisibles
que par lui, et il peut les effacer à tout moment.
"""

from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comptes.models import Professionnel, StatutValidationPro, Utilisateur
from apps.ressources.models import Ressource
from apps.suivi.models import SuiviHumeur

from .models import ConversationChatbot, MessageChatbot

URL_MESSAGE = '/api/chatbot/message'
URL_CONVERSATIONS = '/api/chatbot/conversations'


def reponse_ia(**extra):
    return {
        'reponse': 'Je vous écoute.',
        'source_reponse': 'REGLE',
        'urgence': False,
        'intention': 'stress',
        'ressource': None,
        **extra,
    }


@patch('apps.chatbot.views.traiter_message')
class ConservationTests(APITestCase):
    def setUp(self):
        self.utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.ressource = Ressource.objects.create(
            titre='Respirer avant un examen', type_ressource='EXERCICE', contenu='…', thematique='Respiration'
        )

    def test_rien_n_est_enregistre_sans_consentement(self, traiter):
        traiter.return_value = reponse_ia()
        self.client.force_authenticate(self.utilisateur)

        reponse = self.client.post(URL_MESSAGE, {'message': 'Bonjour'})

        self.assertEqual(reponse.status_code, 200)
        self.assertIsNone(reponse.data['conversation_id'])
        self.assertFalse(MessageChatbot.objects.exists())

    def test_rien_n_est_enregistre_pour_un_visiteur(self, traiter):
        traiter.return_value = reponse_ia()

        self.client.post(URL_MESSAGE, {'message': 'Bonjour', 'consentement_conservation': True})

        self.assertFalse(ConversationChatbot.objects.exists())

    def test_avec_consentement_la_reponse_garde_urgence_et_ressource(self, traiter):
        traiter.return_value = reponse_ia(
            urgence=True,
            ressource={'ressource_id': self.ressource.pk, 'titre': self.ressource.titre, 'thematique': 'Respiration'},
        )
        self.client.force_authenticate(self.utilisateur)

        reponse = self.client.post(URL_MESSAGE, {'message': 'Je panique', 'consentement_conservation': True})

        conversation = ConversationChatbot.objects.get(pk=reponse.data['conversation_id'])
        utilisateur, bot = conversation.messages.order_by('id')
        self.assertEqual((utilisateur.type_expediteur, utilisateur.contenu), ('UTILISATEUR', 'Je panique'))
        self.assertTrue(bot.urgence)
        self.assertEqual(bot.ressource, self.ressource)

    def test_l_historique_est_transmis_au_microservice_sans_etre_enregistre(self, traiter):
        traiter.return_value = reponse_ia()
        historique = [{'auteur': 'UTILISATEUR', 'contenu': 'Bonjour'}, {'auteur': 'BOT', 'contenu': 'Bonjour !'}]

        self.client.post(URL_MESSAGE, {'message': 'Ça va', 'historique': historique}, format='json')

        traiter.assert_called_once_with('Ça va', historique, None, False)
        self.assertFalse(MessageChatbot.objects.exists())

    def test_une_reponse_generee_par_le_modele_est_conservee(self, traiter):
        traiter.return_value = reponse_ia(source_reponse='GENERATION', reponse='Réponse encadrée.')
        self.client.force_authenticate(self.utilisateur)

        self.client.post(URL_MESSAGE, {'message': 'Bonjour', 'consentement_conservation': True})

        bot = MessageChatbot.objects.get(type_expediteur='BOT')
        self.assertEqual((bot.source_reponse, bot.contenu), ('GENERATION', 'Réponse encadrée.'))

    def test_une_ressource_inconnue_n_empeche_pas_l_enregistrement(self, traiter):
        traiter.return_value = reponse_ia(ressource={'ressource_id': 9999, 'titre': 'Supprimée', 'thematique': 'X'})
        self.client.force_authenticate(self.utilisateur)

        self.client.post(URL_MESSAGE, {'message': 'Bonjour', 'consentement_conservation': True})

        self.assertIsNone(MessageChatbot.objects.get(type_expediteur='BOT').ressource)


@patch('apps.chatbot.views.traiter_message')
class PersonnalisationTests(APITestCase):
    """Le profil de tendance n'est transmis qu'avec un consentement explicite."""

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        SuiviHumeur.objects.create(utilisateur=self.utilisateur, date=timezone.localdate(), score_humeur='MAL', note='Mon secret')
        self.client.force_authenticate(self.utilisateur)

    def _profil_transmis(self, traiter):
        traiter.return_value = reponse_ia()
        self.client.post(URL_MESSAGE, {'message': 'Bonjour'})
        return traiter.call_args.args[2]

    def test_sans_consentement_aucun_profil_n_est_transmis(self, traiter):
        self.assertIsNone(self._profil_transmis(traiter))

    def test_avec_consentement_seuls_des_mots_cles_sont_transmis(self, traiter):
        self.utilisateur.preferences = {'personnalisation_chatbot': True}
        self.utilisateur.save()

        profil = self._profil_transmis(traiter)

        self.assertEqual(profil, ['journal irrégulier'])
        texte = ' '.join(profil)
        for donnee_brute in ('Mon secret', 'Awa', 'Diop', 'awa@test.sn'):
            self.assertNotIn(donnee_brute, texte)

    def test_un_consentement_retire_coupe_la_personnalisation(self, traiter):
        self.utilisateur.preferences = {'personnalisation_chatbot': False}
        self.utilisateur.save()

        self.assertIsNone(self._profil_transmis(traiter))

    def test_un_profil_indisponible_ne_bloque_jamais_la_reponse(self, traiter):
        self.utilisateur.preferences = {'personnalisation_chatbot': True}
        self.utilisateur.save()

        with patch('apps.chatbot.views.profil_tendance', side_effect=RuntimeError('panne')):
            self.assertIsNone(self._profil_transmis(traiter))

    def test_un_visiteur_n_a_jamais_de_profil(self, traiter):
        self.client.force_authenticate(None)

        self.assertIsNone(self._profil_transmis(traiter))


@patch('apps.chatbot.views.traiter_message')
class HistoriqueTests(APITestCase):
    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.moussa = Utilisateur.objects.create(email='moussa@test.sn', nom='Fall', prenom='Moussa')

    def conversation_de(self, utilisateur, *messages, consentement=True):
        conversation = ConversationChatbot.objects.create(utilisateur=utilisateur, consentement_conservation=consentement)
        for auteur, contenu in messages:
            MessageChatbot.objects.create(conversation=conversation, type_expediteur=auteur, contenu=contenu)
        return conversation

    def test_liste_uniquement_mes_conversations_de_la_plus_recente_a_la_plus_ancienne(self, traiter):
        ancienne = self.conversation_de(self.awa, ('UTILISATEUR', 'Je dors mal'), ('BOT', 'Depuis quand ?'))
        recente = self.conversation_de(self.awa, ('UTILISATEUR', 'Je suis stressée ' + 'x' * 100))
        self.conversation_de(self.moussa, ('UTILISATEUR', 'Message de Moussa'))
        self.conversation_de(self.awa)  # vide : pas dans la liste
        self.client.force_authenticate(self.awa)

        reponse = self.client.get(URL_CONVERSATIONS)

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual([c['id'] for c in reponse.data], [recente.pk, ancienne.pk])
        self.assertEqual(reponse.data[1]['apercu'], 'Je dors mal')
        self.assertEqual(reponse.data[1]['nombre_messages'], 2)
        self.assertTrue(reponse.data[0]['apercu'].endswith('…'))
        self.assertLessEqual(len(reponse.data[0]['apercu']), 81)

    def test_lit_une_conversation_dans_l_ordre(self, traiter):
        conversation = self.conversation_de(self.awa, ('UTILISATEUR', 'Bonjour'), ('BOT', 'Naka nga def ?'))
        self.client.force_authenticate(self.awa)

        reponse = self.client.get(f'{URL_CONVERSATIONS}/{conversation.pk}')

        self.assertEqual(reponse.status_code, 200)
        self.assertEqual([(m['auteur'], m['contenu']) for m in reponse.data['messages']], [('UTILISATEUR', 'Bonjour'), ('BOT', 'Naka nga def ?')])

    def test_la_conversation_d_un_autre_compte_est_introuvable(self, traiter):
        conversation = self.conversation_de(self.moussa, ('UTILISATEUR', 'Confidence'))
        self.client.force_authenticate(self.awa)

        self.assertEqual(self.client.get(f'{URL_CONVERSATIONS}/{conversation.pk}').status_code, 404)
        self.assertEqual(self.client.delete(f'{URL_CONVERSATIONS}/{conversation.pk}').status_code, 404)
        self.assertTrue(ConversationChatbot.objects.filter(pk=conversation.pk).exists())

    def test_une_conversation_sans_consentement_n_apparait_pas(self, traiter):
        conversation = self.conversation_de(self.awa, ('UTILISATEUR', 'Non conservé'), consentement=False)
        self.client.force_authenticate(self.awa)

        self.assertEqual(self.client.get(URL_CONVERSATIONS).data, [])
        self.assertEqual(self.client.get(f'{URL_CONVERSATIONS}/{conversation.pk}').status_code, 404)

    def test_effacer_supprime_la_conversation_et_ses_messages(self, traiter):
        conversation = self.conversation_de(self.awa, ('UTILISATEUR', 'À effacer'), ('BOT', 'Réponse'))
        self.client.force_authenticate(self.awa)

        reponse = self.client.delete(f'{URL_CONVERSATIONS}/{conversation.pk}')

        self.assertEqual(reponse.status_code, 204)
        self.assertFalse(ConversationChatbot.objects.filter(pk=conversation.pk).exists())
        self.assertFalse(MessageChatbot.objects.filter(conversation_id=conversation.pk).exists())

    def test_reserve_aux_comptes_utilisateur(self, traiter):
        professionnel = Professionnel.objects.create(
            email='pro@test.sn', nom='Test Pro', specialite='PSYCHOLOGUE', ville='Dakar',
            langue='français', tarif_indicatif=10000, statut_validation=StatutValidationPro.VALIDE,
        )
        self.assertIn(self.client.get(URL_CONVERSATIONS).status_code, (401, 403))
        self.client.force_authenticate(professionnel)
        self.assertEqual(self.client.get(URL_CONVERSATIONS).status_code, 403)


@patch('apps.chatbot.views.traiter_message')
class ConsentementEnCoursDeConversationTests(APITestCase):
    """Cocher « Conserver cet échange » en cours de route enregistre aussi ce qui précède."""

    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.ressource = Ressource.objects.create(
            titre='Dormir mieux', type_ressource='ARTICLE', contenu='…', thematique='Sommeil'
        )
        self.client.force_authenticate(self.awa)

    def test_enregistre_les_messages_deja_echanges_puis_la_suite(self, traiter):
        traiter.return_value = reponse_ia(reponse='Parlons de votre sommeil.')
        anterieurs = [
            {'auteur': 'UTILISATEUR', 'contenu': 'Je dors mal'},
            {'auteur': 'BOT', 'contenu': 'Voici un article.', 'ressource_id': self.ressource.pk},
        ]

        creation = self.client.post(URL_CONVERSATIONS, {'messages': anterieurs}, format='json')
        self.assertEqual(creation.status_code, 201)
        self.client.post(
            URL_MESSAGE,
            {'message': 'Merci', 'conversation_id': creation.data['id'], 'consentement_conservation': True},
            format='json',
        )

        messages = self.client.get(f"{URL_CONVERSATIONS}/{creation.data['id']}").data['messages']
        self.assertEqual(
            [m['contenu'] for m in messages],
            ['Je dors mal', 'Voici un article.', 'Merci', 'Parlons de votre sommeil.'],
        )
        self.assertEqual(messages[1]['ressource']['titre'], 'Dormir mieux')

    def test_une_ressource_ou_une_urgence_sur_un_message_utilisateur_est_ignoree(self, traiter):
        creation = self.client.post(
            URL_CONVERSATIONS,
            {'messages': [{'auteur': 'UTILISATEUR', 'contenu': 'Test', 'urgence': True, 'ressource_id': self.ressource.pk}]},
            format='json',
        )

        message = MessageChatbot.objects.get(conversation_id=creation.data['id'])
        self.assertFalse(message.urgence)
        self.assertIsNone(message.ressource)

    def test_refuse_une_liste_vide_ou_trop_longue(self, traiter):
        vide = self.client.post(URL_CONVERSATIONS, {'messages': []}, format='json')
        trop = self.client.post(
            URL_CONVERSATIONS, {'messages': [{'auteur': 'BOT', 'contenu': 'x'}] * 51}, format='json'
        )

        self.assertEqual(vide.status_code, 400)
        self.assertEqual(trop.status_code, 400)
        self.assertFalse(ConversationChatbot.objects.exists())
