"""Sérialiseurs de comptes.

Un sérialiseur par usage : inscription (écriture) et lecture sont séparées
dès que les champs exposés diffèrent (règle du style de code back-end).
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CompteUtilisateur, Professionnel, StatutValidationPro, Utilisateur


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
            'specialite', 'ville', 'langue', 'tarif_indicatif', 'presentation',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        # statut_validation n'est jamais accepté en entrée : le modèle le
        # place déjà à EN_ATTENTE par défaut.
        professionnel = Professionnel(**validated_data)
        professionnel.set_password(password)
        professionnel.save()
        return professionnel


class ProfessionnelPublicSerializer(serializers.ModelSerializer):
    """Profil affichable publiquement : jamais d'e-mail ni de statut interne."""

    specialite_affichee = serializers.CharField(source='get_specialite_display', read_only=True)

    class Meta:
        model = Professionnel
        fields = [
            'id', 'nom', 'specialite', 'specialite_affichee',
            'ville', 'langue', 'tarif_indicatif', 'presentation',
        ]


class ProfessionnelLectureSerializer(serializers.ModelSerializer):
    specialite_affichee = serializers.CharField(source='get_specialite_display', read_only=True)
    statut_validation_affiche = serializers.CharField(
        source='get_statut_validation_display', read_only=True
    )

    class Meta:
        model = Professionnel
        fields = [
            'id', 'nom', 'email', 'specialite', 'specialite_affichee',
            'ville', 'langue', 'tarif_indicatif', 'presentation',
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


class DemandeReinitialisationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ConfirmationReinitialisationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])


class CompteMoiSerializer(serializers.ModelSerializer):
    """Compte connecté (GET/PATCH /api/comptes/moi)."""

    type_compte = serializers.CharField(read_only=True)
    prenom = serializers.CharField(required=False, allow_blank=False)
    ville = serializers.CharField(required=False, allow_blank=True)
    pseudonyme = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = CompteUtilisateur
        fields = ['id', 'type_compte', 'nom', 'prenom', 'email', 'ville', 'pseudonyme', 'preferences']

    def to_representation(self, instance):
        donnees = super().to_representation(instance)
        if instance.type_compte == 'utilisateur':
            donnees['prenom'] = instance.utilisateur.prenom
            donnees['ville'] = instance.utilisateur.ville
            donnees['pseudonyme'] = instance.utilisateur.pseudonyme
        elif instance.type_compte == 'professionnel':
            donnees['prenom'] = None
            donnees['ville'] = instance.professionnel.ville
            donnees['pseudonyme'] = None
        else:
            donnees['prenom'] = donnees['ville'] = donnees['pseudonyme'] = None
        return donnees

    def update(self, instance, validated_data):
        prenom = validated_data.pop('prenom', None)
        ville = validated_data.pop('ville', None)
        instance = super().update(instance, validated_data)
        if instance.type_compte == 'utilisateur':
            utilisateur = instance.utilisateur
            if prenom is not None:
                utilisateur.prenom = prenom
            if ville is not None:
                utilisateur.ville = ville
            utilisateur.save()
        elif instance.type_compte == 'professionnel' and ville is not None:
            instance.professionnel.ville = ville
            instance.professionnel.save(update_fields=['ville'])
        return instance


class ChangementMotDePasseSerializer(serializers.Serializer):
    ancien = serializers.CharField(write_only=True)
    nouveau = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_ancien(self, valeur):
        if not self.context['request'].user.check_password(valeur):
            raise serializers.ValidationError('Le mot de passe actuel est incorrect.')
        return valeur


class SuppressionCompteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, valeur):
        if not self.context['request'].user.check_password(valeur):
            raise serializers.ValidationError('Mot de passe incorrect.')
        return valeur
