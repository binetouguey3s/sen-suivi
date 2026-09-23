"""Validateurs de robustesse des mots de passe (directive de sécurité, section 2A).

Ils complètent les validateurs natifs de Django déclarés dans
AUTH_PASSWORD_VALIDATORS (longueur minimale, similarité avec le compte,
liste de 20 000 mots de passe compromis connus). Comme tous les
sérialiseurs appellent validate_password, ces règles s'appliquent à
l'inscription, à l'inscription pro, au changement et à la réinitialisation.
"""

import re

from django.core.exceptions import ValidationError

# Rangées de clavier et alphabets lus dans les deux sens pour repérer les suites.
SUITES_DE_REFERENCE = (
    'abcdefghijklmnopqrstuvwxyz',
    '0123456789',
    'azertyuiop',
    'qsdfghjklm',
    'wxcvbn',
    'qwertyuiop',
    'asdfghjkl',
    'zxcvbnm',
)


class ComplexiteValidator:
    """Exige au moins `categories_minimum` des quatre catégories de caractères."""

    def __init__(self, categories_minimum=3):
        self.categories_minimum = categories_minimum

    def validate(self, password, user=None):
        categories = [
            re.search(r'[A-Z]', password),
            re.search(r'[a-z]', password),
            re.search(r'\d', password),
            re.search(r'[^A-Za-z0-9]', password),
        ]
        if sum(1 for c in categories if c) < self.categories_minimum:
            raise ValidationError(self.get_help_text(), code='password_trop_simple')

    def get_help_text(self):
        return (
            'Le mot de passe doit contenir au moins trois de ces éléments : '
            'une majuscule, une minuscule, un chiffre, un caractère spécial.'
        )


class SuiteEvidenteValidator:
    """Refuse les suites logiques (12345, abcde, azerty) et les répétitions (aaaa).

    La comparaison se fait sans tenir compte des majuscules : « Azerty »
    est aussi prévisible que « azerty ».
    """

    def __init__(self, longueur_suite=5, longueur_repetition=4):
        # 5 plutôt que 4 : « Liberty » contient « erty » sans être une suite tapée au clavier.
        self.longueur_suite = longueur_suite
        self.longueur_repetition = longueur_repetition

    def validate(self, password, user=None):
        minuscule = password.lower()
        if self._contient_suite(minuscule) or self._contient_repetition(minuscule):
            raise ValidationError(self.get_help_text(), code='password_suite_evidente')

    def _contient_suite(self, texte):
        n = self.longueur_suite
        for reference in SUITES_DE_REFERENCE:
            for sens in (reference, reference[::-1]):
                for debut in range(len(sens) - n + 1):
                    if sens[debut:debut + n] in texte:
                        return True
        return False

    def _contient_repetition(self, texte):
        return re.search(r'(.)\1{%d,}' % (self.longueur_repetition - 1), texte) is not None

    def get_help_text(self):
        return (
            'Le mot de passe ne doit pas contenir de suite évidente '
            '(comme 12345, abcde ou azerty) ni de caractère répété.'
        )
