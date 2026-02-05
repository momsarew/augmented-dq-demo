"""
scan_to_beta_connector.py
Connecteur entre résultats scan anomalies et calcul vecteurs Beta 4D

Flux:
    Scan anomalies → Détections par dimension → Paramètres α,β → Distributions Beta
"""

import pandas as pd
from typing import Dict, List
from scipy.stats import beta as beta_dist
import numpy as np


def scan_results_to_beta_params(scan_report) -> Dict:
    """
    Convertit résultats scan en paramètres Beta par dimension
    
    Args:
        scan_report: ScanReport depuis AdaptiveScanEngine
    
    Returns:
        Dict avec paramètres Beta:
        {
            'DB': {'alpha': 3, 'beta': 97, 'total': 100},
            'DP': {'alpha': 0, 'beta': 100, 'total': 100},
            ...
        }
    """
    return scan_report.get_beta_parameters()


def compute_beta_vectors_from_scan(scan_report, usage_weights: Dict = None) -> Dict:
    """
    Calcule vecteurs Beta 4D depuis résultats scan
    
    Args:
        scan_report: ScanReport avec détections
        usage_weights: Pondérations usage (optionnel)
    
    Returns:
        Dict avec distributions Beta par dimension
    """
    beta_params = scan_results_to_beta_params(scan_report)
    
    if usage_weights is None:
        usage_weights = {'DB': 0.25, 'DP': 0.25, 'BR': 0.25, 'UP': 0.25}
    
    vectors = {}
    
    for dim in ['DB', 'DP', 'BR', 'UP']:
        params = beta_params[dim]
        
        # Paramètres Beta : alpha = échecs + 1, beta = succès + 1
        alpha = params['alpha'] + 1
        beta_val = params['beta'] + 1
        
        # Distribution Beta
        distribution = beta_dist(alpha, beta_val)
        
        # Statistiques
        mean = distribution.mean()
        std = distribution.std()
        
        # Quantiles
        q05 = distribution.ppf(0.05)
        q50 = distribution.ppf(0.50)
        q95 = distribution.ppf(0.95)
        
        vectors[dim] = {
            'alpha': alpha,
            'beta': beta_val,
            'mean': mean,
            'std': std,
            'quantile_05': q05,
            'quantile_50': q50,
            'quantile_95': q95,
            'weight': usage_weights.get(dim, 0.25),
            'anomalies_detected': params['alpha'],
            'total_rows': params['total_rows']
        }
    
    return vectors


def compute_global_quality_score(beta_vectors: Dict) -> Dict:
    """
    Calcule score qualité global depuis vecteurs Beta
    
    Args:
        beta_vectors: Dict depuis compute_beta_vectors_from_scan()
    
    Returns:
        Dict avec score global et par dimension
    """
    # Score par dimension = moyenne Beta
    dim_scores = {}
    for dim, vec in beta_vectors.items():
        dim_scores[dim] = {
            'score': vec['mean'],
            'confidence': 1 - vec['std'],  # Moins de variance = plus confiant
            'risk_low': 1 - vec['quantile_95'],  # Risque bas
            'risk_high': 1 - vec['quantile_05']  # Risque haut
        }
    
    # Score global pondéré
    global_score = sum(
        beta_vectors[dim]['mean'] * beta_vectors[dim]['weight']
        for dim in beta_vectors
    )
    
    # Variance globale (propagation)
    global_variance = sum(
        (beta_vectors[dim]['std'] * beta_vectors[dim]['weight']) ** 2
        for dim in beta_vectors
    )
    global_std = np.sqrt(global_variance)
    
    return {
        'global_score': global_score,
        'global_std': global_std,
        'global_confidence': 1 - global_std,
        'dimension_scores': dim_scores,
        'interpretation': _interpret_score(global_score)
    }


def _interpret_score(score: float) -> str:
    """Interprète score qualité"""
    if score >= 0.95:
        return "EXCELLENT"
    elif score >= 0.85:
        return "BON"
    elif score >= 0.70:
        return "MOYEN"
    elif score >= 0.50:
        return "FAIBLE"
    else:
        return "CRITIQUE"


def format_beta_for_display(beta_vectors: Dict) -> pd.DataFrame:
    """
    Formate vecteurs Beta pour affichage Streamlit
    
    Returns:
        DataFrame avec colonnes:
        - Dimension
        - Anomalies détectées
        - Score qualité
        - Confiance
        - Intervalle [Q05, Q95]
    """
    data = []
    
    for dim, vec in beta_vectors.items():
        data.append({
            'Dimension': dim,
            'Anomalies': vec['anomalies_detected'],
            'Total lignes': vec['total_rows'],
            'Score qualité': f"{vec['mean']:.2%}",
            'Confiance': f"{(1 - vec['std']):.2%}",
            'Intervalle [5%-95%]': f"[{vec['quantile_05']:.2%}, {vec['quantile_95']:.2%}]",
            'Pondération': f"{vec['weight']:.0%}"
        })
    
    return pd.DataFrame(data)


# ============================================================================
# EXEMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("📊 TEST CONNECTEUR SCAN → BETA")
    
    # Simuler résultats scan
    class MockScanReport:
        def __init__(self):
            self.total_rows = 1000
            self.results = []
        
        def get_beta_parameters(self):
            return {
                'DB': {'alpha': 25, 'beta': 975, 'total_rows': 1000},
                'DP': {'alpha': 0, 'beta': 1000, 'total_rows': 1000},
                'BR': {'alpha': 12, 'beta': 988, 'total_rows': 1000},
                'UP': {'alpha': 5, 'beta': 995, 'total_rows': 1000}
            }
    
    mock_report = MockScanReport()
    
    # Calculer vecteurs Beta
    vectors = compute_beta_vectors_from_scan(mock_report)
    
    print("\n🎯 VECTEURS BETA PAR DIMENSION:")
    for dim, vec in vectors.items():
        print(f"\n{dim}:")
        print(f"  Anomalies: {vec['anomalies_detected']}")
        print(f"  Score: {vec['mean']:.2%}")
        print(f"  IC95%: [{vec['quantile_05']:.2%}, {vec['quantile_95']:.2%}]")
    
    # Score global
    global_quality = compute_global_quality_score(vectors)
    
    print(f"\n📊 SCORE GLOBAL:")
    print(f"  Score: {global_quality['global_score']:.2%}")
    print(f"  Confiance: {global_quality['global_confidence']:.2%}")
    print(f"  Interprétation: {global_quality['interpretation']}")
    
    # DataFrame
    df = format_beta_for_display(vectors)
    print(f"\n📋 TABLEAU:")
    print(df.to_string(index=False))
