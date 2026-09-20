"""Données de test (docs/SPECIFICATIONS.md section 5).

Une commande de gestion plutôt qu'une fixture JSON : les mots de passe
doivent être hachés via set_password() et les pseudonymes générés/forcés
via save(), ce que loaddata ne permet pas proprement sur un modèle
d'authentification personnalisé en héritage multi-table.

Idempotente : peut être relancée sans dupliquer les données (get_or_create
sur les clés naturelles : email, titre, nom+ville).
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.comptes.models import Administrateur, Professionnel, StatutValidationPro, Utilisateur
from apps.forum.models import CommentaireForum, PublicationForum, StatutModeration, ThematiqueForum
from apps.ressources.contenus_demo import LIEUX as LIEUX_DETAILS, RESSOURCES as RESSOURCES_DEMO
from apps.ressources.models import LieuDetente, Ressource
from apps.suivi.models import (
    AutoEvaluation,
    NiveauHumeur,
    OptionReponse,
    QuestionEvaluation,
    SuiviHumeur,
    TypeEvaluation,
)

MOT_DE_PASSE_DEMO = 'SenSuivi2026!'

OPTIONS_STANDARD = [
    ('Jamais', 0),
    ('Rarement', 1),
    ('Parfois', 2),
    ('Souvent', 3),
    ('Presque tout le temps', 4),
]

QUESTIONS_PAR_TYPE = {
    TypeEvaluation.STRESS: [
        "Depuis quelques jours, avez-vous l'impression de courir après le temps ?",
        "Ressentez-vous une tension dans le corps (épaules, mâchoire, nuque) sans effort particulier ?",
        "Les petits imprévus du quotidien vous semblent-ils plus difficiles à gérer que d'habitude ?",
        "Avez-vous du mal à vous concentrer sur une seule tâche à la fois ?",
        "Ressentez-vous le besoin de vous isoler pour retrouver votre calme ?",
        "Votre sommeil est-il perturbé par des pensées liées à vos obligations ?",
        "Avez-vous l'impression que vos responsabilités s'accumulent plus vite que vous ne pouvez les traiter ?",
        "Ressentez-vous de l'irritabilité face à des situations qui ne vous dérangeaient pas auparavant ?",
    ],
    TypeEvaluation.ANXIETE: [
        "Anticipez-vous souvent le pire avant même qu'une situation ne se présente ?",
        "Ressentez-vous une boule au ventre à l'idée de certains rendez-vous ou échéances ?",
        "Avez-vous du mal à rester en place, comme si quelque chose n'allait pas ?",
        "Vos pensées tournent-elles en boucle autour d'une même inquiétude ?",
        "Évitez-vous certaines situations par peur de ne pas y arriver ?",
        "Votre respiration se fait-elle plus courte dans les moments de doute ?",
        "Avez-vous besoin d'être rassuré·e plus souvent que d'habitude ?",
        "Les incertitudes de la vie quotidienne vous semblent-elles difficiles à supporter ?",
    ],
    TypeEvaluation.FATIGUE: [
        "Vous réveillez-vous déjà fatigué·e, même après une nuit complète ?",
        "Avez-vous besoin de plus de temps que d'habitude pour démarrer votre journée ?",
        "Les tâches simples vous demandent-elles plus d'énergie que d'ordinaire ?",
        "Ressentez-vous une baisse de motivation pour des activités que vous appréciez ?",
        "Votre corps vous semble-t-il plus lourd ou plus lent que d'habitude ?",
        "Avez-vous besoin de vous reposer plusieurs fois dans la journée ?",
        "Votre attention se relâche-t-elle plus vite qu'avant en fin de journée ?",
        "Ressentez-vous un épuisement qu'une bonne nuit de sommeil ne suffit pas à effacer ?",
    ],
}

PROFESSIONNELS = [
    ('Aminata Ba', 'Psychologue', 'Dakar Point E', 'français, wolof', 15000, StatutValidationPro.VALIDE),
    ('Moussa Diop', 'Médiateur familial', 'Thiès', 'français, sérère', 12000, StatutValidationPro.VALIDE),
    ('Sokhna Mbaye', 'Sophrologue', 'Mbour', 'français, wolof', 10000, StatutValidationPro.VALIDE),
    ('Ousmane Sow', 'Coach sportif', 'Dakar Ouakam', 'français', 8000, StatutValidationPro.VALIDE),
    ('Ndèye Coumba Diallo', 'Assistant social', 'Saint-Louis', 'français', 9000, StatutValidationPro.EN_ATTENTE),
    ('Ibrahima Kane', 'Coach en développement personnel', 'Ziguinchor', 'français', 11000, StatutValidationPro.EN_ATTENTE),
]

LIEUX = [
    ('Plage de Ngor', 'Dakar', 'Plage'),
    ('Île de Gorée', 'Dakar', 'Île'),
    ('Lac Rose', 'Niayes', 'Site naturel'),
    ('Parc Forestier de Hann', 'Dakar', 'Parc'),
    ('Lagune de la Somone', 'Mbour', 'Lagune'),
    ('Corniche Ouest', 'Dakar', 'Site naturel'),
    ('Popenguine', 'Thiès', 'Plage'),
    ('Toubab Dialaw', 'Thiès', 'Plage'),
]

PUBLICATIONS_FORUM = [
    {
        'pseudonyme': 'Teranga221',
        'titre': "Parler ici m'aide déjà à y voir plus clair",
        'contenu': "Je traverse une période difficile en ce moment et j'ai l'impression que ce forum m'aide déjà à y voir plus clair. Merci à celles et ceux qui prennent le temps de répondre.",
        'thematique': ThematiqueForum.STRESS,
        'statut': StatutModeration.VISIBLE,
        'commentaires': [
            ('Jàmm_rekk', "Content de lire ça. Le simple fait d'écrire ce qu'on ressent aide déjà beaucoup.", StatutModeration.VISIBLE),
            ('Soleil_de_Thiès', "Courage à vous, cet espace est justement fait pour ça.", StatutModeration.VISIBLE),
        ],
    },
    {
        'pseudonyme': 'Jàmm_rekk',
        'titre': 'Conseils pour mieux dormir avant les examens ?',
        'contenu': "Quelqu'un a des conseils pour mieux dormir avant les examens ? Je me couche fatigué mais j'ai du mal à trouver le sommeil.",
        'thematique': ThematiqueForum.SOMMEIL,
        'statut': StatutModeration.VISIBLE,
        'commentaires': [
            ('Etudiante_UCAD', "Éviter l'écran une heure avant de dormir m'a beaucoup aidé, personnellement.", StatutModeration.VISIBLE),
        ],
    },
    {
        'pseudonyme': 'Etudiante_UCAD',
        'titre': 'La charge de travail est énorme ce semestre',
        'contenu': "La charge de travail est énorme ce semestre, je me sens débordée. J'aimerais savoir comment les autres organisent leur temps.",
        'thematique': ThematiqueForum.TRAVAIL,
        'statut': StatutModeration.VISIBLE,
        'commentaires': [],
    },
    {
        'pseudonyme': 'Soleil_de_Thiès',
        'titre': "Une petite marche le soir m'a beaucoup aidé",
        'contenu': "Une petite marche le soir m'a beaucoup aidé cette semaine. Je la recommande à qui se sent tendu en rentrant du travail.",
        'thematique': ThematiqueForum.STRESS,
        'statut': StatutModeration.VISIBLE,
        'commentaires': [],
    },
    {
        'pseudonyme': 'Sama_xel',
        'titre': 'Message retiré par la modération',
        'contenu': 'Message retiré par la modération.',
        'thematique': ThematiqueForum.RELATIONS,
        'statut': StatutModeration.MASQUE,
        'commentaires': [],
    },
    {
        'pseudonyme': 'Anonyme_Dakar',
        'titre': "Je viens de m'inscrire",
        'contenu': "Je viens de m'inscrire, je découvre encore la plateforme. Bonjour à toutes et à tous.",
        'thematique': ThematiqueForum.RELATIONS,
        'statut': StatutModeration.EN_ATTENTE,
        'commentaires': [],
    },
]


class Command(BaseCommand):
    help = "Crée les données de test de docs/SPECIFICATIONS.md (professionnels, lieux, ressources, comptes, forum, questions)."

    def handle(self, *args, **options):
        self._creer_questions()
        professionnel_valide = self._creer_professionnels()
        self._creer_lieux()
        self._creer_ressources()
        utilisateur_demo = self._creer_comptes_demo(professionnel_valide)
        self._creer_forum(utilisateur_demo)
        self.stdout.write(self.style.SUCCESS('Données de test créées.'))
        self.stdout.write(f"Mot de passe de tous les comptes de démonstration : {MOT_DE_PASSE_DEMO}")

    def _creer_questions(self):
        for type_evaluation, questions in QUESTIONS_PAR_TYPE.items():
            for ordre, libelle in enumerate(questions, start=1):
                question, _ = QuestionEvaluation.objects.get_or_create(
                    type_evaluation=type_evaluation,
                    ordre=ordre,
                    defaults={'libelle': libelle},
                )
                for libelle_option, valeur in OPTIONS_STANDARD:
                    OptionReponse.objects.get_or_create(
                        question=question, valeur=valeur, defaults={'libelle': libelle_option}
                    )

    def _creer_professionnels(self):
        professionnel_valide = None
        for nom, specialite_libelle, ville, langue, tarif, statut in PROFESSIONNELS:
            specialite = {
                'Psychologue': 'PSYCHOLOGUE',
                'Assistant social': 'ASSISTANT_SOCIAL',
                'Coach en développement personnel': 'COACH_DEVELOPPEMENT',
                'Sophrologue': 'SOPHROLOGUE',
                'Médiateur familial': 'MEDIATEUR_FAMILIAL',
                'Coach sportif': 'COACH_SPORTIF',
            }[specialite_libelle]
            email = f"{nom.lower().replace(' ', '.').replace('è', 'e').replace('é', 'e')}@sensuivi.sn"
            professionnel, cree = Professionnel.objects.get_or_create(
                email=email,
                defaults={
                    'nom': nom,
                    'specialite': specialite,
                    'ville': ville,
                    'langue': langue,
                    'tarif_indicatif': tarif,
                    'statut_validation': statut,
                },
            )
            if cree:
                professionnel.set_password(MOT_DE_PASSE_DEMO)
                professionnel.save()
            if statut == StatutValidationPro.VALIDE and professionnel_valide is None:
                professionnel_valide = professionnel
        return professionnel_valide

    def _creer_lieux(self):
        for nom, ville, categorie in LIEUX:
            details = LIEUX_DETAILS.get(nom, {})
            LieuDetente.objects.update_or_create(
                nom=nom, ville=ville,
                defaults={'categorie': categorie, 'description': details.get('description', f'{nom}, {ville}.'),
                          'latitude': details.get('latitude'), 'longitude': details.get('longitude'),
                          'acces_libre': details.get('acces_libre', True)},
            )

    def _creer_ressources(self):
        for ressource in RESSOURCES_DEMO:
            Ressource.objects.update_or_create(
                titre=ressource['titre'],
                defaults={cle: valeur for cle, valeur in ressource.items() if cle != 'titre'},
            )

    def _creer_comptes_demo(self, professionnel_valide):
        utilisateur, cree = Utilisateur.objects.get_or_create(
            email='awa.ndiaye@sensuivi.sn',
            defaults={'nom': 'Ndiaye', 'prenom': 'Awa'},
        )
        if cree:
            utilisateur.set_password(MOT_DE_PASSE_DEMO)
            utilisateur.save()

            aujourdhui = timezone.localdate()
            humeurs = list(NiveauHumeur.values)
            for decalage in range(14):
                SuiviHumeur.objects.create(
                    utilisateur=utilisateur,
                    date=aujourdhui - timedelta(days=decalage),
                    score_humeur=humeurs[decalage % len(humeurs)],
                    note='',
                )

            for type_evaluation, score in [(TypeEvaluation.STRESS, 45), (TypeEvaluation.FATIGUE, 62)]:
                AutoEvaluation.objects.create(
                    utilisateur=utilisateur,
                    type_evaluation=type_evaluation,
                    score_de_tendance=score,
                )

        admin, cree = Administrateur.objects.get_or_create(
            email='admin@sensuivi.sn',
            defaults={'nom': 'Administrateur', 'is_staff': True, 'is_superuser': True},
        )
        if cree:
            admin.set_password(MOT_DE_PASSE_DEMO)
            admin.save()

        return utilisateur

    def _creer_forum(self, utilisateur_demo):
        for donnee in PUBLICATIONS_FORUM:
            auteur = self._compte_forum(donnee['pseudonyme'])
            publication, _ = PublicationForum.objects.get_or_create(
                utilisateur=auteur,
                titre=donnee['titre'],
                defaults={
                    'contenu': donnee['contenu'],
                    'thematique': donnee['thematique'],
                    'statut_moderation': donnee['statut'],
                },
            )
            for pseudonyme_commentateur, contenu, statut in donnee['commentaires']:
                commentateur = self._compte_forum(pseudonyme_commentateur)
                CommentaireForum.objects.get_or_create(
                    publication=publication,
                    utilisateur=commentateur,
                    contenu=contenu,
                    defaults={'statut_moderation': statut},
                )

    def _compte_forum(self, pseudonyme):
        """Un compte Utilisateur de démonstration, avec ce pseudonyme précis."""
        auteur, cree = Utilisateur.objects.get_or_create(
            email=f'{pseudonyme.lower()}@sensuivi.sn',
            defaults={'nom': pseudonyme, 'prenom': pseudonyme},
        )
        if cree:
            auteur.set_password(MOT_DE_PASSE_DEMO)
            auteur.pseudonyme = pseudonyme
            auteur.save()
        return auteur
