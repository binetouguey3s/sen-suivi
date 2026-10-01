"""Personne de confiance : l'utilisateur peut la faire prévenir en un geste.

Règles :
- jamais d'alerte automatique : c'est toujours l'utilisateur qui décide ;
- seulement en situation de détresse détectée (jeton d'urgence valide) ;
- aucun contenu de conversation transmis, seulement l'invitation à prendre
  des nouvelles et les numéros d'urgence ;
- par défaut, l'utilisateur appelle ou envoie un SMS depuis SON téléphone : rien
  ne transite par Sen Suivi. L'e-mail automatique (n8n) est une option.
"""

import re
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.services import declencher_workflow
from apps.orientation.urgence import en_detresse

from .models import AlerteConfiance, PersonneConfiance
from .permissions import EstUtilisateur

# Une seule alerte e-mail par période : on ne submerge jamais la personne
ALERTE_INTERVALLE_MINUTES = 30


def message_alerte(prenom_utilisateur: str) -> str:
    """Texte proposé pour le SMS ou envoyé par e-mail : sans aucun détail des échanges."""
    return (
        f"Bonjour, c'est {prenom_utilisateur}. Je traverse un moment très difficile et j'aimerais que tu prennes "
        "de mes nouvelles dès que possible. Si tu penses que je suis en danger, appelle le 1515 (SAMU) ou le 18. "
        "Numéro vert d'écoute : 800 805 805. (Message envoyé depuis Sen Suivi)"
    )


class PersonneConfianceSerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model = PersonneConfiance
        fields = ['prenom', 'lien', 'telephone', 'email', 'accord_confirme', 'date_mise_a_jour']
        read_only_fields = ['date_mise_a_jour']

    def validate_telephone(self, telephone):
        chiffres = re.sub(r'[\s.\-]', '', telephone)
        if chiffres and not re.fullmatch(r'(\+221|00221)?7[05678]\d{7}|\+?\d{8,15}', chiffres):
            raise serializers.ValidationError('Indiquez un numéro valide (ex. 77 123 45 67).')
        return chiffres

    def validate(self, donnees):
        if not (donnees.get('telephone') or donnees.get('email')):
            raise serializers.ValidationError('Indiquez au moins un téléphone ou un e-mail.')
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
    l'utilisateur : on ne trace que le geste. EMAIL passe par n8n.
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
                declencher_workflow('alerte-personne-confiance', {
                    'destinataire_email': personne.email,
                    'destinataire_prenom': personne.prenom,
                    'objet': f'{utilisateur.prenom} aimerait avoir de vos nouvelles',
                    'message': message_alerte(utilisateur.prenom),
                })
        AlerteConfiance.objects.create(personne=personne, canal=canal)
        return Response({'detail': f'{personne.prenom} va être prévenu·e.' if canal == 'EMAIL' else 'Merci.'}, status=201)
