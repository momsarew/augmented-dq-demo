"""
Module de propagation du risque le long du lineage
Formule convolution bayésienne: P_d(N) ≈ 1 - ∏(1 - P_d(i))
"""

from typing import Dict, List, Tuple, Any
import numpy as np


class LineagePropagator:
    """
    Propagateur de risque le long des pipelines de transformation
    """
    
    def __init__(self):
        pass
    
    def propagate_dimension(self,
                           P_initial: float,
                           transformations: List[Dict[str, float]]) -> List[float]:
        """
        Propage risque d'une dimension le long d'un pipeline
        
        Formule: P_d(étape_N) ≈ 1 - ∏(i=0 to N) (1 - P_d(étape_i))
        
        Args:
            P_initial: Probabilité initiale (source)
            transformations: Liste dicts {"nom": "ETL", "P_add": 0.05}
        
        Returns:
            [P_0, P_1, P_2, ..., P_N] (historique propagation)
        """
        propagation = [P_initial]
        P_current = P_initial
        
        for transfo in transformations:
            P_add = transfo.get('P_add', 0.0)
            
            # Convolution (approximation indépendance)
            P_new = 1 - (1 - P_current) * (1 - P_add)
            
            propagation.append(P_new)
            P_current = P_new
        
        return propagation
    
    def simulate_pipeline_propagation(self,
                                     vector_4d_source: Dict[str, float],
                                     pipeline: List[Dict]) -> Dict[str, Any]:
        """
        Simule propagation complète vecteur 4D le long d'un pipeline
        
        Args:
            vector_4d_source: Vecteur initial
                {"P_DB": 0.99, "P_DP": 0.02, "P_BR": 0.20, "P_UP": 0.10}
            
            pipeline: Liste étapes avec risques additionnels par dimension
                [
                    {
                        "nom": "ETL Extraction",
                        "P_DB_add": 0.0,
                        "P_DP_add": 0.05,
                        "P_BR_add": 0.0,
                        "P_UP_add": 0.0
                    },
                    {
                        "nom": "Enrichissement",
                        "P_DP_add": 0.0,
                        "P_BR_add": 0.02,
                        ...
                    },
                    ...
                ]
        
        Returns:
            {
                "vector_final": {"P_DB": 0.99, "P_DP": 0.152, ...},
                "degradation": {
                    "P_DB": 0.0,
                    "P_DP": 0.132,
                    "P_BR": 0.016,
                    "P_UP": 0.0
                },
                "history": [
                    {"etape": "Source", "P_DB": 0.99, ...},
                    {"etape": "ETL", "P_DB": 0.99, ...},
                    ...
                ]
            }
        """
        # Initialiser historique
        history = [{
            "etape": "Source SIRH",
            "P_DB": vector_4d_source['P_DB'],
            "P_DP": vector_4d_source['P_DP'],
            "P_BR": vector_4d_source['P_BR'],
            "P_UP": vector_4d_source['P_UP']
        }]
        
        # Propager chaque dimension
        P_DB = vector_4d_source['P_DB']
        P_DP = vector_4d_source['P_DP']
        P_BR = vector_4d_source['P_BR']
        P_UP = vector_4d_source['P_UP']
        
        for step in pipeline:
            # Ajouter risques additionnels
            P_DB = 1 - (1 - P_DB) * (1 - step.get('P_DB_add', 0.0))
            P_DP = 1 - (1 - P_DP) * (1 - step.get('P_DP_add', 0.0))
            P_BR = 1 - (1 - P_BR) * (1 - step.get('P_BR_add', 0.0))
            P_UP = 1 - (1 - P_UP) * (1 - step.get('P_UP_add', 0.0))
            
            history.append({
                "etape": step['nom'],
                "P_DB": round(P_DB, 4),
                "P_DP": round(P_DP, 4),
                "P_BR": round(P_BR, 4),
                "P_UP": round(P_UP, 4)
            })
        
        # Calculer dégradation
        degradation = {
            "P_DB": round(P_DB - vector_4d_source['P_DB'], 4),
            "P_DP": round(P_DP - vector_4d_source['P_DP'], 4),
            "P_BR": round(P_BR - vector_4d_source['P_BR'], 4),
            "P_UP": round(P_UP - vector_4d_source['P_UP'], 4)
        }
        
        return {
            "vector_final": {
                "P_DB": round(P_DB, 4),
                "P_DP": round(P_DP, 4),
                "P_BR": round(P_BR, 4),
                "P_UP": round(P_UP, 4)
            },
            "degradation": degradation,
            "history": history
        }
    
    def compute_risk_delta(self,
                          risk_source: float,
                          risk_final: float) -> Dict[str, Any]:
        """
        Calcule delta risque décisionnel après propagation
        
        Returns:
            {
                "risk_source": 0.463,
                "risk_final": 0.507,
                "delta_absolute": 0.044,
                "delta_relative": 0.096,
                "interpretation": "..."
            }
        """
        delta_abs = risk_final - risk_source
        delta_rel = (delta_abs / risk_source) if risk_source > 0 else 0.0
        
        # Interprétation
        if delta_abs > 0.10:
            interpretation = "⚠️ DÉGRADATION MAJEURE - Action corrective URGENTE"
        elif delta_abs > 0.05:
            interpretation = "⚠️ Dégradation significative - Surveillance renforcée"
        elif delta_abs > 0.01:
            interpretation = "⚡ Dégradation mineure - Monitoring continu"
        elif delta_abs > -0.01:
            interpretation = "➡️ STABLE - Qualité préservée"
        else:
            interpretation = "✅ AMÉLIORATION - Pipeline ajoute contrôles qualité"
        
        return {
            "risk_source": round(risk_source, 4),
            "risk_final": round(risk_final, 4),
            "delta_absolute": round(delta_abs, 4),
            "delta_relative": round(delta_rel, 4),
            "interpretation": interpretation
        }


