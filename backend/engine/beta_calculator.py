"""
Module de calcul des distributions Beta bayésiennes
Convertit taux d'erreur observés en Beta(α, β) avec incertitude quantifiée
"""

import numpy as np
from scipy.stats import beta as beta_dist
from typing import Dict, List, Tuple, Any
import pandas as pd


class BetaCalculator:
    """
    Calculateur de distributions Beta pour dimensions DQ
    """
    
    # Mapping confidence → nombre observations équivalentes
    CONFIDENCE_MAP = {
        'HIGH': 100,
        'MEDIUM': 50,
        'LOW': 20
    }
    
    def __init__(self):
        pass
    
    def compute_beta_params(self, 
                           error_rate: float, 
                           confidence_level: str = 'HIGH',
                           n_obs_equivalent: int = None) -> Dict[str, float]:
        """
        Convertit taux erreur observé → Beta(α, β)
        
        Args:
            error_rate: Taux erreur (0.0 à 1.0)
            confidence_level: 'HIGH', 'MEDIUM', 'LOW'
            n_obs_equivalent: Override nombre observations équivalentes
        
        Returns:
            {
                "alpha": 2.0,
                "beta": 98.0,
                "E_P": 0.020,
                "std": 0.014,
                "confidence": "HIGH",
                "n_obs_equiv": 100,
                "ci_lower": 0.005,
                "ci_upper": 0.045
            }
        """
        # Clamp error_rate
        error_rate = max(0.0001, min(0.9999, error_rate))
        
        # Déterminer n observations équivalentes
        n = n_obs_equivalent or self.CONFIDENCE_MAP.get(confidence_level, 50)
        
        # Calcul paramètres Beta
        alpha = error_rate * n
        beta_param = (1 - error_rate) * n
        
        # Créer distribution
        dist = beta_dist(alpha, beta_param)
        
        # Stats distribution
        mean = dist.mean()
        std = dist.std()
        
        # Intervalle confiance 95%
        ci_lower, ci_upper = dist.ppf([0.025, 0.975])
        
        return {
            "alpha": round(alpha, 2),
            "beta": round(beta_param, 2),
            "E_P": round(mean, 4),
            "std": round(std, 4),
            "confidence": confidence_level,
            "n_obs_equiv": n,
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4)
        }
    
    def compute_4d_vector(self,
                         P_DB: float,
                         P_DP: float,
                         P_BR: float,
                         P_UP: float,
                         confidence_DB: str = 'HIGH',
                         confidence_DP: str = 'HIGH',
                         confidence_BR: str = 'HIGH',
                         confidence_UP: str = 'MEDIUM') -> Dict[str, Any]:
        """
        Calcule vecteur 4D complet pour un attribut
        
        Args:
            P_DB: Taux erreur Database
            P_DP: Taux erreur Data Processing
            P_BR: Taux erreur Business Rules
            P_UP: Taux erreur Usage-fit
            confidence_*: Niveaux confiance par dimension
        
        Returns:
            {
                "P_DB": 0.99, "alpha_DB": 99, "beta_DB": 1, ...
                "P_DP": 0.02, "alpha_DP": 2, "beta_DP": 98, ...
                "P_BR": 0.20, "alpha_BR": 20, "beta_BR": 80, ...
                "P_UP": 0.10, "alpha_UP": 5, "beta_UP": 45, ...
            }
        """
        vector = {}
        
        # DB dimension
        db = self.compute_beta_params(P_DB, confidence_DB)
        vector.update({
            "P_DB": db["E_P"],
            "alpha_DB": db["alpha"],
            "beta_DB": db["beta"],
            "std_DB": db["std"],
            "confidence_DB": db["confidence"],
            "ci_lower_DB": db["ci_lower"],
            "ci_upper_DB": db["ci_upper"]
        })
        
        # DP dimension
        dp = self.compute_beta_params(P_DP, confidence_DP)
        vector.update({
            "P_DP": dp["E_P"],
            "alpha_DP": dp["alpha"],
            "beta_DP": dp["beta"],
            "std_DP": dp["std"],
            "confidence_DP": dp["confidence"],
            "ci_lower_DP": dp["ci_lower"],
            "ci_upper_DP": dp["ci_upper"]
        })
        
        # BR dimension
        br = self.compute_beta_params(P_BR, confidence_BR)
        vector.update({
            "P_BR": br["E_P"],
            "alpha_BR": br["alpha"],
            "beta_BR": br["beta"],
            "std_BR": br["std"],
            "confidence_BR": br["confidence"],
            "ci_lower_BR": br["ci_lower"],
            "ci_upper_BR": br["ci_upper"]
        })
        
        # UP dimension
        up = self.compute_beta_params(P_UP, confidence_UP)
        vector.update({
            "P_UP": up["E_P"],
            "alpha_UP": up["alpha"],
            "beta_UP": up["beta"],
            "std_UP": up["std"],
            "confidence_UP": up["confidence"],
            "ci_lower_UP": up["ci_lower"],
            "ci_upper_UP": up["ci_upper"]
        })
        
        return vector


