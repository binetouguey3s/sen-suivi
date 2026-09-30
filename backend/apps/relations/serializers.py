from rest_framework import serializers, status
from rest_framework.exceptions import APIException

from apps.comptes.models import Professionnel, StatutValidationPro
from apps.orientation.acces import peut_demander
from apps.orientation.urgence import en_detresse

from .models import DemandeContact, MessageRelation, StatutDemandeContact


class AccesVerrouille(APIException):
    """Offre de lancement terminée et aucun accès actif : l'interface affiche
    l'écran de déblocage avant l'envoi de la demande."""

    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "La période de mise en relation gratuite est terminée."
    default_code = 'acces_verrouille'


class DemandeContactEcritureSerializer(serializers.ModelSerializer):
    professionnel = serializers.PrimaryKeyRelatedField(
        queryset=Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE)
    )
    message = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    class Meta:
        model = DemandeContact
        fields = ['id', 'professionnel', 'message', 'statut', 'date']
        read_only_fields = ['statut', 'date']

    def validate_professionnel(self, professionnel):
        if not professionnel.accepte_demandes:
            raise serializers.ValidationError(
                "Ce professionnel ne prend pas de nouvelles demandes pour le moment. Vous pouvez en choisir un autre dans l'annuaire."
            )
        return professionnel

    def validate(self, attrs):
        request = self.context['request']
        # Seule la mise en relation peut devenir payante, et jamais pour une
        # personne en détresse (jeton d'urgence remis par le chatbot)
        if not peut_demander(request.user.utilisateur, en_detresse(request)):
            raise AccesVerrouille
        return attrs

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user.utilisateur
        return super().create(validated_data)


class DemandeContactUtilisateurSerializer(serializers.ModelSerializer):
    """Vue de l'utilisateur sur ses propres demandes, avec ce qu'il faut pour
    la suite : spécialité, modalités du professionnel et messages non lus."""

    professionnel_nom = serializers.CharField(source='professionnel.nom', read_only=True)
    professionnel_specialite = serializers.CharField(source='professionnel.get_specialite_display', read_only=True)
    professionnel_ville = serializers.CharField(source='professionnel.ville', read_only=True)
    consultation_cabinet = serializers.BooleanField(source='professionnel.consultation_cabinet', read_only=True)
    adresse_cabinet = serializers.CharField(source='professionnel.adresse_cabinet', read_only=True)
    consultation_distance = serializers.BooleanField(source='professionnel.consultation_distance', read_only=True)
    non_lus = serializers.IntegerField(read_only=True, default=0)
    dernier_message = serializers.DateTimeField(read_only=True, default=None)

    class Meta:
        model = DemandeContact
        fields = [
            'id', 'professionnel', 'professionnel_nom', 'professionnel_specialite', 'professionnel_ville',
            'consultation_cabinet', 'adresse_cabinet', 'consultation_distance',
            'message', 'statut', 'date', 'date_reponse', 'non_lus', 'dernier_message',
        ]


class DemandeContactProfessionnelSerializer(serializers.ModelSerializer):
    """Vue du professionnel : l'identité de l'utilisateur reste masquée tant que la
    demande n'est pas ACCEPTEE. Seul le pseudonyme
    est visible avant."""

    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    ville = serializers.CharField(source='utilisateur.ville', read_only=True)
    nom = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    non_lus = serializers.IntegerField(read_only=True, default=0)
    dernier_message = serializers.DateTimeField(read_only=True, default=None)

    class Meta:
        model = DemandeContact
        fields = [
            'id', 'date', 'date_reponse', 'statut', 'message', 'pseudonyme', 'ville', 'nom', 'email',
            'non_lus', 'dernier_message',
        ]

    def _acceptee(self, obj):
        return obj.statut == StatutDemandeContact.ACCEPTEE

    def get_nom(self, obj):
        return f'{obj.utilisateur.prenom} {obj.utilisateur.nom}' if self._acceptee(obj) else None

    def get_email(self, obj):
        return obj.utilisateur.email if self._acceptee(obj) else None


class DemandeContactReponseSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(
        choices=[StatutDemandeContact.ACCEPTEE, StatutDemandeContact.REFUSEE]
    )

    def save(self, **kwargs):
        demande = self.instance
        try:
            if self.validated_data['statut'] == StatutDemandeContact.ACCEPTEE:
                demande.accepter()
            else:
                demande.refuser()
        except ValueError as erreur:
            raise serializers.ValidationError(str(erreur)) from erreur
        return demande


class MessageRelationSerializer(serializers.ModelSerializer):
    contenu = serializers.CharField(max_length=2000, trim_whitespace=True)
    de_moi = serializers.SerializerMethodField()
    lu = serializers.SerializerMethodField()

    class Meta:
        model = MessageRelation
        fields = ['id', 'contenu', 'date', 'de_moi', 'lu']
        read_only_fields = ['date']

    def get_de_moi(self, message):
        return message.auteur_id == self.context['request'].user.pk

    def get_lu(self, message):
        return message.lu_le is not None
