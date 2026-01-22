"""
Module de calcul des scores de risque contextualisés
Formule: R(a,U) = w_DB × P_DB + w_DP × P_DP + w_BR × P_BR + w_UP × P_UP
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class RiskScorer:
    """
    Calculateur de scores risque contextualisés par usage
    """
    
    # Seuils de criticité
    RISK_THRESHOLDS = {
        "CRITIQUE": 0.40,      # > 40% = Action urgente
        "ÉLEVÉ": 0.25,         # 25-40% = Surveillance
        "MOYEN": 0.15,         # 15-25% = Attention
        "ACCEPTABLE": 0.10,    # 10-15% = Normal
        "TRÈS_FAIBLE": 0.0     # < 10% = Excellent
    }
    
    def __init__(self):
        pass
    
    def compute_risk_score(self,
                          vector_4d: Dict[str, float],
                          weights: Dict[str, float]) -> float:
        """
        Calcule score risque pour un attribut × usage
        
        Formule: R(a,U) = Σ w_d × P_d
        
        Args:
            vector_4d: Vecteur qualité 4D
                {"P_DB": 0.99, "P_DP": 0.02, "P_BR": 0.20, "P_UP": 0.10}
            weights: Pondérations usage
                {"w_DB": 0.40, "w_DP": 0.30, "w_BR": 0.30, "w_UP": 0.00}
        
        Returns:
            Score risque entre 0 et 1 (ex: 0.463)
        """
        risk = (
            weights.get('w_DB', 0.25) * vector_4d.get('P_DB', 0.0) +
            weights.get('w_DP', 0.25) * vector_4d.get('P_DP', 0.0) +
            weights.get('w_BR', 0.25) * vector_4d.get('P_BR', 0.0) +
            weights.get('w_UP', 0.25) * vector_4d.get('P_UP', 0.0)
        )
        
        return round(risk, 4)
    
    def compute_all_scores(self,
                          vecteurs_4d: Dict[str, Dict],
                          weights_by_usage: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calcule matrice complète scores [Attribut × Usage]
        
        Args:
            vecteurs_4d: {
                "Anciennete": {"P_DB": 0.99, "P_DP": 0.02, ...},
                "Dates_promos": {...},
                ...
            }
            weights_by_usage: {
                "Paie": {"w_DB": 0.40, "w_DP": 0.30, ...},
                "CSE": {...},
                ...
            }
        
        Returns:
            {
                "Anciennete_Paie": 0.463,
                "Anciennete_CSE": 0.337,
                "Dates_promos_Paie": 0.212,
                ...
            }
        """
        scores = {}
        
        for attr, vector in vecteurs_4d.items():
            for usage_name, weights in weights_by_usage.items():
                # Calculer score
                risk = self.compute_risk_score(vector, weights)
                
                # Clé combinée
                key = f"{attr}_{usage_name}"
                scores[key] = risk
        
        return scores
    
    def classify_risk(self, risk_score: float) -> str:
        """
        Classifie score risque en catégorie textuelle
        
        Returns:
            "CRITIQUE" | "ÉLEVÉ" | "MOYEN" | "ACCEPTABLE" | "TRÈS_FAIBLE"
        """
        if risk_score >= self.RISK_THRESHOLDS["CRITIQUE"]:
            return "CRITIQUE"
        elif risk_score >= self.RISK_THRESHOLDS["ÉLEVÉ"]:
            return "ÉLEVÉ"
        elif risk_score >= self.RISK_THRESHOLDS["MOYEN"]:
            return "MOYEN"
        elif risk_score >= self.RISK_THRESHOLDS["ACCEPTABLE"]:
            return "ACCEPTABLE"
        else:
            return "TRÈS_FAIBLE"
    
    def get_risk_color(self, risk_score: float) -> str:
        """
        Retourne code couleur pour visualisation
        
        Returns:
            "red" | "orange" | "yellow" | "lightgreen" | "green"
        """
        category = self.classify_risk(risk_score)
        
        color_map = {
            "CRITIQUE": "red",
            "ÉLEVÉ": "orange",
            "MOYEN": "yellow",
            "ACCEPTABLE": "lightgreen",
            "TRÈS_FAIBLE": "green"
        }
        
        return color_map[category]
    
    def rank_scores_by_risk(self,
                           scores: Dict[str, float],
                           top_n: int = 10) -> List[Tuple[str, float, str]]:
        """
        Classe scores par risque décroissant (priorités actions)
        
        Returns:
            [
                ("Anciennete_Paie", 0.463, "CRITIQUE"),
                ("Anciennete_CSE", 0.337, "ÉLEVÉ"),
                ...
            ]
        """
        # Trier par score décroissant
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Ajouter classification
        ranked = [
            (key, score, self.classify_risk(score))
            for key, score in sorted_scores[:top_n]
        ]
        
        return ranked
    
    def compute_impact_business(self,
                               risk_score: float,
                               attribut: str,
                               usage: str,
                               n_records: int = 687) -> Dict[str, Any]:
        """
        Estime impact business d'un risque
        
        Modèle simplifié:
        - Impact financier basé sur type usage + criticité
        - Nombre enregistrements affectés = risk_score × n_records
        
        Returns:
            {
                "records_affected": 196,
                "impact_financier_mensuel": 45080,
                "severite": "CRITIQUE",
                "actions_recommandees": [...]
            }
        """
        # Estimations impact par type usage
        impact_factors = {
            "Paie": 230,      # €/mois/employé
            "CSE": 50,        # €/mois coût audit
            "Dashboard": 10   # €/mois inefficacité
        }
        
        # Extraire usage
        usage_type = usage
        for key in impact_factors.keys():
            if key.lower() in usage.lower():
                usage_type = key
                break
        
        # Calculer
        records_affected = int(risk_score * n_records)
        impact_mensuel = records_affected * impact_factors.get(usage_type, 50)
        
        # Actions recommandées
        actions = []
        if risk_score > 0.40:
            actions.append(f"URGENT: Corriger {attribut} immédiatement")
            actions.append("Impact: Risque redressement/litiges")
        elif risk_score > 0.25:
            actions.append(f"Planifier correction {attribut} (2 semaines)")
            actions.append("Surveillance renforcée quotidienne")
        elif risk_score > 0.15:
            actions.append(f"Améliorer {attribut} progressivement")
            actions.append("Surveillance hebdomadaire")
        else:
            actions.append(f"{attribut}: Qualité acceptable")
            actions.append("Monitoring standard mensuel")
        
        return {
            "records_affected": records_affected,
            "impact_financier_mensuel": impact_mensuel,
            "severite": self.classify_risk(risk_score),
            "actions_recommandees": actions
        }


