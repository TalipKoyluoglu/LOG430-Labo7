"""
Tests d'intégration pour les views du module magasin
Tests via Django Client avec mocking des clients HTTP
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import Client
from django.urls import reverse
from uuid import UUID
import json


@pytest.mark.django_db
@pytest.mark.integration
class TestGestionStockViews:
    """Tests d'intégration des vues de gestion des stocks"""

    def setup_method(self):
        self.client = Client()

    @patch(
        "magasin.infrastructure.inventaire_client.InventaireClient.lister_stocks_centraux"
    )
    def test_uc2_stock_success(self, mock_lister_stocks):
        """Test intégration consultation stocks - cas succès"""
        # Arrange
        mock_response = {
            "success": True,
            "stocks": [
                {"produit_id": "123", "quantite": 50, "seuil_minimum": 10},
                {"produit_id": "456", "quantite": 5, "seuil_minimum": 20},
            ],
        }
        mock_lister_stocks.return_value = mock_response

        # Act
        response = self.client.get(reverse("gestion_stocks"))

        # Assert
        assert response.status_code == 200
        assert "stocks" in response.context
        assert len(response.context["stocks"]) == 2
        mock_lister_stocks.assert_called_once()

    @patch(
        "magasin.infrastructure.inventaire_client.InventaireClient.lister_stocks_centraux"
    )
    def test_uc2_stock_api_error(self, mock_lister_stocks):
        """Test intégration consultation stocks - cas erreur API"""
        # Arrange
        mock_lister_stocks.return_value = {
            "success": False,
            "error": "Service inventaire indisponible",
        }

        # Act
        response = self.client.get(reverse("gestion_stocks"))

        # Assert
        assert response.status_code == 200
        assert response.context["stocks"] == []
        mock_lister_stocks.assert_called_once()

    @patch(
        "magasin.infrastructure.inventaire_client.InventaireClient.creer_demande_reapprovisionnement"
    )
    def test_uc2_reapprovisionner_success(self, mock_creer_demande):
        """Test intégration créer demande réapprovisionnement"""
        # Arrange
        mock_creer_demande.return_value = {"success": True, "demande_id": "demand-123"}

        # Act
        response = self.client.post(
            reverse("reapprovisionner"),
            {"produit_id": "123", "magasin_id": "456", "quantite": "25"},
        )

        # Assert
        assert response.status_code == 302  # Redirect après succès
        mock_creer_demande.assert_called_once_with(
            produit_id="123", magasin_id="456", quantite=25
        )


@pytest.mark.django_db
@pytest.mark.integration
class TestGestionProduitsViews:
    """Tests d'intégration des vues de gestion des produits"""

    def setup_method(self):
        self.client = Client()

    @patch(
        "magasin.infrastructure.catalogue_client.CatalogueClient.rechercher_produits"
    )
    def test_uc4_lister_produits_success(self, mock_rechercher):
        """Test intégration listing produits"""
        # Arrange
        mock_rechercher.return_value = {
            "success": True,
            "data": {
                "produits": [
                    {"id": "1", "nom": "Produit A", "prix": 19.99},
                    {"id": "2", "nom": "Produit B", "prix": 29.99},
                ]
            },
        }

        # Act
        response = self.client.get(reverse("lister_produits"))

        # Assert
        assert response.status_code == 200
        assert len(response.context["produits"]) == 2
        mock_rechercher.assert_called_once()

    @patch("magasin.infrastructure.catalogue_client.CatalogueClient.ajouter_produit")
    def test_uc4_ajouter_produit_success(self, mock_ajouter):
        """Test intégration ajout produit"""
        # Arrange
        mock_ajouter.return_value = {"success": True, "produit_id": "new-123"}

        # Act
        response = self.client.post(
            reverse("ajouter_produit"),
            {
                "nom": "Nouveau Produit",
                "prix": "39.99",
                "description": "Description test",
                "categorie": "Test",
            },
        )

        # Assert
        assert response.status_code == 302  # Redirect après succès
        mock_ajouter.assert_called_once_with(
            "Nouveau Produit", "Test", 39.99, "Description test"
        )


