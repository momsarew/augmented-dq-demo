"""
Module d'élicitation des pondérations AHP (Analytic Hierarchy Process)
Méthode pour obtenir poids w_DB, w_DP, w_BR, w_UP par usage métier
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class AHPElicitor:
    """
    Éliciteur de pondérations via AHP ou règles métier
    """
    
    # Pondérations pré-configurées par type usage
    PRESET_WEIGHTS = {
        "paie_reglementaire": {
            "w_DB": 0.40,  # DB critique (parsing obligatoire)
            "w_DP": 0.30,  # DP critique (ETL pour calculs légaux)
            "w_BR": 0.30,  # BR critique (règles comptables)
            "w_UP": 0.00,  # UP non pertinent (paie imposée par loi)
            "rationale": "Conformité légale prime, aucune flexibilité contextuelle"
        },
        
        "reporting_social": {
            "w_DB": 0.25,  # DB important mais agrégations compensent
            "w_DP": 0.20,  # DP moyen (agrégations masquent erreurs individuelles)
            "w_BR": 0.30,  # BR critique (cohérence entre rapports)
            "w_UP": 0.25,  # UP important (granularité adaptée)
            "rationale": "Cohérence métier prime, flexibilité contextuelle importante"
        },
        
        "dashboard_operationnel": {
            "w_DB": 0.10,  # DB secondaire (fraîcheur > précision ponctuelle)
            "w_DP": 0.10,  # DP secondaire (dashboard = exploration)
            "w_BR": 0.20,  # BR moyen (incohérences tolérées si alertées)
            "w_UP": 0.60,  # UP critique (adéquation usage prime)
            "rationale": "Adéquation usage prime (fraîcheur, granularité adaptative)"
        },
        
        "audit_conformite": {
            "w_DB": 0.35,  # DB critique (traçabilité complète requise)
            "w_DP": 0.35,  # DP critique (transformations auditables)
            "w_BR": 0.30,  # BR critique (règles documentées)
            "w_UP": 0.00,  # UP non pertinent (conformité imposée)
            "rationale": "Traçabilité et conformité réglementaire absolues"
        },
        
        "analytics_decisional": {
            "w_DB": 0.20,  # DB moyen (tolère nulls si justifiés)
            "w_DP": 0.25,  # DP important (transformations correctes)
            "w_BR": 0.25,  # BR important (règles métier cohérentes)
            "w_UP": 0.30,  # UP important (adéquation cas d'usage)
            "rationale": "Équilibre technique/métier, contexte important"
        }
    }
    
    def __init__(self):
        pass
    
    def get_weights_preset(self, usage_type: str) -> Dict[str, float]:
        """
        Récupère pondérations pré-configurées pour un type usage
        
        Args:
            usage_type: Clé dans PRESET_WEIGHTS
        
        Returns:
            {
                "w_DB": 0.40,
                "w_DP": 0.30,
                "w_BR": 0.30,
                "w_UP": 0.00,
                "rationale": "..."
            }
        """
        # Normaliser clé
        usage_key = usage_type.lower().replace(' ', '_').replace('-', '_')
        
        # Chercher match
        for preset_key, weights in self.PRESET_WEIGHTS.items():
            if preset_key in usage_key or usage_key in preset_key:
                return weights.copy()
        
        # Fallback: pondérations équilibrées
        return {
            "w_DB": 0.25,
            "w_DP": 0.25,
            "w_BR": 0.25,
            "w_UP": 0.25,
            "rationale": "Pondérations équilibrées par défaut"
        }
    
    def elicit_weights_interactive(self, usage_name: str) -> Dict[str, float]:
        """
        Élicitation interactive via comparaisons pairées AHP
        
        Méthode:
        1. Poser questions "DB vs DP, lequel plus important ?"
        2. Scorer réponses (1-9 échelle Saaty)
        3. Calculer vecteur propre matrice comparaisons
        4. Normaliser poids
        
        NOTE: Nécessite interaction utilisateur (chat IA)
        Pour l'instant, retourne preset
        """
        # TODO: Implémenter dialogue AHP complet
        # Pour démo, retourne preset basé sur nom usage
        return self.get_weights_preset(usage_name)
    
    def compute_ahp_matrix(self, comparisons: List[Tuple[str, str, float]]) -> Dict[str, float]:
        """
        Calcule pondérations depuis matrice comparaisons pairées AHP
        
        Args:
            comparisons: Liste (dim1, dim2, score_saaty)
                Ex: [("DB", "DP", 3), ("DB", "BR", 2), ...]
                Score Saaty: 1=égaux, 3=modérément plus, 5=fortement plus, 9=extrêmement plus
        
        Returns:
            {"w_DB": 0.45, "w_DP": 0.25, "w_BR": 0.20, "w_UP": 0.10}
        """
        # Dimensions
        dims = ["DB", "DP", "BR", "UP"]
        n = len(dims)
        
        # Initialiser matrice comparaisons (identité)
        matrix = np.eye(n)
        
        # Remplir matrice avec comparaisons
        dim_to_idx = {d: i for i, d in enumerate(dims)}
        
        for dim1, dim2, score in comparisons:
            i = dim_to_idx[dim1]
            j = dim_to_idx[dim2]
            matrix[i, j] = score
            matrix[j, i] = 1 / score  # Réciprocité
        
        # Calculer vecteur propre principal (méthode AHP classique)
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_idx = np.argmax(eigenvalues)
        principal_vector = eigenvectors[:, max_idx].real
        
        # Normaliser (somme = 1)
        weights = principal_vector / principal_vector.sum()
        
        # Convertir en dict
        return {
            f"w_{dims[i]}": round(weights[i], 2)
            for i in range(n)
        }
    
    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """
        Valide cohérence pondérations
        
        Checks:
        - Somme = 1.0 (ou proche)
        - Toutes valeurs >= 0
        - Clés attendues présentes
        """
        expected_keys = ["w_DB", "w_DP", "w_BR", "w_UP"]
        
        # Check clés
        if not all(k in weights for k in expected_keys):
            return False
        
        # Check valeurs positives
        if any(weights[k] < 0 for k in expected_keys):
            return False
        
        # Check somme proche 1.0
        total = sum(weights[k] for k in expected_keys)
        if not (0.98 <= total <= 1.02):
            return False
        
        return True
    
    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Normalise pondérations pour somme = 1.0
        """
        expected_keys = ["w_DB", "w_DP", "w_BR", "w_UP"]
        total = sum(weights.get(k, 0) for k in expected_keys)
        
        if total == 0:
            # Cas dégénéré: équipondération
            return {k: 0.25 for k in expected_keys}
        
        return {
            k: round(weights.get(k, 0) / total, 2)
            for k in expected_keys
        }