def simulate_lineage(vector_4d_source: Dict[str, float],
                    weights_usage: Dict[str, float],
                    pipeline_config: List[Dict] = None) -> Dict[str, Any]:
    """
    Fonction utilitaire: simulation complète lineage pour API
    
    Si pipeline_config non fourni, utilise pipeline démo (calcul paie)
    
    Returns:
        {
            "pipeline": [...],
            "vector_final": {...},
            "degradation": {...},
            "risk_source": 0.463,
            "risk_final": 0.507,
            "delta": {...}
        }
    """
    # Pipeline par défaut: Calcul prime ancienneté
    if pipeline_config is None:
        pipeline_config = [
            {
                "nom": "ETL Extraction",
                "description": "Conversion VARCHAR → DECIMAL",
                "P_DB_add": 0.0,
                "P_DP_add": 0.05,  # Parsing virgule→point
                "P_BR_add": 0.0,
                "P_UP_add": 0.0
            },
            {
                "nom": "Enrichissement Métier",
                "description": "Calcul barème (si Ancienneté ≥5: prime = 0.03×salaire)",
                "P_DB_add": 0.0,
                "P_DP_add": 0.0,
                "P_BR_add": 0.02,  # Erreurs règle barème
                "P_UP_add": 0.0
            },
            {
                "nom": "Agrégation Paie",
                "description": "JOIN salaires + Calcul final",
                "P_DB_add": 0.0,
                "P_DP_add": 0.08,  # Matricules mal formés
                "P_BR_add": 0.0,
                "P_UP_add": 0.0
            },
            {
                "nom": "Calcul Final",
                "description": "Somme primes",
                "P_DB_add": 0.0,
                "P_DP_add": 0.01,  # Arrondis
                "P_BR_add": 0.0,
                "P_UP_add": 0.0
            }
        ]
    
    propagator = LineagePropagator()
    
    # Propager vecteur
    propagation = propagator.simulate_pipeline_propagation(
        vector_4d_source,
        pipeline_config
    )
    
    # Calculer risques décisionnels
    from .risk_scorer import RiskScorer
    scorer = RiskScorer()
    
    risk_source = scorer.compute_risk_score(vector_4d_source, weights_usage)
    risk_final = scorer.compute_risk_score(propagation['vector_final'], weights_usage)
    
    # Delta
    delta = propagator.compute_risk_delta(risk_source, risk_final)
    
    return {
        "pipeline": pipeline_config,
        "vector_source": vector_4d_source,
        "vector_final": propagation['vector_final'],
        "degradation": propagation['degradation'],
        "history": propagation['history'],
        "risk_source": risk_source,
        "risk_final": risk_final,
        "delta": delta
    }


