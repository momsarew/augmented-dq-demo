# backend/engine/__init__.py
from __future__ import annotations

from typing import Dict, List, Any, Optional
import pandas as pd

# ---------------------------------------------------------------------
# Tentative d'import des implémentations réelles si elles existent
# ---------------------------------------------------------------------
_IMPLEMENTATION_OK = True
_IMPORT_ERROR = None

try:
    # Si tu as déjà ces fichiers, garde cette structure.
    # Sinon, le fallback ci-dessous prendra le relais.
    from .analyzer import analyze_dataset  # type: ignore
    from .beta_calculator import compute_all_beta_vectors  # type: ignore
    from .ahp_elicitor import elicit_weights_auto  # type: ignore
    from .risk_scorer import compute_risk_scores, get_top_priorities  # type: ignore
    from .lineage_propagator import simulate_lineage  # type: ignore
    from .comparator import compare_dama_vs_probabiliste  # type: ignore
except Exception as e:
    _IMPLEMENTATION_OK = False
    _IMPORT_ERROR = str(e)

# ---------------------------------------------------------------------
# Fallbacks minimaux (permettent à l’app de tourner si modules manquants)
# ---------------------------------------------------------------------
if not _IMPLEMENTATION_OK:

    def analyze_dataset(df: pd.DataFrame, selected_columns: List[str]) -> Dict[str, Any]:
        """
        Analyse simple: stats de base par colonne.
        """
        stats: Dict[str, Any] = {}
        for col in selected_columns:
            s = df[col]
            stats[col] = {
                "n_rows": int(len(df)),
                "null_count": int(s.isna().sum()),
                "null_rate": float(s.isna().mean()) if len(df) else 0.0,
                "n_unique": int(s.nunique(dropna=True)),
                "dtype": str(s.dtype),
            }
        return stats

    def compute_all_beta_vectors(df: pd.DataFrame, selected_columns: List[str], stats: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """
        Vecteurs 4D simplifiés:
        - DB: basé sur null_rate
        - DP: basé sur type coercion fail rate (heuristique légère)
        - BR: basé sur outliers (heuristique quantiles sur numériques)
        - UP: basé sur cardinalité (unique ratio)
        """
        vectors: Dict[str, Dict[str, float]] = {}
        n = len(df) if len(df) else 1

        for col in selected_columns:
            s = df[col]
            null_rate = float(s.isna().mean()) if len(df) else 0.0

            # DP heuristic: conversion numeric fail rate si colonne object
            dp_rate = 0.0
            if s.dtype == "object":
                coerced = pd.to_numeric(s, errors="coerce")
                dp_rate = float(coerced.isna().mean()) if len(coerced) else 0.0

            # BR heuristic: outliers sur numériques
            br_rate = 0.0
            if pd.api.types.is_numeric_dtype(s):
                q01 = s.quantile(0.01)
                q99 = s.quantile(0.99)
                br_rate = float(((s < q01) | (s > q99)).mean()) if len(s) else 0.0

            # UP heuristic: unique ratio
            up_rate = float(s.nunique(dropna=True) / n) if n else 0.0
            up_rate = max(0.0, min(up_rate, 1.0))

            # Paramètres Beta simples: alpha=erreurs*n +1, beta=(1-erreurs)*n +1
            def beta_params(p: float) -> Dict[str, float]:
                p = max(0.0, min(p, 1.0))
                alpha = p * n + 1.0
                beta = (1.0 - p) * n + 1.0
                return {"p": p, "alpha": alpha, "beta": beta}

            db = beta_params(null_rate)
            dp = beta_params(dp_rate)
            br = beta_params(br_rate)
            up = beta_params(up_rate)

            vectors[col] = {
                "P_DB": db["p"], "alpha_DB": db["alpha"], "beta_DB": db["beta"],
                "P_DP": dp["p"], "alpha_DP": dp["alpha"], "beta_DP": dp["beta"],
                "P_BR": br["p"], "alpha_BR": br["alpha"], "beta_BR": br["beta"],
                "P_UP": up["p"], "alpha_UP": up["alpha"], "beta_UP": up["beta"],
            }

        return vectors

    def elicit_weights_auto(usages: List[Dict[str, Any]], vecteurs_4d: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """
        Pondérations par usage (fallback):
        - Paie: BR et DB plus forts
        - Reporting: DB/DP équilibrés
        - Dashboard: UP/DP plus forts
        """
        weights: Dict[str, Dict[str, float]] = {}
        for u in usages:
            name = u.get("nom", "Usage")
            utype = u.get("type", "")

            if "paie" in utype:
                w = {"DB": 0.35, "DP": 0.15, "BR": 0.40, "UP": 0.10}
            elif "reporting" in utype:
                w = {"DB": 0.30, "DP": 0.30, "BR": 0.25, "UP": 0.15}
            else:
                w = {"DB": 0.20, "DP": 0.35, "BR": 0.15, "UP": 0.30}

            weights[name] = w
        return weights

    def compute_risk_scores(vecteurs_4d: Dict[str, Dict[str, float]], weights: Dict[str, Dict[str, float]], usages: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Score = somme pondérée des probabilités d’erreur P_DB/P_DP/P_BR/P_UP.
        """
        scores: Dict[str, float] = {}
        for attr, v in vecteurs_4d.items():
            for usage_name, w in weights.items():
                score = (
                    float(v.get("P_DB", 0.0)) * float(w.get("DB", 0.0)) +
                    float(v.get("P_DP", 0.0)) * float(w.get("DP", 0.0)) +
                    float(v.get("P_BR", 0.0)) * float(w.get("BR", 0.0)) +
                    float(v.get("P_UP", 0.0)) * float(w.get("UP", 0.0))
                )
                scores[f"{attr}_{usage_name}"] = max(0.0, min(score, 1.0))
        return scores

    def get_top_priorities(scores: Dict[str, float], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Top N des risques, avec format compatible UI.
        """
        def severity(s: float) -> str:
            if s > 0.4:
                return "CRITIQUE"
            if s > 0.25:
                return "ÉLEVÉ"
            if s > 0.15:
                return "MOYEN"
            return "ACCEPTABLE"

        sorted_items = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        out: List[Dict[str, Any]] = []
        for k, s in sorted_items:
            parts = k.rsplit("_", 1)
            attr = parts[0] if len(parts) == 2 else k
            usage = parts[1] if len(parts) == 2 else "Usage"

            out.append({
                "attribut": attr,
                "usage": usage,
                "score": float(s),
                "severite": severity(float(s)),
                "records_affected": "N/A",
                "actions": [
                    "Qualifier les valeurs en erreur (profiling ciblé).",
                    "Mettre en place une règle de contrôle et un seuil d’alerte.",
                    "Corriger à la source ou dans la chaîne de traitement.",
                ],
            })
        return out

    def simulate_lineage(vector_4d: Dict[str, float], weights_for_usage: Dict[str, float]) -> Dict[str, Any]:
        """
        Simulation simple: risque final = min(1, risque_source * (1 + 0.25)).
        """
        risk_source = (
            float(vector_4d.get("P_DB", 0.0)) * float(weights_for_usage.get("DB", 0.0)) +
            float(vector_4d.get("P_DP", 0.0)) * float(weights_for_usage.get("DP", 0.0)) +
            float(vector_4d.get("P_BR", 0.0)) * float(weights_for_usage.get("BR", 0.0)) +
            float(vector_4d.get("P_UP", 0.0)) * float(weights_for_usage.get("UP", 0.0))
        )
        risk_final = min(1.0, risk_source * 1.25)
        return {
            "risk_source": float(risk_source),
            "risk_final": float(risk_final),
            "delta": {
                "delta_absolute": float(risk_final - risk_source),
                "interpretation": "Propagation simplifiée (fallback).",
            },
        }

    def compare_dama_vs_probabiliste(df: pd.DataFrame, selected_columns: List[str], scores: Dict[str, float], vecteurs_4d: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Score DAMA simplifié: calcul DAMA standard pour chaque colonne.
        Unicité = 1 - (nb_doublons / total) selon norme DAMA
        """
        dama_scores: Dict[str, Any] = {}
        for col in selected_columns:
            s = df[col]
            total = len(df)
            null_rate = float(s.isna().mean()) if total > 0 else 0.0

            # Complétude : % de valeurs non-nulles
            completeness = 1.0 - null_rate

            # Unicité DAMA : 1 - (nb_lignes_dupliquées / total)
            # Si toutes les valeurs sont uniques → 100%
            # Si toutes les valeurs sont identiques → ~0%
            if total > 0:
                duplicated_count = s.duplicated(keep='first').sum()
                uniqueness = 1.0 - (duplicated_count / total)
            else:
                uniqueness = 0.0

            # Les autres dimensions ne sont pas calculables sans métadonnées
            validity = None
            consistency = None
            accuracy = None
            timeliness = None

            # Score global : moyenne des dimensions calculables uniquement
            dims_calculables = [v for v in [completeness, uniqueness] if v is not None]
            score_global = sum(dims_calculables) / len(dims_calculables) if dims_calculables else 0.0

            dama_scores[col] = {
                "completeness": round(completeness, 4),
                "validity": validity,
                "consistency": consistency,
                "accuracy": accuracy,
                "timeliness": timeliness,
                "uniqueness": round(uniqueness, 4),
                "score_global": round(score_global, 4),
                "dimensions_calculables": len(dims_calculables),
                "dimensions_total": 6,
                "note": "Seulement Completeness et Uniqueness calculables sans métadonnées supplémentaires"
            }

        return {"dama_scores": dama_scores, "problemes_masques": []}

# Exports
__all__ = [
    "analyze_dataset",
    "compute_all_beta_vectors",
    "elicit_weights_auto",
    "compute_risk_scores",
    "get_top_priorities",
    "simulate_lineage",
    "compare_dama_vs_probabiliste",
]