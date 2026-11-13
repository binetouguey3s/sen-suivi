"""Photo d'un lieu refusée par le stockage en ligne : message clair, pas d'erreur 500."""

from unittest.mock import patch

from botocore.exceptions import ClientError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.comptes.models import Administrateur
from apps.ressources.models import LieuDetente


class StockageRefuseTests(APITestCase):
    def test_un_refus_du_stockage_est_explique_a_l_administration(self):
        admin = Administrateur.objects.create(email='admin@test.sn', nom='Admin')
        self.client.force_authenticate(admin)
        lieu = LieuDetente.objects.first() or LieuDetente.objects.create(nom='Plage test', ville='Dakar')
        refus = ClientError({'Error': {'Code': 'SignatureDoesNotMatch', 'Message': 'clé'}}, 'PutObject')
        with patch('django.db.models.fields.files.FieldFile.save', side_effect=refus), \
             patch('apps.ressources.views.ImageLieuSerializer') as entree:
            entree.return_value.validated_data = {'image': SimpleUploadedFile('a.webp', b'x')}
            reponse = self.client.post(f'/api/lieux/{lieu.pk}/image', {})
        self.assertEqual(reponse.status_code, 502)
        self.assertIn('SignatureDoesNotMatch', reponse.json()['detail'])