def compute_risk_scores(vecteurs_4d: Dict[str, Dict],
                       weights_by_usage: Dict[str, Dict],
                       usages: List[Dict] = None) -> Dict[str, float]:
    """
    Fonction utilitaire: calcul scores pour API
    
    Returns:
        {
            "Anciennete_Paie": 0.463,
            "Anciennete_CSE": 0.337,
            ...
        }
    """
    scorer = RiskScorer()
    return scorer.compute_all_scores(vecteurs_4d, weights_by_usage)


def get_top_priorities(scores: Dict[str, float],
                      top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Récupère top N priorités avec métadonnées enrichies
    
    Returns:
        [
            {
                "attribut": "Anciennete",
                "usage": "Paie",
                "score": 0.463,
                "severite": "CRITIQUE",
                "color": "red",
                "records_affected": 196,
                "impact_mensuel": 45080
            },
            ...
        ]
    """
    scorer = RiskScorer()
    ranked = scorer.rank_scores_by_risk(scores, top_n)
    
    priorities = []
    for key, score, severite in ranked:
        # Parser clé
        parts = key.rsplit('_', 1)
        attribut = parts[0] if len(parts) > 1 else key
        usage = parts[1] if len(parts) > 1 else "Unknown"
        
        # Impact business
        impact = scorer.compute_impact_business(score, attribut, usage)
        
        priorities.append({
            "attribut": attribut,
            "usage": usage,
            "score": score,
            "severite": severite,
            "color": scorer.get_risk_color(score),
            "records_affected": impact["records_affected"],
            "impact_mensuel": impact["impact_financier_mensuel"],
            "actions": impact["actions_recommandees"]
        })
    
    return priorities


if __name__ == "__main__":
    # Test risk scoring
    scorer = RiskScorer()
    
    print("="*80)
    print("TEST MODULE RISK_SCORER")
    print("="*80)
    
    # Test 1: Score simple
    print("\n1. Score risque 'Anciennete × Paie':")
    vector = {
        "P_DB": 0.99,
        "P_DP": 0.02,
        "P_BR": 0.20,
        "P_UP": 0.10
    }
    weights = {
        "w_DB": 0.40,
        "w_DP": 0.30,
        "w_BR": 0.30,
        "w_UP": 0.00
    }
    
    risk = scorer.compute_risk_score(vector, weights)
    severite = scorer.classify_risk(risk)
    color = scorer.get_risk_color(risk)
    
    print(f"   R = 0.40×0.99 + 0.30×0.02 + 0.30×0.20 + 0.00×0.10 = {risk}")
    print(f"   Sévérité: {severite} ({color})")
    
    # Test 2: Matrice complète
    print("\n2. Matrice scores [Attribut × Usage]:")
    vecteurs = {
        "Anciennete": vector,
        "Dates_promos": {
            "P_DB": 0.364,
            "P_DP": 0.143,
            "P_BR": 0.080,
            "P_UP": 0.300
        }
    }
    
    weights_all = {
        "Paie": {"w_DB": 0.40, "w_DP": 0.30, "w_BR": 0.30, "w_UP": 0.00},
        "CSE": {"w_DB": 0.25, "w_DP": 0.20, "w_BR": 0.30, "w_UP": 0.25},
        "Dashboard": {"w_DB": 0.10, "w_DP": 0.10, "w_BR": 0.20, "w_UP": 0.60}
    }
    
    scores = scorer.compute_all_scores(vecteurs, weights_all)
    for key, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"   {key}: {score:.3f} ({scorer.classify_risk(score)})")
    
    # Test 3: Top priorités
    print("\n3. Top 3 priorités actions:")
    priorities = get_top_priorities(scores, top_n=3)
    for i, p in enumerate(priorities, 1):
        print(f"   {i}. {p['attribut']} × {p['usage']}: {p['score']:.1%} {p['severite']}")
        print(f"      Impact: {p['records_affected']} enreg., {p['impact_mensuel']}€/mois")
        print(f"      Action: {p['actions'][0]}")
