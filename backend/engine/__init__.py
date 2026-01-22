"""
Framework Probabiliste DQ - Moteur de calcul
"""

from .analyzer import analyze_dataset, detect_type_errors, detect_business_violations
from .beta_calculator import BetaCalculator, compute_all_beta_vectors
from .ahp_elicitor import AHPElicitor, elicit_weights_auto
from .risk_scorer import RiskScorer, compute_risk_scores, get_top_priorities
from .lineage_propagator import LineagePropagator, simulate_lineage
from .comparator import Comparator, DAMACalculator, compare_dama_vs_probabiliste

__all__ = [
    'analyze_dataset',
    'BetaCalculator',
    'compute_all_beta_vectors',
    'AHPElicitor',
    'elicit_weights_auto',
    'RiskScorer',
    'compute_risk_scores',
    'get_top_priorities',
    'LineagePropagator',
    'simulate_lineage',
    'Comparator',
    'DAMACalculator',
    'compare_dama_vs_probabiliste'
]

__version__ = '1.0.0'