def elicit_weights_auto(usages: List[Dict], 
                        vecteurs_4d: Dict = None) -> Dict[str, Dict]:
    """
    Élicitation automatique pondérations pour liste usages
    
    Args:
        usages: Liste dicts avec clés 'nom', 'criticite', 'type'
            Ex: [
                {"nom": "Paie", "criticite": "HIGH", "type": "paie_reglementaire"},
                {"nom": "CSE", "criticite": "MEDIUM", "type": "reporting_social"},
                ...
            ]
        vecteurs_4d: Optionnel, pour ajustements contextuels
    
    Returns:
        {
            "Paie": {"w_DB": 0.40, "w_DP": 0.30, ...},
            "CSE": {"w_DB": 0.25, "w_DP": 0.20, ...},
            ...
        }
    """
    elicitor = AHPElicitor()
    weights = {}
    
    for usage in usages:
        usage_name = usage.get('nom', 'Unknown')
        usage_type = usage.get('type', usage_name)
        
        # Récupérer preset
        w = elicitor.get_weights_preset(usage_type)
        
        # Ajustements contextuels si vecteurs fournis
        if vecteurs_4d:
            # TODO: Ajuster poids basé sur distribution vecteurs
            # Ex: Si P_DB très élevé pour tous attributs, augmenter w_DB
            pass
        
        weights[usage_name] = w
    
    return weights


