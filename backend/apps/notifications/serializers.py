from rest_framework import serializers


class NotificationLectureSerializer(serializers.Serializer):
    """Représentation commune d'une NotificationEmail ou NotificationPush."""

    id = serializers.IntegerField()
    canal = serializers.SerializerMethodField()
    titre = serializers.SerializerMethodField()
    contenu = serializers.CharField()
    date_envoi = serializers.DateTimeField()
    lue = serializers.SerializerMethodField()

    def get_canal(self, obj):
        return 'email' if hasattr(obj, 'objet') else 'push'

    def get_titre(self, obj):
        return getattr(obj, 'objet', '') or ''

    def get_lue(self, obj):
        return obj.statut == 'LUE'
