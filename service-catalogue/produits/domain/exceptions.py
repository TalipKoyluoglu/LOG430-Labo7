"""
Exceptions du domaine Catalogue
Exceptions métier spécifiques au contexte Catalogue
"""


class CatalogueError(Exception):
    """Exception de base pour le domaine Catalogue"""

    pass


class ProduitError(CatalogueError):
    """Exception de base pour les erreurs liées aux produits"""

    pass


class ProduitInexistantError(ProduitError):
    """Erreur quand un produit n'existe pas"""

    def __init__(self, produit_id: str):
        self.produit_id = produit_id
        super().__init__(f"Produit {produit_id} non trouvé dans le catalogue")


class ProduitDejaExistantError(ProduitError):
    """Erreur quand un produit existe déjà (nom ou SKU)"""

    def __init__(self, message: str):
        super().__init__(message)


class ProduitNonSupprimableError(ProduitError):
    """Erreur quand un produit ne peut pas être supprimé (règles métier)"""

    def __init__(self, produit_id: str, raison: str):
        self.produit_id = produit_id
        self.raison = raison
        super().__init__(f"Produit {produit_id} ne peut pas être supprimé: {raison}")


class NomProduitInvalideError(ProduitError):
    """Erreur de validation du nom de produit"""

    pass


class PrixInvalideError(ProduitError):
    """Erreur de validation du prix"""

    pass


class SKUInvalideError(ProduitError):
    """Erreur de validation du SKU"""

    pass


class CategorieError(CatalogueError):
    """Exception de base pour les erreurs liées aux catégories"""

    pass


class CategorieInexistanteError(CategorieError):
    """Erreur quand une catégorie n'existe pas"""

    def __init__(self, categorie_id: str):
        self.categorie_id = categorie_id
        super().__init__(f"Catégorie {categorie_id} non trouvée")


class CategorieNonSupprimableError(CategorieError):
    """Erreur quand une catégorie ne peut pas être supprimée"""

    def __init__(self, categorie_id: str, raison: str):
        self.categorie_id = categorie_id
        self.raison = raison
        super().__init__(
            f"Catégorie {categorie_id} ne peut pas être supprimée: {raison}"
        )


class CategorieCirculaireError(CategorieError):
    """Erreur quand on tente de créer une référence circulaire entre catégories"""

    def __init__(self, categorie_id: str, parent_id: str):
        super().__init__(
            f"Référence circulaire détectée: catégorie {categorie_id} "
            f"ne peut pas avoir pour parent {parent_id}"
        )


class RechercheError(CatalogueError):
    """Exception de base pour les erreurs de recherche"""

    pass


class CriteresRechercheInvalidesError(RechercheError):
    """Erreur quand les critères de recherche sont invalides"""

    pass
