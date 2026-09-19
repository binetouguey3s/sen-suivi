from rest_framework import serializers

from apps.comptes.models import Professionnel, StatutValidationPro

from .models import DemandeContact, StatutDemandeContact


class DemandeContactEcritureSerializer(serializers.ModelSerializer):
    professionnel = serializers.PrimaryKeyRelatedField(
        queryset=Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE)
    )
    message = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    class Meta:
        model = DemandeContact
        fields = ['id', 'professionnel', 'message', 'statut', 'date']
        read_only_fields = ['statut', 'date']

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user.utilisateur
        return super().create(validated_data)


class DemandeContactUtilisateurSerializer(serializers.ModelSerializer):
    """Vue de l'utilisateur sur ses propres demandes."""

    professionnel_nom = serializers.CharField(source='professionnel.nom', read_only=True)

    class Meta:
        model = DemandeContact
        fields = ['id', 'professionnel', 'professionnel_nom', 'message', 'statut', 'date', 'date_reponse']


class DemandeContactProfessionnelSerializer(serializers.ModelSerializer):
    """Vue du professionnel : l'identité de l'utilisateur reste masquée tant que la
    demande n'est pas ACCEPTEE (docs/SPECIFICATIONS.md section 8). Seul le pseudonyme
    est visible avant."""

    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    ville = serializers.CharField(source='utilisateur.ville', read_only=True)
    nom = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = DemandeContact
        fields = ['id', 'date', 'date_reponse', 'statut', 'message', 'pseudonyme', 'ville', 'nom', 'email']

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
