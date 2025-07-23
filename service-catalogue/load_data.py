#!/usr/bin/env python
"""
Script pour charger les données initiales dans le service produits
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from produits.models import Produit
import json


def load_initial_data():
    """Charge les données initiales depuis le fichier JSON"""
    try:
        with open("initial_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            if item["model"] == "produits.produit":
                fields = item["fields"]
                produit_id = item["pk"]

                # Vérifier si le produit existe déjà
                if not Produit.objects.filter(id=produit_id).exists():
                    Produit.objects.create(
                        id=produit_id,
                        nom=fields["nom"],
                        categorie=fields["categorie"],
                        prix=fields["prix"],
                        description=fields["description"],
                    )
                    print(f"✅ Produit créé : {fields['nom']}")
                else:
                    print(f"⏭️  Produit déjà existant : {fields['nom']}")

        print(
            f"\n🎉 Chargement terminé ! {Produit.objects.count()} produits dans la base."
        )

    except FileNotFoundError:
        print("❌ Fichier initial_data.json non trouvé")
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")


if __name__ == "__main__":
    load_initial_data()
