"""
extended_anomaly_catalog.py
Référentiel chargé dynamiquement depuis rules_catalog.yaml

Structure :
- 15 anomalies avec détecteurs RÉELS complets
- Les autres anomalies avec détecteurs TEMPLATES (structure prête)
- Métadonnées (nom, description, criticité, etc.) issues du YAML
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

# Import détecteurs réels du catalogue core
from core_anomaly_catalog import (
    Dimension, Criticality, CoreAnomaly,
    detect_null_in_required,
    detect_pk_duplicates,
    detect_invalid_email,
    detect_out_of_domain,
    detect_negative_values,
    detect_derived_calc_error,
    detect_division_by_zero,
    detect_data_type_mismatch,
    detect_temporal_inconsistency,
    detect_out_of_business_range,
    detect_forbidden_combination,
    detect_mandatory_business_rule,
    detect_obsolete_data,
    detect_excessive_granularity
)

from rules_catalog_loader import catalog as _yaml_catalog


# ============================================================================
# DÉTECTEURS TEMPLATES (pour anomalies 16-60)
# ============================================================================

def detect_template_db(df: pd.DataFrame, **params) -> Dict:
    """Template détecteur DB - À implémenter selon besoin"""
    return {
        'detected': False,
        'affected_rows': 0,
        'note': 'Template - Implémentation progressive',
        'sample': []
    }

def detect_template_dp(df: pd.DataFrame, **params) -> Dict:
    """Template détecteur DP - À implémenter selon besoin"""
    return {
        'detected': False,
        'affected_rows': 0,
        'note': 'Template - Implémentation progressive',
        'sample': []
    }

def detect_template_br(df: pd.DataFrame, **params) -> Dict:
    """Template détecteur BR - À implémenter selon besoin"""
    return {
        'detected': False,
        'affected_rows': 0,
        'note': 'Template - Implémentation progressive',
        'sample': []
    }

def detect_template_up(df: pd.DataFrame, **params) -> Dict:
    """Template détecteur UP - À implémenter selon besoin"""
    return {
        'detected': False,
        'affected_rows': 0,
        'note': 'Template - Implémentation progressive',
        'sample': []
    }


# ============================================================================
# DÉTECTEURS RÉELS mappés par anomaly_id
# ============================================================================

_REAL_DETECTORS: Dict[str, Callable] = {
    "DB#1": detect_null_in_required,
    "DB#2": detect_pk_duplicates,
    "DB#3": detect_invalid_email,
    "DB#4": detect_out_of_domain,
    "DB#5": detect_negative_values,
    "DP#1": detect_derived_calc_error,
    "DP#2": detect_division_by_zero,
    "DP#3": detect_data_type_mismatch,
    "BR#1": detect_temporal_inconsistency,
    "BR#2": detect_out_of_business_range,
    "BR#3": detect_forbidden_combination,
    "BR#4": detect_mandatory_business_rule,
    "UP#1": detect_obsolete_data,
    "UP#2": detect_excessive_granularity,
    "UP#3": lambda df, col, min_unique: {
        'detected': df[col].nunique() < min_unique if col in df.columns else False,
        'affected_rows': len(df) if (col in df.columns and df[col].nunique() < min_unique) else 0,
        'unique_count': df[col].nunique() if col in df.columns else 0,
        'min_expected': min_unique,
        'sample': []
    },
}

_TEMPLATE_DETECTORS: Dict[str, Callable] = {
    "DB": detect_template_db,
    "DP": detect_template_dp,
    "BR": detect_template_br,
    "UP": detect_template_up,
}

_CRITICALITY_MAP = {
    "CRITIQUE": Criticality.CRITIQUE,
    "ÉLEVÉ": Criticality.ÉLEVÉ,
    "MOYEN": Criticality.MOYEN,
    "FAIBLE": Criticality.FAIBLE,
    "VARIABLE": Criticality.MOYEN,
}

_DIMENSION_MAP = {
    "DB": Dimension.DB,
    "DP": Dimension.DP,
    "BR": Dimension.BR,
    "UP": Dimension.UP,
}


def _build_catalog_from_yaml() -> List[CoreAnomaly]:
    """Construit la liste CoreAnomaly depuis le catalogue YAML."""
    anomalies_dict = _yaml_catalog.anomalies
    rule_types = _yaml_catalog.rule_types
    result = []

    for aid, info in anomalies_dict.items():
        dim_str = info.get("dimension", "DB")
        crit_str = info.get("criticality", "MOYEN")

        # Détecteur réel ou template
        detector = _REAL_DETECTORS.get(aid, _TEMPLATE_DETECTORS.get(dim_str, detect_template_db))

        # SQL template depuis le rule_type s'il existe
        rt_key = info.get("default_rule_type", "")
        rt_cfg = rule_types.get(rt_key, {})
        odcs = rt_cfg.get("odcs", {})
        sql_template = odcs.get("query", f"-- {rt_key}")

        # Exemple
        example = info.get("business_risk", info.get("description", ""))

        result.append(CoreAnomaly(
            id=aid,
            dimension=_DIMENSION_MAP.get(dim_str, Dimension.DB),
            name=info.get("name", aid),
            description=info.get("description", ""),
            criticality=_CRITICALITY_MAP.get(crit_str, Criticality.MOYEN),
            woodall_level=info.get("woodall", "SAST"),
            detector=detector,
            sql_template=sql_template,
            example=example,
        ))

    return result


# ============================================================================
# MANAGER ÉTENDU — chargé depuis YAML
# ============================================================================

class ExtendedCatalogManager:
    """Gestionnaire catalogue chargé depuis rules_catalog.yaml"""

    def __init__(self, persistence_file: str = "extended_anomaly_stats.json"):
        self.catalog = _build_catalog_from_yaml()
        self.persistence_file = Path(persistence_file)
        self._load_stats()
    
    def _load_stats(self):
        """Charge stats apprentissage"""
        if self.persistence_file.exists():
            with open(self.persistence_file, 'r') as f:
                stats = json.load(f)
            
            for anomaly in self.catalog:
                if anomaly.id in stats:
                    anomaly.detection_count = stats[anomaly.id]['detection_count']
                    anomaly.scan_count = stats[anomaly.id]['scan_count']
                    anomaly.frequency = stats[anomaly.id]['frequency']
    
    def _save_stats(self):
        """Sauvegarde stats"""
        stats = {}
        for anomaly in self.catalog:
            stats[anomaly.id] = {
                'detection_count': anomaly.detection_count,
                'scan_count': anomaly.scan_count,
                'frequency': anomaly.frequency
            }
        
        with open(self.persistence_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def get_by_id(self, anomaly_id: str) -> Optional[CoreAnomaly]:
        """Récupère anomalie par ID"""
        for anomaly in self.catalog:
            if anomaly.id == anomaly_id:
                return anomaly
        return None
    
    def get_by_dimension(self, dimension: str) -> List[CoreAnomaly]:
        """Filtre par dimension"""
        return [a for a in self.catalog if a.dimension.value == dimension]
    
    def get_top_priority(self, n: int = 10) -> List[CoreAnomaly]:
        """Top N par score priorité adaptatif"""
        sorted_anomalies = sorted(
            self.catalog,
            key=lambda a: a.get_priority_score(),
            reverse=True
        )
        return sorted_anomalies[:n]
    
    def get_real_detectors(self) -> List[CoreAnomaly]:
        """Anomalies avec détecteurs réels (non-templates)"""
        real = []
        for a in self.catalog:
            # Vérifier si le détecteur est un template
            if a.detector.__name__ not in ['detect_template_db', 'detect_template_dp', 
                                          'detect_template_br', 'detect_template_up']:
                real.append(a)
        return real
    
    def update_stats(self, anomaly_id: str, detected: bool):
        """Met à jour stats après scan"""
        anomaly = self.get_by_id(anomaly_id)
        if anomaly:
            anomaly.update_stats(detected)
            self._save_stats()
    
    def get_stats_df(self) -> pd.DataFrame:
        """Stats en DataFrame"""
        data = []
        for a in self.catalog:
            score = a.get_priority_score()
            is_real = a.detector.__name__ not in ['detect_template_db', 'detect_template_dp', 
                                                   'detect_template_br', 'detect_template_up']
            data.append({
                'ID': a.id,
                'Nom': a.name,
                'Dimension': a.dimension.value,
                'Criticité': a.criticality.name,
                'Woodall': a.woodall_level,
                'Type': '✅ Réel' if is_real else '📝 Template',
                'Détections': a.detection_count,
                'Scans': a.scan_count,
                'Fréquence': f"{a.frequency:.1%}" if a.scan_count > 0 else "N/A",
                'Score Priorité': f"{score:.1f}",
                '_score_numeric': score
            })
        
        df = pd.DataFrame(data)
        return df.sort_values('_score_numeric', ascending=False)


if __name__ == "__main__":
    manager = ExtendedCatalogManager()

    print(f"📊 CATALOGUE ÉTENDU - {len(manager.catalog)} ANOMALIES (depuis YAML)")
    print(f"Total: {len(manager.catalog)}")
    print(f"\nPar dimension:")
    for dim in ['DB', 'DP', 'BR', 'UP']:
        count = len(manager.get_by_dimension(dim))
        print(f"  {dim}: {count}")

    print(f"\nDétecteurs réels: {len(manager.get_real_detectors())}")
    print(f"Templates: {len(manager.catalog) - len(manager.get_real_detectors())}")
