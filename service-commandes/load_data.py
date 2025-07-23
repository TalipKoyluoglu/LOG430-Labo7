#!/usr/bin/env python
"""
Script pour charger les données initiales dans le service-commandes
Charge seulement les magasins - les ventes seront créées via API
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from ventes.models import Magasin
import json


def load_initial_data():
    """Charge les magasins depuis le fichier JSON"""
    try:
        with open("initial_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        print("🏪 === CRÉATION DES MAGASINS ===")
        magasins_crees = 0

        for item in data:
            if item["model"] == "ventes.magasin":
                fields = item["fields"]
                magasin_id = item["pk"]
                if not Magasin.objects.filter(id=magasin_id).exists():
                    Magasin.objects.create(
                        id=magasin_id, nom=fields["nom"], adresse=fields["adresse"]
                    )
                    print(f"✅ Magasin créé : {fields['nom']}")
                    magasins_crees += 1
                else:
                    print(f"⏭️  Magasin déjà existant : {fields['nom']}")

        print(
            f"\n🎉 Chargement terminé ! {Magasin.objects.count()} magasins dans la base."
        )
        if magasins_crees > 0:
            print(
                "💡 Les ventes peuvent maintenant être créées via l'API /ventes/enregistrer/"
            )

    except FileNotFoundError:
        print("❌ Fichier initial_data.json non trouvé")
    except Exception as e:
        print(f"❌ Erreur lors du chargement : {e}")


if __name__ == "__main__":
    load_initial_data()