def compute_all_beta_vectors(df: pd.DataFrame, 
                             columns: List[str],
                             stats: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Calcule vecteurs 4D pour tous attributs
    
    Args:
        df: DataFrame pandas
        columns: Liste colonnes à analyser
        stats: Stats exploratoires (depuis analyzer.py)
    
    Returns:
        {
            "Anciennete": {
                "P_DB": 0.99, "alpha_DB": 99, ...
                "P_DP": 0.02, "alpha_DP": 2, ...
            },
            "Dates_promos": { ... },
            ...
        }
    """
    calculator = BetaCalculator()
    vectors = {}
    
    for col in columns:
        if col not in stats:
            continue
        
        col_stats = stats[col]
        
        # Extraire taux erreur par dimension
        
        # [DB] Database - Basé sur nulls + type inconsistencies
        P_DB = col_stats['null_rate']
        if col_stats['dtype'] == 'object' and 'anciennete' in col.lower():
            # VARCHAR au lieu DECIMAL = 100% non-conforme structurellement
            P_DB = max(P_DB, 0.99)
        
        # [DP] Data Processing - Basé sur erreurs parsing
        P_DP = col_stats['type_errors']['error_rate']
        if P_DP == 0:
            P_DP = 0.02  # Baseline ETL (estimation conservatrice)
        
        # [BR] Business Rules - Basé sur violations métier
        P_BR = col_stats['business_violations']['violation_rate']
        if P_BR == 0:
            P_BR = 0.05  # Baseline (estimation)
        
        # [UP] Usage-fit - À éliciter (placeholder)
        # En prod, serait fourni par AHP ou élicitation IA
        P_UP = 0.10  # Default
        
        # Calculer vecteur 4D
        vector = calculator.compute_4d_vector(
            P_DB=P_DB,
            P_DP=P_DP,
            P_BR=P_BR,
            P_UP=P_UP,
            confidence_DB='HIGH',
            confidence_DP='HIGH' if P_DP > 0.1 else 'MEDIUM',
            confidence_BR='HIGH' if P_BR > 0.1 else 'MEDIUM',
            confidence_UP='MEDIUM'
        )
        
        vectors[col] = vector
    
    return vectors


def update_beta_with_new_evidence(current_alpha: float,
                                   current_beta: float,
                                   new_successes: int,
                                   new_failures: int) -> Tuple[float, float]:
    """
    Mise à jour bayésienne d'une distribution Beta avec nouvelles observations
    
    Formule: Beta(α', β') = Beta(α + successes, β + failures)
    
    Args:
        current_alpha: α actuel
        current_beta: β actuel
        new_successes: Nouvelles observations "qualité OK"
        new_failures: Nouvelles observations "erreurs"
    
    Returns:
        (new_alpha, new_beta)
    """
    new_alpha = current_alpha + new_failures  # Erreurs augmentent α
    new_beta = current_beta + new_successes   # Succès augmentent β
    
    return (new_alpha, new_beta)


def sample_from_beta(alpha: float, beta: float, n_samples: int = 1000) -> np.ndarray:
    """
    Échantillonne distribution Beta(α, β)
    Utile pour simulations Monte Carlo
    
    Returns:
        Array de n_samples valeurs entre 0 et 1
    """
    return np.random.beta(alpha, beta, size=n_samples)


if __name__ == "__main__":
    # Test calculs Beta
    calc = BetaCalculator()
    
    print("="*80)
    print("TEST MODULE BETA_CALCULATOR")
    print("="*80)
    
    # Test 1: Paramètres simples
    print("\n1. Beta(2%, HIGH confidence):")
    result = calc.compute_beta_params(0.02, 'HIGH')
    print(f"   Beta({result['alpha']}, {result['beta']}) → E[P]={result['E_P']:.3f} ±{result['std']:.3f}")
    print(f"   IC 95%: [{result['ci_lower']:.3f}, {result['ci_upper']:.3f}]")
    
    # Test 2: Vecteur 4D complet
    print("\n2. Vecteur 4D 'Anciennete':")
    vector = calc.compute_4d_vector(
        P_DB=0.99,
        P_DP=0.02,
        P_BR=0.20,
        P_UP=0.10
    )
    print(f"   [DB] Beta({vector['alpha_DB']}, {vector['beta_DB']}) → {vector['P_DB']:.3f}")
    print(f"   [DP] Beta({vector['alpha_DP']}, {vector['beta_DP']}) → {vector['P_DP']:.3f}")
    print(f"   [BR] Beta({vector['alpha_BR']}, {vector['beta_BR']}) → {vector['P_BR']:.3f}")
    print(f"   [UP] Beta({vector['alpha_UP']}, {vector['beta_UP']}) → {vector['P_UP']:.3f}")
    
    # Test 3: Mise à jour bayésienne
    print("\n3. Mise à jour bayésienne:")
    print(f"   Initial: Beta(2, 98)")
    new_alpha, new_beta = update_beta_with_new_evidence(2, 98, 90, 10)
    print(f"   Après 100 nouvelles obs (10 erreurs): Beta({new_alpha}, {new_beta})")
    print(f"   Nouvelle moyenne: {new_alpha/(new_alpha+new_beta):.3f}")
