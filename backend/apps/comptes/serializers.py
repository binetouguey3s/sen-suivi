"""Sérialiseurs de comptes.

Un sérialiseur par usage : inscription (écriture) et lecture sont séparées
dès que les champs exposés diffèrent (règle du style de code back-end).
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Professionnel, StatutValidationPro, Utilisateur


class InscriptionUtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = Utilisateur
        fields = ['id', 'nom', 'prenom', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        utilisateur = Utilisateur(**validated_data)
        utilisateur.set_password(password)
        utilisateur.save()
        return utilisateur


class InscriptionProfessionnelSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = Professionnel
        fields = [
            'id', 'nom', 'email', 'password',
            'specialite', 'ville', 'langue', 'tarif_indicatif',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        # statut_validation n'est jamais accepté en entrée : le modèle le
        # place déjà à EN_ATTENTE par défaut.
        professionnel = Professionnel(**validated_data)
        professionnel.set_password(password)
        professionnel.save()
        return professionnel


class ProfessionnelLectureSerializer(serializers.ModelSerializer):
    specialite_affichee = serializers.CharField(source='get_specialite_display', read_only=True)
    statut_validation_affiche = serializers.CharField(
        source='get_statut_validation_display', read_only=True
    )

    class Meta:
        model = Professionnel
        fields = [
            'id', 'nom', 'email', 'specialite', 'specialite_affichee',
            'ville', 'langue', 'tarif_indicatif',
            'statut_validation', 'statut_validation_affiche', 'date_creation',
        ]


class ProfessionnelValidationSerializer(serializers.Serializer):
    """PATCH /api/professionnels/{id} : fait uniquement transiter le statut.

    La logique (notification, caractère définitif de REFUSE) vit dans les
    méthodes du modèle Professionnel.valider()/refuser(), pas ici.
    """

    statut_validation = serializers.ChoiceField(
        choices=[StatutValidationPro.VALIDE, StatutValidationPro.REFUSE]
    )

    def save(self, **kwargs):
        professionnel = self.instance
        cible = self.validated_data['statut_validation']
        try:
            if cible == StatutValidationPro.VALIDE:
                professionnel.valider()
            else:
                professionnel.refuser()
        except ValueError as erreur:
            raise serializers.ValidationError(str(erreur)) from erreur
        return professionnel


class LoginSerializer(TokenObtainPairSerializer):
    """Ajoute le claim type_compte et refuse un professionnel non VALIDE."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['type_compte'] = user.type_compte
        token['nom'] = user.nom
        if user.type_compte == 'utilisateur':
            token['prenom'] = user.utilisateur.prenom
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.type_compte == 'professionnel':
            statut = self.user.professionnel.statut_validation
            if statut == StatutValidationPro.EN_ATTENTE:
                raise serializers.ValidationError(
                    "Votre inscription professionnelle est en cours de validation "
                    "par un administrateur."
                )
            if statut == StatutValidationPro.REFUSE:
                raise serializers.ValidationError(
                    "Votre inscription professionnelle a été refusée."
                )

        return data
