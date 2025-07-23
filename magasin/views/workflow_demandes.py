"""
Vue Workflow des Demandes (ex-UC6)
Gestion du workflow de validation/rejet des demandes via le service-supply-chain DDD
"""

from django.shortcuts import render, redirect
from django.contrib import messages
import logging

# Import du client HTTP vers service-supply-chain
from magasin.infrastructure.supply_chain_client import SupplyChainClient

logger = logging.getLogger(__name__)


def uc6_demandes(request):
    """
    Affiche la liste des demandes en attente de validation
    Utilise l'API DDD du service-supply-chain : ListerDemandesUseCase
    """
    logger.info("📋 Consultation workflow des demandes supply-chain")
    try:
        # Initialisation du client HTTP
        supply_chain_client = SupplyChainClient()

        # Récupération des demandes en attente via l'API DDD
        demandes_data = supply_chain_client.lister_demandes_en_attente()

        if not demandes_data.get("success", False):
            # En cas d'erreur API, afficher un message explicite pour l'utilisateur
            logger.error(
                "❌ Échec récupération demandes supply-chain: %s",
                demandes_data.get("error", "Erreur inconnue"),
            )
            messages.info(
                request,
                "Aucune demande en attente ou service temporairement indisponible.",
            )
            return render(
                request,
                "magasin/uc6_demandes.html",
                {
                    "demandes": [],
                    "error_message": demandes_data.get(
                        "error",
                        "Aucune demande en attente ou service temporairement indisponible.",
                    ),
                },
            )

        # Extraction des demandes
        demandes = demandes_data.get("demandes", [])

        # Statistiques pour l'affichage
        stats = {
            "total_demandes": len(demandes),
            "demandes_urgentes": len(
                [d for d in demandes if d.get("quantite", 0) > 50]  # Seuil d'urgence
            ),
            "valeur_totale": sum(
                d.get("quantite", 0) * d.get("prix_unitaire_estime", 0)
                for d in demandes
            ),
        }

        # Tri des demandes par priorité (quantité décroissante)
        demandes_triees = sorted(
            demandes, key=lambda x: x.get("quantite", 0), reverse=True
        )

        logger.info(
            f"Demandes listées avec succès: {len(demandes)} demandes en attente"
        )

        return render(
            request,
            "magasin/uc6_demandes.html",
            {
                "demandes": demandes_triees,
                "stats": stats,
                "success_message": "Liste des demandes mise à jour",
            },
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des demandes: {e}")
        messages.error(request, "Erreur interne lors de la récupération des demandes")
        return render(
            request,
            "magasin/uc6_demandes.html",
            {"demandes": [], "error_message": "Erreur interne du serveur"},
        )


def uc6_valider(request, demande_id):
    """
    Valide une demande de réapprovisionnement via l'API DDD du service-supply-chain
    Utilise le Use Case: ValiderDemandeUseCase
    """
    logger.info("✅ Validation demande supply-chain ID: %s", demande_id)
    try:
        # Initialisation du client HTTP
        supply_chain_client = SupplyChainClient()

        # Appel à l'API DDD pour valider la demande
        validation_result = supply_chain_client.valider_demande(demande_id)

        if validation_result.get("success", False):
            logger.info("✅ Demande ID %s validée avec succès", demande_id)
            messages.success(
                request,
                f"Demande {demande_id} approuvée et stock transféré avec succès",
            )
            logger.info(f"Demande {demande_id} validée avec succès")
        else:
            error_msg = validation_result.get(
                "error", "Erreur inconnue lors de la validation"
            )

            # Messages d'erreur spécifiques selon le type d'erreur
            if "stock insuffisant" in error_msg.lower():
                messages.error(
                    request,
                    f"Validation impossible: stock central insuffisant pour la demande {demande_id}",
                )
            elif "demande introuvable" in error_msg.lower():
                messages.error(
                    request, f"Demande {demande_id} introuvable ou déjà traitée"
                )
            else:
                messages.error(
                    request,
                    f"Échec de la validation de la demande {demande_id}: {error_msg}",
                )

            logger.warning(f"Échec validation demande {demande_id}: {error_msg}")

        return redirect("workflow_demandes")

    except Exception as e:
        messages.error(
            request, f"Erreur interne lors de la validation de la demande {demande_id}"
        )
        logger.error(f"Erreur lors de la validation de la demande {demande_id}: {e}")
        return redirect("workflow_demandes")


def uc6_rejeter(request, demande_id):
    """
    Rejette une demande de réapprovisionnement via l'API DDD du service-supply-chain
    Utilise le Use Case: RejeterDemandeUseCase
    """
    logger.info("❌ Rejet demande supply-chain ID: %s", demande_id)
    try:
        # Initialisation du client HTTP
        supply_chain_client = SupplyChainClient()

        # Appel à l'API DDD pour rejeter la demande
        rejet_result = supply_chain_client.rejeter_demande(
            demande_id, motif="Rejeté par l'utilisateur"
        )
        logger.info(f"RÉPONSE REJET DEMANDE: {rejet_result}")
        if rejet_result.get("success", False):
            messages.success(request, f"Demande {demande_id} rejetée avec succès")
            logger.info(f"Demande {demande_id} rejetée avec succès")
        else:
            error_msg = rejet_result.get("error", "Erreur inconnue lors du rejet")
            if "demande introuvable" in error_msg.lower():
                messages.error(
                    request, f"Demande {demande_id} introuvable ou déjà traitée"
                )
            else:
                messages.error(
                    request, f"Échec du rejet de la demande {demande_id}: {error_msg}"
                )
            logger.warning(f"Échec rejet demande {demande_id}: {error_msg}")

        return redirect("workflow_demandes")

    except Exception as e:
        messages.error(
            request, f"Erreur interne lors du rejet de la demande {demande_id}"
        )
        logger.error(f"Erreur lors du rejet de la demande {demande_id}: {e}")
        return redirect("workflow_demandes")
