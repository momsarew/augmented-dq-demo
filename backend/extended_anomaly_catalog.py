"""
extended_anomaly_catalog.py
Référentiel ÉTENDU : 60 anomalies (15 par dimension)

Structure :
- 15 anomalies avec détecteurs RÉELS complets
- 45 anomalies avec détecteurs TEMPLATES (structure prête)
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
# CATALOGUE ÉTENDU : 60 ANOMALIES
# ============================================================================

EXTENDED_CATALOG = [
    
    # ========================================================================
    # DB : 15 ANOMALIES (5 réelles + 10 templates)
    # ========================================================================
    
    # DB#1-5 : DÉTECTEURS RÉELS
    CoreAnomaly(
        id="DB#1", dimension=Dimension.DB,
        name="NULL dans colonnes obligatoires",
        description="Attributs (1,1) contenant NULL",
        criticality=Criticality.CRITIQUE, woodall_level="SAST",
        detector=detect_null_in_required,
        sql_template="SELECT * FROM {table} WHERE {column} IS NULL",
        example="employee_id NULL → Paie bloquée"
    ),
    
    CoreAnomaly(
        id="DB#2", dimension=Dimension.DB,
        name="Doublons clé primaire",
        description="Violations contrainte PK",
        criticality=Criticality.CRITIQUE, woodall_level="SAMT",
        detector=detect_pk_duplicates,
        sql_template="SELECT {pk}, COUNT(*) FROM {table} GROUP BY {pk} HAVING COUNT(*)>1",
        example="Matricule double → Masse salariale ×2"
    ),
    
    CoreAnomaly(
        id="DB#3", dimension=Dimension.DB,
        name="Formats email invalides",
        description="Email sans @ ou domaine",
        criticality=Criticality.MOYEN, woodall_level="SAST",
        detector=detect_invalid_email,
        sql_template="SELECT * FROM {table} WHERE {email} NOT LIKE '%@%.%'",
        example="Email invalide → Notification échoue"
    ),
    
    CoreAnomaly(
        id="DB#4", dimension=Dimension.DB,
        name="Valeurs hors domaine",
        description="Valeur ∉ ensemble autorisé",
        criticality=Criticality.ÉLEVÉ, woodall_level="SAST",
        detector=detect_out_of_domain,
        sql_template="SELECT * FROM {table} WHERE {column} NOT IN ({values})",
        example="Statut hors CDI/CDD/Stage"
    ),
    
    CoreAnomaly(
        id="DB#5", dimension=Dimension.DB,
        name="Valeurs négatives interdites",
        description="< 0 sur champs positifs",
        criticality=Criticality.MOYEN, woodall_level="SAST",
        detector=detect_negative_values,
        sql_template="SELECT * FROM {table} WHERE {column} < 0",
        example="Age négatif → Calcul faussé"
    ),
    
    # DB#6-15 : TEMPLATES (implémentation progressive)
    *[CoreAnomaly(
        id=f"DB#{i}", dimension=Dimension.DB,
        name=f"Anomalie DB#{i}",
        description=f"Anomalie base données #{i} - Template",
        criticality=Criticality.MOYEN, woodall_level="SAMT",
        detector=detect_template_db,
        sql_template="-- Template SQL",
        example=f"Exemple DB#{i}"
    ) for i in range(6, 16)],
    
    # ========================================================================
    # DP : 15 ANOMALIES (3 réelles + 12 templates)
    # ========================================================================
    
    # DP#1-3 : DÉTECTEURS RÉELS
    CoreAnomaly(
        id="DP#1", dimension=Dimension.DP,
        name="Calculs dérivés incorrects",
        description="Formule F(A,...) non respectée",
        criticality=Criticality.ÉLEVÉ, woodall_level="MAST",
        detector=detect_derived_calc_error,
        sql_template="SELECT * WHERE {target} != F({sources})",
        example="Age=35 mais né en 1985"
    ),
    
    CoreAnomaly(
        id="DP#2", dimension=Dimension.DP,
        name="Divisions par zéro",
        description="Dénominateur = 0 ou NULL",
        criticality=Criticality.MOYEN, woodall_level="SAST",
        detector=detect_division_by_zero,
        sql_template="SELECT * WHERE {denominator} = 0",
        example="Calcul ratio avec dénominateur 0"
    ),
    
    CoreAnomaly(
        id="DP#3", dimension=Dimension.DP,
        name="Type données incorrect",
        description="Type réel ≠ type attendu",
        criticality=Criticality.MOYEN, woodall_level="SAST",
        detector=detect_data_type_mismatch,
        sql_template="SELECT * WHERE TYPEOF({column}) != {expected}",
        example="Prix VARCHAR au lieu DECIMAL"
    ),
    
    # DP#4-15 : TEMPLATES
    *[CoreAnomaly(
        id=f"DP#{i}", dimension=Dimension.DP,
        name=f"Anomalie DP#{i}",
        description=f"Anomalie traitement données #{i} - Template",
        criticality=Criticality.MOYEN, woodall_level="MAST",
        detector=detect_template_dp,
        sql_template="-- Template SQL",
        example=f"Exemple DP#{i}"
    ) for i in range(4, 16)],
    
    # ========================================================================
    # BR : 15 ANOMALIES (4 réelles + 11 templates)
    # ========================================================================
    
    # BR#1-4 : DÉTECTEURS RÉELS
    CoreAnomaly(
        id="BR#1", dimension=Dimension.BR,
        name="Incohérences temporelles",
        description="date_début > date_fin",
        criticality=Criticality.ÉLEVÉ, woodall_level="MAST",
        detector=detect_temporal_inconsistency,
        sql_template="SELECT * WHERE {start_date} > {end_date}",
        example="Date sortie < date entrée"
    ),
    
    CoreAnomaly(
        id="BR#2", dimension=Dimension.BR,
        name="Valeurs hors bornes métier",
        description="Hors [min_business, max_business]",
        criticality=Criticality.CRITIQUE, woodall_level="MAST",
        detector=detect_out_of_business_range,
        sql_template="SELECT * WHERE {column} NOT BETWEEN {min} AND {max}",
        example="Age = 150 ans"
    ),
    
    CoreAnomaly(
        id="BR#3", dimension=Dimension.BR,
        name="Combinaisons interdites",
        description="États mutuellement exclusifs",
        criticality=Criticality.ÉLEVÉ, woodall_level="MAST",
        detector=detect_forbidden_combination,
        sql_template="SELECT * WHERE {col1}={val1} AND {col2}={val2}",
        example="Forfait jour ET heures sup"
    ),
    
    CoreAnomaly(
        id="BR#4", dimension=Dimension.BR,
        name="Obligations métier",
        description="SI A ALORS B obligatoire",
        criticality=Criticality.ÉLEVÉ, woodall_level="MAST",
        detector=detect_mandatory_business_rule,
        sql_template="SELECT * WHERE {condition} AND {required} IS NULL",
        example="Ancienneté>0 MAIS prime=0"
    ),
    
    # BR#5-15 : TEMPLATES
    *[CoreAnomaly(
        id=f"BR#{i}", dimension=Dimension.BR,
        name=f"Anomalie BR#{i}",
        description=f"Anomalie règles métier #{i} - Template",
        criticality=Criticality.MOYEN, woodall_level="MAST",
        detector=detect_template_br,
        sql_template="-- Template SQL",
        example=f"Exemple BR#{i}"
    ) for i in range(5, 16)],
    
    # ========================================================================
    # UP : 15 ANOMALIES (3 réelles + 12 templates)
    # ========================================================================
    
    # UP#1-3 : DÉTECTEURS RÉELS
    CoreAnomaly(
        id="UP#1", dimension=Dimension.UP,
        name="Données obsolètes",
        description="Date MAJ trop ancienne",
        criticality=Criticality.ÉLEVÉ, woodall_level="SAMT",
        detector=detect_obsolete_data,
        sql_template="SELECT * WHERE {date_col} < NOW() - INTERVAL {days} DAY",
        example="Prix 2019 en 2025"
    ),
    
    CoreAnomaly(
        id="UP#2", dimension=Dimension.UP,
        name="Granularité excessive",
        description="Trop de valeurs uniques",
        criticality=Criticality.FAIBLE, woodall_level="SAMT",
        detector=detect_excessive_granularity,
        sql_template="SELECT COUNT(DISTINCT {column}) / COUNT(*) FROM {table}",
        example="Données secondes pour reporting annuel"
    ),
    
    CoreAnomaly(
        id="UP#3", dimension=Dimension.UP,
        name="Granularité insuffisante",
        description="Pas assez de détail",
        criticality=Criticality.MOYEN, woodall_level="SAMT",
        detector=lambda df, col, min_unique: {
            'detected': df[col].nunique() < min_unique if col in df.columns else False,
            'affected_rows': len(df) if (col in df.columns and df[col].nunique() < min_unique) else 0,
            'unique_count': df[col].nunique() if col in df.columns else 0,
            'min_expected': min_unique,
            'sample': []
        },
        sql_template="SELECT COUNT(DISTINCT {column}) FROM {table}",
        example="Pays avec 3 valeurs uniquement"
    ),
    
    # UP#4-15 : TEMPLATES
    *[CoreAnomaly(
        id=f"UP#{i}", dimension=Dimension.UP,
        name=f"Anomalie UP#{i}",
        description=f"Anomalie usage #{i} - Template",
        criticality=Criticality.FAIBLE, woodall_level="SAMT",
        detector=detect_template_up,
        sql_template="-- Template SQL",
        example=f"Exemple UP#{i}"
    ) for i in range(4, 16)],
]


# ============================================================================
# MANAGER ÉTENDU
# ============================================================================

class ExtendedCatalogManager:
    """Gestionnaire catalogue étendu 60 anomalies"""
    
    def __init__(self, persistence_file: str = "extended_anomaly_stats.json"):
        self.catalog = EXTENDED_CATALOG
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
    
    print("📊 CATALOGUE ÉTENDU - 60 ANOMALIES")
    print(f"Total: {len(manager.catalog)}")
    print(f"\nPar dimension:")
    for dim in ['DB', 'DP', 'BR', 'UP']:
        count = len(manager.get_by_dimension(dim))
        print(f"  {dim}: {count}")
    
    print(f"\nDétecteurs réels: {len(manager.get_real_detectors())}")
    print(f"Templates: {len(manager.catalog) - len(manager.get_real_detectors())}")