def simulate_expert_dialogue(usage_name: str, usage_type: str) -> List[str]:
    """
    Simule dialogue élicitation expert (pour démo chat IA)
    
    Returns:
        Liste questions/réponses simulées
    """
    dialogues = {
        "paie_reglementaire": [
            ("Q: Entre [DB] contraintes structurelles et [BR] règles métier, lequel prime pour la Paie ?",
             "R: Les deux sont critiques. DB car parsing obligatoire, BR car calculs légaux."),
            ("Q: [DP] Data Processing est-il critique pour la Paie ?",
             "R: Oui, une erreur ETL = redressement URSSAF potentiel."),
            ("Q: [UP] Usage-fit compte-t-il pour la Paie ?",
             "R: Non, la paie est imposée par la loi, pas de flexibilité contextuelle.")
        ],
        
        "reporting_social": [
            ("Q: Quelle dimension prime pour un rapport CSE ?",
             "R: [BR] Cohérence entre rapports est critique. [DB] important mais agrégations compensent."),
            ("Q: [DP] est-il critique pour reporting social ?",
             "R: Moyen. Les agrégations masquent erreurs individuelles."),
            ("Q: [UP] Usage-fit compte-t-il ?",
             "R: Oui ! La granularité doit être adaptée (mois vs jour).")
        ],
        
        "dashboard_operationnel": [
            ("Q: Qu'est-ce qui compte pour un dashboard RH opérationnel ?",
             "R: FRAÎCHEUR et TENDANCES. Précision ponctuelle secondaire."),
            ("Q: [DP] est-il critique ?",
             "R: Peu. Le dashboard est pour l'exploration, pas décision légale."),
            ("Q: [BR] compte-t-il ?",
             "R: Moyen. Incohérences tolérées si elles sont alertées.")
        ]
    }
    
    usage_key = usage_type.lower().replace(' ', '_')
    
    for key, dialogue in dialogues.items():
        if key in usage_key or usage_key in key:
            return dialogue
    
    # Fallback
    return [
        ("Q: Quelle dimension est la plus importante ?",
         "R: Ça dépend du contexte métier.")
    ]


if __name__ == "__main__":
    # Test élicitation
    elicitor = AHPElicitor()
    
    print("="*80)
    print("TEST MODULE AHP_ELICITOR")
    print("="*80)
    
    # Test 1: Presets
    print("\n1. Pondérations preset 'Paie réglementaire':")
    weights_paie = elicitor.get_weights_preset("paie_reglementaire")
    print(f"   w_DB={weights_paie['w_DB']}, w_DP={weights_paie['w_DP']}, "
          f"w_BR={weights_paie['w_BR']}, w_UP={weights_paie['w_UP']}")
    print(f"   Rationale: {weights_paie['rationale']}")
    
    # Test 2: Élicitation auto multiple usages
    print("\n2. Élicitation auto pour 3 usages:")
    usages = [
        {"nom": "Paie", "type": "paie_reglementaire", "criticite": "HIGH"},
        {"nom": "CSE", "type": "reporting_social", "criticite": "MEDIUM"},
        {"nom": "Dashboard", "type": "dashboard_operationnel", "criticite": "LOW"}
    ]
    
    weights_all = elicit_weights_auto(usages)
    for usage_name, weights in weights_all.items():
        print(f"   {usage_name}: w_DB={weights['w_DB']}, w_DP={weights['w_DP']}, "
              f"w_BR={weights['w_BR']}, w_UP={weights['w_UP']}")
    
    # Test 3: Calcul AHP depuis matrice
    print("\n3. Calcul AHP depuis comparaisons pairées:")
    comparisons = [
        ("DB", "DP", 2),   # DB modérément plus important que DP
        ("DB", "BR", 1.5), # DB légèrement plus que BR
        ("DB", "UP", 5),   # DB fortement plus que UP
        ("DP", "BR", 1),   # DP égal BR
        ("DP", "UP", 3),   # DP modérément plus que UP
        ("BR", "UP", 3)    # BR modérément plus que UP
    ]
    weights_ahp = elicitor.compute_ahp_matrix(comparisons)
    print(f"   Résultat AHP: {weights_ahp}")
    print(f"   Somme: {sum(weights_ahp.values())}")
