from django.utils import timezone
from rest_framework import serializers

from apps.comptes.serializers import ProfessionnelLectureSerializer

from .models import AutoEvaluation, OptionReponse, QuestionEvaluation, SuiviHumeur, TypeEvaluation
from .services import calculer_score_de_tendance, interpreter_score, suggerer_professionnels


class SuiviHumeurSerializer(serializers.ModelSerializer):
    # Optionnel en entrée : la date du jour est utilisée par défaut si absente.
    date = serializers.DateField(required=False)

    class Meta:
        model = SuiviHumeur
        fields = ['id', 'date', 'score_humeur', 'note']

    def create(self, validated_data):
        utilisateur = self.context['request'].user.utilisateur
        validated_data.setdefault('date', timezone.localdate())
        # Une seule entrée par jour et par utilisateur : une seconde saisie le
        # même jour met à jour l'existante (docs/SPECIFICATIONS.md section 2).
        suivi, _ = SuiviHumeur.objects.update_or_create(
            utilisateur=utilisateur,
            date=validated_data['date'],
            defaults={
                'score_humeur': validated_data['score_humeur'],
                'note': validated_data.get('note', ''),
            },
        )
        return suivi


class OptionReponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionReponse
        fields = ['id', 'libelle', 'valeur']


class QuestionEvaluationSerializer(serializers.ModelSerializer):
    options = OptionReponseSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionEvaluation
        fields = ['id', 'libelle', 'ordre', 'options']


class ReponseEvaluationSerializer(serializers.Serializer):
    question = serializers.PrimaryKeyRelatedField(queryset=QuestionEvaluation.objects.all())
    option = serializers.PrimaryKeyRelatedField(queryset=OptionReponse.objects.all())

    def validate(self, attrs):
        if attrs['option'].question_id != attrs['question'].id:
            raise serializers.ValidationError(
                "L'option choisie ne correspond pas à la question."
            )
        return attrs


class AutoEvaluationEcritureSerializer(serializers.Serializer):
    """POST /api/auto-evaluations : calcule le score et suggère des professionnels."""

    type_evaluation = serializers.ChoiceField(choices=TypeEvaluation.choices)
    reponses = ReponseEvaluationSerializer(many=True)

    def validate(self, attrs):
        questions_attendues = QuestionEvaluation.objects.filter(
            type_evaluation=attrs['type_evaluation']
        )
        questions_repondues = {reponse['question'].id for reponse in attrs['reponses']}

        if questions_repondues != set(questions_attendues.values_list('id', flat=True)):
            raise serializers.ValidationError(
                "Toutes les questions de ce type d'évaluation doivent recevoir une réponse."
            )
        for reponse in attrs['reponses']:
            if reponse['question'].type_evaluation != attrs['type_evaluation']:
                raise serializers.ValidationError(
                    "Une des questions ne correspond pas au type d'évaluation indiqué."
                )
        return attrs

    def create(self, validated_data):
        utilisateur = self.context['request'].user.utilisateur
        valeurs = [reponse['option'].valeur for reponse in validated_data['reponses']]
        score = calculer_score_de_tendance(valeurs)

        auto_evaluation = AutoEvaluation.objects.create(
            utilisateur=utilisateur,
            type_evaluation=validated_data['type_evaluation'],
            score_de_tendance=score,
        )
        return auto_evaluation

    def to_representation(self, instance):
        professionnels = suggerer_professionnels(instance.utilisateur)
        return {
            'id': instance.id,
            'type_evaluation': instance.type_evaluation,
            'score_de_tendance': instance.score_de_tendance,
            'interpretation': interpreter_score(instance.score_de_tendance),
            'texte_complementaire': "Ce résultat n'est pas un diagnostic.",
            'professionnels_suggeres': ProfessionnelLectureSerializer(professionnels, many=True).data,
        }