if __name__ == "__main__":
    # Test propagation
    propagator = LineagePropagator()
    
    print("="*80)
    print("TEST MODULE LINEAGE_PROPAGATOR")
    print("="*80)
    
    # Test 1: Propagation simple dimension
    print("\n1. Propagation [DP] le long du pipeline:")
    P_init = 0.02
    transfos = [
        {"nom": "ETL", "P_add": 0.05},
        {"nom": "Enrichissement", "P_add": 0.0},
        {"nom": "JOIN", "P_add": 0.08},
        {"nom": "Calcul", "P_add": 0.01}
    ]
    
    propagation = propagator.propagate_dimension(P_init, transfos)
    for i, P in enumerate(propagation):
        etape = "Source" if i == 0 else transfos[i-1]['nom']
        print(f"   {etape}: P_DP = {P:.4f}")
    
    # Test 2: Propagation vecteur 4D complet
    print("\n2. Propagation vecteur 4D 'Ancienneté' (pipeline paie):")
    vector_source = {
        "P_DB": 0.99,
        "P_DP": 0.02,
        "P_BR": 0.20,
        "P_UP": 0.10
    }
    
    pipeline = [
        {"nom": "ETL", "P_DB_add": 0.0, "P_DP_add": 0.05, "P_BR_add": 0.0, "P_UP_add": 0.0},
        {"nom": "Enrichissement", "P_DB_add": 0.0, "P_DP_add": 0.0, "P_BR_add": 0.02, "P_UP_add": 0.0},
        {"nom": "JOIN", "P_DB_add": 0.0, "P_DP_add": 0.08, "P_BR_add": 0.0, "P_UP_add": 0.0},
        {"nom": "Calcul", "P_DB_add": 0.0, "P_DP_add": 0.01, "P_BR_add": 0.0, "P_UP_add": 0.0}
    ]
    
    result = propagator.simulate_pipeline_propagation(vector_source, pipeline)
    
    print("   Vecteur source:")
    print(f"     [DB]={vector_source['P_DB']:.3f}, [DP]={vector_source['P_DP']:.3f}, "
          f"[BR]={vector_source['P_BR']:.3f}, [UP]={vector_source['P_UP']:.3f}")
    
    print("   Vecteur final:")
    final = result['vector_final']
    print(f"     [DB]={final['P_DB']:.3f}, [DP]={final['P_DP']:.3f}, "
          f"[BR]={final['P_BR']:.3f}, [UP]={final['P_UP']:.3f}")
    
    print("   Dégradation:")
    deg = result['degradation']
    print(f"     [DB]=+{deg['P_DB']:.3f}, [DP]=+{deg['P_DP']:.3f}, "
          f"[BR]=+{deg['P_BR']:.3f}, [UP]=+{deg['P_UP']:.3f}")
    
    # Test 3: Delta risque décisionnel
    print("\n3. Impact sur risque décisionnel (usage Paie):")
    weights = {"w_DB": 0.40, "w_DP": 0.30, "w_BR": 0.30, "w_UP": 0.00}
    
    risk_source = 0.40*0.99 + 0.30*0.02 + 0.30*0.20 + 0.00*0.10
    risk_final = 0.40*final['P_DB'] + 0.30*final['P_DP'] + 0.30*final['P_BR'] + 0.00*final['P_UP']
    
    delta = propagator.compute_risk_delta(risk_source, risk_final)
    print(f"   Risque source: {delta['risk_source']:.1%}")
    print(f"   Risque final: {delta['risk_final']:.1%}")
    print(f"   Delta: +{delta['delta_absolute']:.3f} (+{delta['delta_relative']:.1%})")
    print(f"   {delta['interpretation']}")
