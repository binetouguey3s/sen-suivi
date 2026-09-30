from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.permissions import EstUtilisateur
from apps.comptes.serializers import ProfessionnelPublicSerializer

from .acces import etat_acces
from .models import AccesMiseEnRelation
from .paiement import prestataire_actif
from .serializers import DemandePaiementSerializer, SuggestionSerializer
from .services import classer, suggerer
from .urgence import en_detresse


class SuggestionView(APIView):
    """GET /api/orientation/suggestion?langue=wolof&ville=Dakar

    UN professionnel mis en avant, avec la phrase qui explique ce choix, PUIS
    la liste complète de tous les professionnels validés : la suggestion
    n'enferme jamais le choix, et l'ignorer ne demande aucune justification.
    """

    permission_classes = [EstUtilisateur]

    def get(self, request):
        utilisateur = request.user.utilisateur
        langue = request.query_params.get('langue') or None
        ville = request.query_params.get('ville') or None
        suggestion = suggerer(utilisateur, langue=langue, ville=ville)
        tous = [s.professionnel for s in classer([], langue, ville or utilisateur.ville or None)]
        tous.sort(key=lambda p: (p.ville, p.nom))
        return Response({
            'suggestion': SuggestionSerializer(suggestion).data if suggestion else None,
            'professionnels': ProfessionnelPublicSerializer(tous, many=True).data,
        })


class EtatAccesView(APIView):
    """GET /api/acces/etat — offre en cours, jours restants, accès verrouillé.

    Avec un jeton d'urgence valide (en-tête X-Jeton-Urgence) : ni compteur, ni
    verrou, ni tarif.
    """

    permission_classes = [EstUtilisateur]

    def get(self, request):
        return Response(etat_acces(request.user.utilisateur, en_detresse(request)))


class PaiementView(APIView):
    """POST /api/acces/paiement — point d'entrée du futur paiement mobile money.

    Tant qu'aucun prestataire n'est branché, la demande est refusée proprement
    (503) sans rien enregistrer. Une fois branché : un accès EN_ATTENTE est
    créé, le prestataire envoie la demande de paiement sur le téléphone, et sa
    confirmation passera l'accès à ACTIF.
    """

    permission_classes = [EstUtilisateur]

    def post(self, request):
        serializer = DemandePaiementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prestataire = prestataire_actif()
        if prestataire is None:
            return Response(
                {'detail': "Le paiement mobile money arrive très bientôt. En attendant, écrivez-nous depuis la "
                           "page Contact : nous trouverons une solution ensemble."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        acces = AccesMiseEnRelation.objects.create(
            utilisateur=request.user.utilisateur,
            moyen=serializer.validated_data['moyen'],
            date_fin=timezone.localdate() + timedelta(days=settings.ACCES_DUREE_JOURS - 1),
        )
        acces.reference = prestataire.initier(acces, serializer.validated_data['telephone'])
        acces.save(update_fields=['reference'])
        return Response({'id': acces.pk, 'statut': acces.statut}, status=status.HTTP_202_ACCEPTED)
