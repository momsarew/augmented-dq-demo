"""
Module d'analyse exploratoire de datasets
Extrait statistiques descriptives pour calcul Beta
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import re


def analyze_dataset(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
    """
    Analyse exploratoire complète d'un dataset
    
    Args:
        df: DataFrame pandas
        columns: Liste colonnes à analyser
    
    Returns:
        Dict avec stats par colonne:
        {
            "colonne1": {
                "dtype": "object",
                "total_rows": 687,
                "null_count": 0,
                "null_rate": 0.0,
                "unique_count": 303,
                "sample_values": [...],
                "type_errors": {...},
                "business_violations": {...}
            },
            ...
        }
    """
    stats = {}
    
    for col in columns:
        if col not in df.columns:
            stats[col] = {"error": f"Colonne '{col}' inexistante"}
            continue
        
        series = df[col]
        
        # Stats de base
        base_stats = {
            "dtype": str(series.dtype),
            "total_rows": len(series),
            "null_count": int(series.isnull().sum()),
            "null_rate": float(series.isnull().sum() / len(series)),
            "unique_count": int(series.nunique()),
            "sample_values": series.dropna().head(5).tolist()
        }
        
        # Détection erreurs type
        type_errors = detect_type_errors(series)
        
        # Détection violations métier
        business_violations = detect_business_violations(series, col)
        
        # Assembler
        stats[col] = {
            **base_stats,
            "type_errors": type_errors,
            "business_violations": business_violations
        }
    
    return stats


def detect_type_errors(series: pd.Series) -> Dict[str, Any]:
    """
    Détecte erreurs de type/parsing dans une colonne
    
    Patterns détectés:
    - Virgules dans nombres (ex: '7,21' au lieu 7.21)
    - Formats hétérogènes dates
    - Caractères invalides
    
    Returns:
        {
            "error_count": 141,
            "error_rate": 0.205,
            "patterns": ["virgule_decimale", "format_mixte"],
            "examples": [...]
        }
    """
    errors = {
        "error_count": 0,
        "error_rate": 0.0,
        "patterns": [],
        "examples": []
    }
    
    if series.dtype == 'object':
        # Détecter virgules dans colonnes supposées numériques
        if series.name and any(kw in series.name.lower() for kw in ['anciennete', 'salaire', 'montant', 'taux']):
            comma_count = series.astype(str).str.contains(',', na=False).sum()
            if comma_count > 0:
                errors["error_count"] += comma_count
                errors["patterns"].append("virgule_decimale")
                errors["examples"].extend(
                    series[series.astype(str).str.contains(',', na=False)].head(3).tolist()
                )
        
        # Détecter formats dates hétérogènes
        if series.name and any(kw in series.name.lower() for kw in ['date', 'datetime', 'time']):
            # Tenter parse différents formats
            formats_detected = set()
            for val in series.dropna().head(100):
                val_str = str(val)
                if re.match(r'\d{2}/\d{2}/\d{4}', val_str):
                    formats_detected.add("DD/MM/YYYY")
                elif re.match(r'\d{4}-\d{2}-\d{2}', val_str):
                    formats_detected.add("YYYY-MM-DD")
                elif 'T' in val_str:
                    formats_detected.add("ISO8601")
            
            if len(formats_detected) > 1:
                errors["error_count"] += len(series)  # Approximation
                errors["patterns"].append("format_mixte")
                errors["examples"].extend(series.dropna().head(3).tolist())
    
    errors["error_rate"] = errors["error_count"] / len(series) if len(series) > 0 else 0.0
    
    return errors


def detect_business_violations(series: pd.Series, col_name: str) -> Dict[str, Any]:
    """
    Détecte violations règles métier spécifiques
    
    Règles implémentées:
    - Dates futures (pour dates passées attendues)
    - Valeurs négatives (montants, ancienneté)
    - Incohérences logiques
    
    Returns:
        {
            "violation_count": 8,
            "violation_rate": 0.012,
            "rules_violated": ["dates_futures", "valeurs_negatives"],
            "examples": [...]
        }
    """
    violations = {
        "violation_count": 0,
        "violation_rate": 0.0,
        "rules_violated": [],
        "examples": []
    }
    
    # Règle 1: Dates futures (pour colonnes date historiques)
    if 'date' in col_name.lower() and 'debut' in col_name.lower():
        try:
            dates = pd.to_datetime(series, errors='coerce')
            future_dates = dates > pd.Timestamp.now()
            future_count = future_dates.sum()
            
            if future_count > 0:
                violations["violation_count"] += future_count
                violations["rules_violated"].append("dates_futures")
                violations["examples"].extend(
                    series[future_dates].head(3).tolist()
                )
        except:
            pass
    
    # Règle 2: Valeurs négatives (ancienneté, montants)
    if series.dtype in ['int64', 'float64'] or col_name.lower() in ['anciennete', 'salaire']:
        try:
            numeric = pd.to_numeric(series, errors='coerce')
            negative_count = (numeric < 0).sum()
            
            if negative_count > 0:
                violations["violation_count"] += negative_count
                violations["rules_violated"].append("valeurs_negatives")
                violations["examples"].extend(
                    series[numeric < 0].head(3).tolist()
                )
        except:
            pass
    
    # Règle 3: Incohérences ancienneté (si colonne Anciennete)
    # Vérification RÉELLE: valeurs d'ancienneté > 50 ans ou < 0 sont incohérentes
    if 'anciennete' in col_name.lower():
        try:
            # Convertir en numérique (gérer virgules françaises)
            numeric_values = series.astype(str).str.replace(',', '.').str.strip()
            numeric_values = pd.to_numeric(numeric_values, errors='coerce')

            # Compter incohérences réelles: < 0 ou > 50 ans
            incoherent = ((numeric_values < 0) | (numeric_values > 50)).sum()
            if incoherent > 0:
                violations["violation_count"] += int(incoherent)
                violations["rules_violated"].append("anciennete_hors_limites")
        except:
            pass
    
    violations["violation_rate"] = violations["violation_count"] / len(series) if len(series) > 0 else 0.0
    
    return violations


def compute_column_quality_metrics(series: pd.Series) -> Dict[str, float]:
    """
    Calcule métriques qualité basiques pour une colonne
    
    Returns:
        {
            "completeness": 0.98,
            "uniqueness": 0.44,
            "consistency": 0.95,
            "validity": 0.88
        }
    """
    total = len(series)
    
    # Complétude
    completeness = 1 - (series.isnull().sum() / total) if total > 0 else 0.0
    
    # Unicité DAMA : 1 - (nb_doublons / total)
    # Si toutes les valeurs sont uniques → 100%
    # Si toutes les valeurs sont identiques → ~0%
    if total > 0:
        duplicated_count = series.duplicated(keep='first').sum()
        uniqueness = 1.0 - (duplicated_count / total)
    else:
        uniqueness = 0.0
    
    # Cohérence (approximation basée sur type)
    consistency = 1.0  # Par défaut
    if series.dtype == 'object':
        # Checker formats cohérents
        sample = series.dropna().head(100)
        if len(sample) > 0:
            # Exemple: dates doivent avoir même format
            formats_count = len(set([type(x) for x in sample]))
            consistency = 1.0 / formats_count if formats_count > 0 else 1.0
    
    # Validité - Calculée depuis les vraies données
    # Validité = proportion de valeurs qui respectent le format/type attendu
    type_errors = detect_type_errors(series)
    validity = 1.0 - type_errors['error_rate']  # DONNÉES RÉELLES
    
    return {
        "completeness": round(completeness, 4),
        "uniqueness": round(uniqueness, 4),
        "consistency": round(consistency, 4),
        "validity": round(validity, 4)
    }


if __name__ == "__main__":
    # Test avec dataset exemple
    import sys
    sys.path.append('/mnt/user-data/uploads')
    
    # Charger dataset RH
    df = pd.read_excel('/mnt/user-data/uploads/Augmented_DQ_-_Dataset.xlsx')
    
    # Analyser colonnes critiques
    columns = ['Anciennete', 'Dates promos', 'Date début dernier contrat', 'LEVEL ACN']
    
    stats = analyze_dataset(df, columns)
    
    print("="*80)
    print("ANALYSE EXPLORATOIRE")
    print("="*80)
    
    for col, stat in stats.items():
        print(f"\n{col}:")
        print(f"  Type: {stat['dtype']}")
        print(f"  Nulls: {stat['null_count']}/{stat['total_rows']} ({stat['null_rate']:.1%})")
        print(f"  Erreurs type: {stat['type_errors']['error_count']} ({stat['type_errors']['error_rate']:.1%})")
        print(f"  Violations métier: {stat['business_violations']['violation_count']} ({stat['business_violations']['violation_rate']:.1%})")
