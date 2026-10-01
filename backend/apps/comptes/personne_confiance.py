"""Personne de confiance : l'utilisateur peut la faire prévenir en un geste.

Règles :
- jamais d'alerte automatique : c'est toujours l'utilisateur qui décide ;
- seulement en situation de détresse détectée (jeton d'urgence valide) ;
- aucun contenu de conversation transmis, seulement l'invitation à prendre
  des nouvelles et les numéros d'urgence ;
- par défaut, l'utilisateur appelle ou envoie un SMS depuis SON téléphone : rien
  ne transite par Sen Suivi. L'e-mail, envoyé par le serveur SMTP du .env, est
  une option.
"""

import re
import unicodedata
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.courriel import envoyer
from apps.orientation.urgence import en_detresse

from .models import AlerteConfiance, PersonneConfiance
from .permissions import EstUtilisateur

# Une seule alerte e-mail par période : on ne submerge jamais la personne
ALERTE_INTERVALLE_MINUTES = 30
# Alerte automatique : au plus une toutes les 6 heures
ALERTE_AUTO_INTERVALLE_HEURES = 6


def message_alerte(prenom_utilisateur: str) -> str:
    """Texte proposé pour le SMS ou envoyé par e-mail : sans aucun détail des échanges."""
    return (
        f"Bonjour, c'est {prenom_utilisateur}. Je traverse un moment très difficile et j'aimerais que tu prennes "
        "de mes nouvelles dès que possible. Si tu penses que je suis en danger, appelle le 1515 (SAMU) ou le 18. "
        "Numéro vert d'écoute : 800 805 805. (Message envoyé depuis Sen Suivi)"
    )


# Raison de l'e-mail, selon la situation : claire, sans jamais citer les messages
RAISONS = {
    'RISQUE_VITAL': "a exprimé, dans ses échanges avec l'assistant d'écoute de Sen Suivi, des propos qui laissent "
                    "penser que sa vie pourrait être en danger.",
    'DANGER_AUTRUI': "a exprimé, dans ses échanges avec l'assistant d'écoute de Sen Suivi, une colère ou une détresse "
                     "très forte, avec des propos qui laissent craindre un passage à l'acte dangereux (violence, "
                     "incendie…), pour elle-même ou pour son entourage.",
}
# Natures pour lesquelles la personne de confiance peut être prévenue automatiquement.
# Jamais pour des violences subies : l'auteur des violences peut être un proche.
NATURES_ALERTE_AUTOMATIQUE = tuple(RAISONS)


def message_accompagnement(prenom_utilisateur: str, prenom_personne: str, nature: str | None = None) -> str:
    """E-mail à la personne de confiance : pourquoi elle est prévenue, et comment
    être présente sans blesser. Jamais le contenu des échanges."""
    p = prenom_utilisateur
    if nature in RAISONS:
        moment = timezone.localtime().strftime('%d/%m/%Y à %H h %M')
        raison = (
            f"{p} vous a désigné·e comme personne de confiance sur Sen Suivi et a accepté, à l'avance, que vous "
            f"soyez prévenu·e automatiquement dans une situation grave. Aujourd'hui ({moment}), {p} {RAISONS[nature]} "
            f"Nous vous écrivons donc pour que {p} ne reste pas seul·e."
        )
    else:
        raison = (
            f"{p} vous a désigné·e comme personne de confiance sur Sen Suivi. Aujourd'hui, {p} traverse un moment "
            "très difficile et a demandé à ce que vous soyez prévenu·e."
        )
    conseils = [
        f"Prenez contact avec {p} dès que possible : un appel, un message, une visite.",
        "Écoutez sans juger et sans faire de reproches. Laissez parler, même s'il y a des silences.",
        "Ne minimisez pas ce qui est ressenti : « ce n'est rien », « pense à ta famille » ou « tu exagères » "
        "peuvent blesser, même avec de bonnes intentions.",
        f"Dites simplement que vous êtes là, que {p} compte pour vous, et que vous voulez aider.",
        "Proposez d'appeler ensemble le 800 805 805 (numéro vert d'écoute, gratuit).",
    ]
    if nature == 'DANGER_AUTRUI':
        conseils.append(
            "Si vous pensez qu'un passage à l'acte est imminent, appelez le 18 (sapeurs-pompiers) ou le 1515 (SAMU). "
            "Ne vous mettez pas vous-même en danger, et éloignez si possible les personnes exposées."
        )
    else:
        conseils.append(f"Si vous pensez que {p} est en danger immédiat, appelez le 1515 (SAMU) ou le 18, et restez à ses côtés.")
    return (
        f"Bonjour {prenom_personne},\n\n{raison}\n\nCe que vous pouvez faire, dès maintenant :\n"
        + '\n'.join(f'- {c}' for c in conseils)
        + f"\n\nPour respecter la confiance de {p}, le contenu exact de ses échanges sur Sen Suivi reste confidentiel."
    )


def _normaliser(texte: str) -> str:
    # « œ » et « æ » ne se décomposent pas : « Sœur » deviendrait « sur »
    texte = (texte or '').replace('œ', 'oe').replace('Œ', 'Oe').replace('æ', 'ae').replace('Æ', 'Ae')
    return unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii').lower()


def personne_visee(personne, textes: list[str]) -> bool:
    """Le message parle-t-il de la personne de confiance elle-même (son prénom,
    ou son lien : « père », « mari »…) ? Alors elle pourrait être la personne visée."""
    contenu = ' ' + re.sub(r'[^a-z]+', ' ', _normaliser(' '.join(textes))) + ' '
    reperes = [m for m in re.split(r'\s+', _normaliser(personne.prenom)) if len(m) >= 3]
    reperes += [m for m in re.split(r'[^a-z]+', _normaliser(personne.lien)) if len(m) >= 3]
    return any(f' {r} ' in contenu for r in reperes)