@pytest.mark.django_db
@pytest.mark.integration
class TestRapportConsolideViews:
    """Tests d'intégration des vues de rapport consolidé"""

    def setup_method(self):
        self.client = Client()

    @patch(
        "magasin.infrastructure.commandes_client.CommandesClient.generer_rapport_consolide"
    )
    def test_rapport_ventes_success(self, mock_rapport):
        """Test intégration génération rapport"""
        # Arrange
        mock_rapport.return_value = {
            "success": True,
            "rapport": {
                "ventes_totales": 1500.00,
                "nombre_ventes": 25,
                "magasins": [
                    {"id": "1", "nom": "Magasin A", "ventes": 800.00},
                    {"id": "2", "nom": "Magasin B", "ventes": 700.00},
                ],
            },
        }

        # Act
        response = self.client.get(reverse("rapport_consolide"))

        # Assert
        assert response.status_code == 200
        assert "rapport_complet" in response.context
        assert (
            response.context["rapport_complet"]["rapport"]["ventes_totales"] == 1500.00
        )
        mock_rapport.assert_called_once()

    @patch("magasin.infrastructure.commandes_client.CommandesClient.enregistrer_vente")
    def test_enregistrer_vente_success(self, mock_enregistrer):
        """Test intégration enregistrement vente"""
        # Arrange
        mock_enregistrer.return_value = {"success": True, "vente_id": "vente-123"}

        # Act
        response = self.client.post(
            reverse("enregistrer_vente"),
            {
                "magasin_id": "1",
                "produit_id": "123",
                "quantite": "2",
                "client_id": "client-456",
            },
        )

        # Assert
        assert response.status_code == 302  # Redirect après succès
        mock_enregistrer.assert_called_once()


@pytest.mark.django_db
@pytest.mark.integration
class TestWorkflowDemandesViews:
    """Tests d'intégration workflow des demandes"""

    def setup_method(self):
        self.client = Client()

    @patch(
        "magasin.infrastructure.supply_chain_client.SupplyChainClient.lister_demandes_en_attente"
    )
    def test_uc6_demandes_success(self, mock_lister):
        """Test intégration listing demandes"""
        # Arrange
        mock_lister.return_value = {
            "success": True,
            "demandes": [
                {"id": "1", "produit": "Produit A", "statut": "EN_ATTENTE"},
                {"id": "2", "produit": "Produit B", "statut": "EN_ATTENTE"},
            ],
        }

        # Act
        response = self.client.get(reverse("workflow_demandes"))

        # Assert
        assert response.status_code == 200
        assert len(response.context["demandes"]) == 2
        mock_lister.assert_called_once()

    @patch(
        "magasin.infrastructure.supply_chain_client.SupplyChainClient.valider_demande"
    )
    def test_uc6_valider_demande(self, mock_valider):
        """Test intégration validation demande"""
        # Arrange
        mock_valider.return_value = {"success": True, "message": "Demande validée"}

        # Act
        response = self.client.post(
            reverse("valider_demande", args=["12345678-1234-5678-9abc-123456789abc"])
        )

        # Assert
        assert response.status_code == 302
        mock_valider.assert_called_once_with(
            UUID("12345678-1234-5678-9abc-123456789abc")
        )

    @patch(
        "magasin.infrastructure.supply_chain_client.SupplyChainClient.rejeter_demande"
    )
    def test_uc6_rejeter_demande(self, mock_rejeter):
        """Test intégration rejet demande"""
        # Arrange
        mock_rejeter.return_value = {"success": True, "message": "Demande rejetée"}

        # Act
        response = self.client.post(
            reverse("rejeter_demande", args=["12345678-1234-5678-9abc-123456789abc"]),
            {"motif": "Stock suffisant"},
        )

        # Assert
        assert response.status_code == 302
        mock_rejeter.assert_called_once_with(
            UUID("12345678-1234-5678-9abc-123456789abc"),
            motif="Rejeté par l'utilisateur",
        )


@pytest.mark.django_db
@pytest.mark.integration
class TestIndicateursPerformanceViews:
    """Tests d'intégration dashboard indicateurs"""

    def setup_method(self):
        self.client = Client()

    @patch(
        "magasin.infrastructure.commandes_client.CommandesClient.generer_indicateurs"
    )
    def test_uc3_dashboard_success(self, mock_indicateurs):
        """Test intégration dashboard"""
        # Arrange
        mock_indicateurs.return_value = [
            {
                "magasin_id": "1",
                "magasin_nom": "Magasin A",
                "ventes_jour": 500.00,
                "objectif": 600.00,
                "performance": 83.33,
            }
        ]

        # Act
        response = self.client.get(reverse("indicateurs_performance"))

        # Assert
        assert response.status_code == 200
        assert "indicateurs" in response.context
        assert len(response.context["indicateurs"]) == 1
        mock_indicateurs.assert_called_once()
