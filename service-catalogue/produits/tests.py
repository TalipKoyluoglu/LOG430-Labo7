from decimal import Decimal

from django.test import TestCase

from produits.domain.value_objects import PrixMonetaire


class PrixMonetaireTaxeTestCase(TestCase):
    """
    Tests unitaires pour la méthode appliquer_taxe de PrixMonetaire
    """

    def test_appliquer_taxe_standard(self):
        prix = PrixMonetaire(Decimal("100.00"), "CAD")
        prix_taxe = prix.appliquer_taxe(Decimal("15"))
        self.assertEqual(prix_taxe.montant, Decimal("115.00"))
        self.assertEqual(prix_taxe.devise, "CAD")

    def test_appliquer_taxe_zero(self):
        prix = PrixMonetaire(Decimal("50.00"), "EUR")
        prix_taxe = prix.appliquer_taxe(Decimal("0"))
        self.assertEqual(prix_taxe.montant, Decimal("50.00"))

    def test_appliquer_taxe_negative_leve_une_erreur(self):
        prix = PrixMonetaire(Decimal("20.00"), "USD")
        with self.assertRaises(ValueError):
            prix.appliquer_taxe(Decimal("-5"))