def alerter_automatiquement(utilisateur, nature: str, textes: list[str]) -> str | None:
    """Situation grave (risque vital, danger pour autrui) : prévient la personne de
    confiance par e-mail, si l'utilisateur l'a accepté à l'avance et si le message
    ne la vise pas elle-même. Renvoie son prénom si elle est prévenue."""
    from apps.notifications.courriel import envoyer_en_arriere_plan

    if nature not in NATURES_ALERTE_AUTOMATIQUE:
        return None
    personne = PersonneConfiance.objects.filter(
        utilisateur=utilisateur, accord_confirme=True, alerte_automatique=True
    ).exclude(email='').first()
    if personne is None or personne_visee(personne, textes):
        return None
    recente = personne.alertes.filter(
        canal__in=['AUTO', 'EMAIL'], date__gte=timezone.now() - timedelta(hours=ALERTE_AUTO_INTERVALLE_HEURES)
    ).exists()
    if not recente:
        # En arrière-plan : la réponse d'urgence ne doit jamais attendre le serveur d'e-mails
        envoyer_en_arriere_plan(
            personne.email,
            f'Urgence : {utilisateur.prenom} a besoin de votre présence',
            message_accompagnement(utilisateur.prenom, personne.prenom, nature),
        )
        AlerteConfiance.objects.create(personne=personne, canal='AUTO')
    return personne.prenom


class PersonneConfianceSerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model = PersonneConfiance
        fields = ['prenom', 'lien', 'telephone', 'email', 'accord_confirme', 'alerte_automatique', 'date_mise_a_jour']
        read_only_fields = ['date_mise_a_jour']

    def validate_telephone(self, telephone):
        chiffres = re.sub(r'[\s.\-]', '', telephone)
        if chiffres and not re.fullmatch(r'(\+221|00221)?7[05678]\d{7}|\+?\d{8,15}', chiffres):
            raise serializers.ValidationError('Indiquez un numéro valide (ex. 77 123 45 67).')
        return chiffres

    def validate(self, donnees):
        if not (donnees.get('telephone') or donnees.get('email')):
            raise serializers.ValidationError('Indiquez au moins un téléphone ou un e-mail.')
        if donnees.get('alerte_automatique') and not donnees.get('email'):
            raise serializers.ValidationError(
                {'alerte_automatique': "L'alerte automatique part par e-mail : indiquez son adresse."}
            )
        if not donnees.get('accord_confirme'):
            raise serializers.ValidationError(
                {'accord_confirme': "Prévenez d'abord cette personne et assurez-vous qu'elle est d'accord."}
            )
        return donnees


class PersonneConfianceView(APIView):
    """GET/PUT/DELETE /api/comptes/moi/personne-confiance"""

    permission_classes = [EstUtilisateur]

    def get(self, request):
        personne = PersonneConfiance.objects.filter(utilisateur=request.user.utilisateur).first()
        if personne is None:
            return Response(None)
        return Response({
            **PersonneConfianceSerializer(personne).data,
            'message_sms': message_alerte(request.user.utilisateur.prenom),
            'alerte_email_disponible': bool(personne.email),
        })

    def put(self, request):
        personne = PersonneConfiance.objects.filter(utilisateur=request.user.utilisateur).first()
        serializer = PersonneConfianceSerializer(personne, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(utilisateur=request.user.utilisateur)
        return self.get(request)

    def delete(self, request):
        PersonneConfiance.objects.filter(utilisateur=request.user.utilisateur).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AlerteConfianceView(APIView):
    """POST /api/comptes/moi/personne-confiance/alerte {canal: APPEL|SMS|EMAIL}

    Seulement à la demande de l'utilisateur, et seulement en situation de
    détresse (jeton d'urgence). APPEL et SMS partent du téléphone de
    l'utilisateur : on ne trace que le geste. EMAIL part tout de suite, et
    l'interface sait s'il est bien parti (sinon, l'appel et le SMS restent là).
    """

    permission_classes = [EstUtilisateur]

    def post(self, request):
        if not en_detresse(request):
            raise PermissionDenied("Cette alerte n'est disponible que depuis l'écran d'aide immédiate.")
        utilisateur = request.user.utilisateur
        personne = PersonneConfiance.objects.filter(utilisateur=utilisateur, accord_confirme=True).first()
        if personne is None:
            raise NotFound("Aucune personne de confiance n'est enregistrée.")
        canal = request.data.get('canal')
        if canal not in ('APPEL', 'SMS', 'EMAIL'):
            raise serializers.ValidationError({'canal': 'Canal inconnu.'})

        if canal == 'EMAIL':
            if not personne.email:
                raise serializers.ValidationError({'canal': "Aucun e-mail n'est enregistré pour cette personne."})
            recente = personne.alertes.filter(
                canal='EMAIL', date__gte=timezone.now() - timedelta(minutes=ALERTE_INTERVALLE_MINUTES)
            ).exists()
            if not recente:
                envoye = envoyer(
                    personne.email,
                    f'{utilisateur.prenom} aimerait avoir de vos nouvelles',
                    message_accompagnement(utilisateur.prenom, personne.prenom),
                )
                if not envoye:
                    return Response(
                        {'detail': "L'e-mail n'a pas pu partir. Appelez ou envoyez un SMS à "
                                   f'{personne.prenom}, ou composez le 800 805 805.'},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
        AlerteConfiance.objects.create(personne=personne, canal=canal)
        return Response({'detail': f'{personne.prenom} va être prévenu·e.' if canal == 'EMAIL' else 'Merci.'}, status=201)
