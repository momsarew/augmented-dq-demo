"""
core_anomaly_catalog.py
Référentiel CORE : 15 anomalies réelles non-chevauchantes

Critères sélection :
- Fréquence haute (détectées souvent)
- Complexité faible (SAST, SAMT, MAST)
- Pas de chevauchement (chacune détecte quelque chose de distinct)
- Impact business élevé
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path


class Dimension(Enum):
    DB = "DB"
    DP = "DP"
    BR = "BR"
    UP = "UP"


class Criticality(Enum):
    CRITIQUE = 4
    ÉLEVÉ = 3
    MOYEN = 2
    FAIBLE = 1


@dataclass
class CoreAnomaly:
    """Anomalie core avec détecteur réel"""
    id: str
    dimension: Dimension
    name: str
    description: str
    criticality: Criticality
    woodall_level: str
    detector: Callable
    sql_template: str
    example: str
    
    # Métadonnées apprentissage
    detection_count: int = 0
    scan_count: int = 0
    frequency: float = 0.0
    
    def update_stats(self, detected: bool):
        """Met à jour stats après scan"""
        self.scan_count += 1
        if detected:
            self.detection_count += 1
        self.frequency = self.detection_count / self.scan_count if self.scan_count > 0 else 0.0
    
    def get_priority_score(self) -> float:
        """Score priorité adaptatif"""
        impact = self.criticality.value * 25  # CRITIQUE=100, ÉLEVÉ=75, etc.
        freq_boost = self.frequency * 100 if self.scan_count >= 3 else impact
        return freq_boost * (impact / 100)


# ============================================================================
# DÉTECTEURS RÉELS - 15 ANOMALIES NON-CHEVAUCHANTES
# ============================================================================

def detect_null_in_required(df: pd.DataFrame, columns: List[str]) -> Dict:
    """
    DB#1: NULL dans colonnes obligatoires
    Chevauchement: AUCUN (détecte absence de valeur)
    """
    results = {}
    total_nulls = 0
    samples = []
    
    for col in columns:
        if col in df.columns:
            nulls = df[df[col].isnull()]
            if len(nulls) > 0:
                total_nulls += len(nulls)
                samples.extend(nulls.head(2).to_dict('records'))
    
    return {
        'detected': total_nulls > 0,
        'affected_rows': total_nulls,
        'columns_with_nulls': [c for c in columns if c in df.columns and df[c].isnull().any()],
        'sample': samples[:5]
    }


def detect_pk_duplicates(df: pd.DataFrame, pk_column: str) -> Dict:
    """
    DB#2: Doublons sur clé primaire
    Chevauchement: AUCUN (détecte lignes identiques sur PK)
    """
    if pk_column not in df.columns:
        return {'detected': False, 'reason': 'column_not_found'}
    
    duplicates = df[df.duplicated(subset=[pk_column], keep=False)]
    
    return {
        'detected': len(duplicates) > 0,
        'affected_rows': len(duplicates),
        'duplicate_values': duplicates[pk_column].value_counts().head(5).to_dict(),
        'sample': duplicates.head(5).to_dict('records')
    }


def detect_invalid_email(df: pd.DataFrame, email_columns: List[str]) -> Dict:
    """
    DB#3: Formats email invalides
    Chevauchement: AUCUN (détecte format incorrect)
    """
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    total_invalid = 0
    samples = []
    invalid_cols = []
    
    for col in email_columns:
        if col in df.columns:
            invalid = df[~df[col].astype(str).str.match(email_pattern, na=False) & df[col].notnull()]
            if len(invalid) > 0:
                total_invalid += len(invalid)
                invalid_cols.append(col)
                samples.extend(invalid.head(2).to_dict('records'))
    
    return {
        'detected': total_invalid > 0,
        'affected_rows': total_invalid,
        'columns_with_invalid': invalid_cols,
        'sample': samples[:5]
    }


def detect_out_of_domain(df: pd.DataFrame, column: str, valid_values: List) -> Dict:
    """
    DB#4: Valeurs hors domaine autorisé
    Chevauchement: AUCUN (détecte valeurs non dans liste)
    """
    if column not in df.columns:
        return {'detected': False, 'reason': 'column_not_found'}
    
    invalid = df[~df[column].isin(valid_values) & df[column].notnull()]
    
    return {
        'detected': len(invalid) > 0,
        'affected_rows': len(invalid),
        'invalid_values': invalid[column].unique().tolist()[:10],
        'sample': invalid.head(5).to_dict('records')
    }


def detect_negative_values(df: pd.DataFrame, columns: List[str]) -> Dict:
    """
    DB#5: Valeurs négatives sur champs positifs
    Chevauchement: AUCUN (détecte < 0)
    """
    total_negative = 0
    samples = []
    negative_cols = []
    
    for col in columns:
        if col in df.columns:
            try:
                values = pd.to_numeric(df[col], errors='coerce')
                negative = df[values < 0]
                if len(negative) > 0:
                    total_negative += len(negative)
                    negative_cols.append(col)
                    samples.extend(negative.head(2).to_dict('records'))
            except:
                continue
    
    return {
        'detected': total_negative > 0,
        'affected_rows': total_negative,
        'columns_with_negative': negative_cols,
        'sample': samples[:5]
    }


def detect_derived_calc_error(df: pd.DataFrame, source_cols: List[str], target_col: str, formula: str) -> Dict:
    """
    DP#1: Calculs dérivés incorrects
    Chevauchement: AUCUN (détecte formule non respectée)
    """
    if not all(c in df.columns for c in source_cols + [target_col]):
        return {'detected': False, 'reason': 'columns_not_found'}
    
    try:
        # Exemples formules courantes
        if formula == "age_from_birthdate":
            expected = (pd.Timestamp.now() - pd.to_datetime(df[source_cols[0]])).dt.days / 365.25
            actual = pd.to_numeric(df[target_col], errors='coerce')
            errors = df[abs(expected - actual) > 1]  # Tolérance 1 an
        
        elif formula == "montant_ttc":
            # montant_ttc = montant_ht * (1 + taux_tva)
            expected = pd.to_numeric(df[source_cols[0]], errors='coerce') * (1 + pd.to_numeric(df[source_cols[1]], errors='coerce'))
            actual = pd.to_numeric(df[target_col], errors='coerce')
            errors = df[~np.isclose(expected, actual, rtol=0.01, atol=0.01, equal_nan=True)]
        
        else:
            return {'detected': False, 'reason': 'formula_not_supported'}
        
        return {
            'detected': len(errors) > 0,
            'affected_rows': len(errors),
            'formula': formula,
            'sample': errors.head(5).to_dict('records')
        }
    except:
        return {'detected': False, 'reason': 'calculation_error'}


def detect_division_by_zero(df: pd.DataFrame, denominator_cols: List[str]) -> Dict:
    """
    DP#2: Divisions par zéro potentielles
    Chevauchement: AUCUN (détecte dénominateur = 0)
    """
    total_zeros = 0
    samples = []
    zero_cols = []
    
    for col in denominator_cols:
        if col in df.columns:
            try:
                values = pd.to_numeric(df[col], errors='coerce')
                zeros = df[(values == 0) | values.isnull()]
                if len(zeros) > 0:
                    total_zeros += len(zeros)
                    zero_cols.append(col)
                    samples.extend(zeros.head(2).to_dict('records'))
            except:
                continue
    
    return {
        'detected': total_zeros > 0,
        'affected_rows': total_zeros,
        'columns_with_zero': zero_cols,
        'sample': samples[:5]
    }


def detect_data_type_mismatch(df: pd.DataFrame, column: str, expected_type: str) -> Dict:
    """
    DP#3: Type données incorrect
    Chevauchement: AUCUN (détecte type wrong)
    """
    if column not in df.columns:
        return {'detected': False, 'reason': 'column_not_found'}
    
    try:
        if expected_type == 'numeric':
            invalid = df[pd.to_numeric(df[column], errors='coerce').isnull() & df[column].notnull()]
        elif expected_type == 'date':
            invalid = df[pd.to_datetime(df[column], errors='coerce').isnull() & df[column].notnull()]
        else:
            return {'detected': False, 'reason': 'type_not_supported'}
        
        return {
            'detected': len(invalid) > 0,
            'affected_rows': len(invalid),
            'expected_type': expected_type,
            'sample': invalid.head(5).to_dict('records')
        }
    except:
        return {'detected': False, 'reason': 'type_check_error'}


def detect_temporal_inconsistency(df: pd.DataFrame, start_col: str, end_col: str) -> Dict:
    """
    BR#1: Incohérences temporelles (date_début > date_fin)
    Chevauchement: AUCUN (détecte ordre dates incorrect)
    """
    if start_col not in df.columns or end_col not in df.columns:
        return {'detected': False, 'reason': 'columns_not_found'}
    
    try:
        start_dates = pd.to_datetime(df[start_col], errors='coerce')
        end_dates = pd.to_datetime(df[end_col], errors='coerce')
        
        inconsistent = df[(start_dates > end_dates) & start_dates.notnull() & end_dates.notnull()]
        
        return {
            'detected': len(inconsistent) > 0,
            'affected_rows': len(inconsistent),
            'sample': inconsistent.head(5).to_dict('records')
        }
    except:
        return {'detected': False, 'reason': 'date_parsing_error'}


def detect_out_of_business_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> Dict:
    """
    BR#2: Valeurs hors bornes métier
    Chevauchement: AUCUN (détecte hors [min, max] business)
    """
    if column not in df.columns:
        return {'detected': False, 'reason': 'column_not_found'}
    
    try:
        values = pd.to_numeric(df[column], errors='coerce')
        out_of_range = df[(values < min_val) | (values > max_val)]
        
        return {
            'detected': len(out_of_range) > 0,
            'affected_rows': len(out_of_range),
            'business_range': [min_val, max_val],
            'actual_min': float(values.min()),
            'actual_max': float(values.max()),
            'sample': out_of_range.head(5).to_dict('records')
        }
    except:
        return {'detected': False, 'reason': 'range_check_error'}


def detect_forbidden_combination(df: pd.DataFrame, col1: str, val1, col2: str, val2) -> Dict:
    """
    BR#3: Combinaisons interdites
    Chevauchement: AUCUN (détecte état mutuellement exclusif)
    """
    if col1 not in df.columns or col2 not in df.columns:
        return {'detected': False, 'reason': 'columns_not_found'}
    
    forbidden = df[(df[col1] == val1) & (df[col2] == val2)]
    
    return {
        'detected': len(forbidden) > 0,
        'affected_rows': len(forbidden),
        'rule': f"{col1}={val1} AND {col2}={val2} is forbidden",
        'sample': forbidden.head(5).to_dict('records')
    }


def detect_mandatory_business_rule(df: pd.DataFrame, condition_col: str, condition_val, required_col: str) -> Dict:
    """
    BR#4: Obligations métier (SI A ALORS B obligatoire)
    Chevauchement: AUCUN (détecte règle conditionnelle violée)
    """
    if condition_col not in df.columns or required_col not in df.columns:
        return {'detected': False, 'reason': 'columns_not_found'}
    
    violations = df[(df[condition_col] == condition_val) & df[required_col].isnull()]
    
    return {
        'detected': len(violations) > 0,
        'affected_rows': len(violations),
        'rule': f"IF {condition_col}={condition_val} THEN {required_col} must be NOT NULL",
        'sample': violations.head(5).to_dict('records')
    }


def detect_obsolete_data(df: pd.DataFrame, date_col: str, max_age_days: int) -> Dict:
    """
    UP#1: Données obsolètes
    Chevauchement: AUCUN (détecte ancienneté excessive)
    """
    if date_col not in df.columns:
        return {'detected': False, 'reason': 'column_not_found'}
    
    try:
        dates = pd.to_datetime(df[date_col], errors='coerce')
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=max_age_days)
        obsolete = df[dates < cutoff]
        
        return {
            'detected': len(obsolete) > 0,
            'affected_rows': len(obsolete),
            'max_age_days': max_age_days,
            'oldest_date': dates.min().isoformat() if len(obsolete) > 0 else None,
            'sample': obsolete.head(5).to_dict('records')
        }
    except:
        return {'detected': False, 'reason': 'date_check_error'}


def detect_excessive_granularity(df: pd.DataFrame, column: str, max_unique_ratio: float) -> Dict:
    """
    UP#2: Granularité excessive
    Chevauchement: AUCUN (détecte trop de valeurs uniques)
    """
    if column not in df.columns:
        return {'detected': False, 'reason': 'column_not_found'}
    
    unique_count = df[column].nunique()
    total_count = len(df)
    ratio = unique_count / total_count
    
    return {
        'detected': ratio > max_unique_ratio,
        'unique_count': unique_count,
        'total_count': total_count,
        'ratio': float(ratio),
        'threshold': max_unique_ratio
    }


# ============================================================================
# CATALOGUE CORE - 15 ANOMALIES
# ============================================================================

CORE_CATALOG = [
    # ──────────── DB (5) ────────────
    CoreAnomaly(
        id="DB#1",
        dimension=Dimension.DB,
        name="NULL dans colonnes obligatoires",
        description="Attributs (1,1) contenant NULL",
        criticality=Criticality.CRITIQUE,
        woodall_level="SAST",
        detector=detect_null_in_required,
        sql_template="SELECT * FROM {table} WHERE {column} IS NULL",
        example="employee_id NULL → Paie bloquée, 15 employés, 45k€/mois"
    ),
    
    CoreAnomaly(
        id="DB#2",
        dimension=Dimension.DB,
        name="Doublons clé primaire",
        description="Violations contrainte PK",
        criticality=Criticality.CRITIQUE,
        woodall_level="SAMT",
        detector=detect_pk_duplicates,
        sql_template="SELECT {pk}, COUNT(*) FROM {table} GROUP BY {pk} HAVING COUNT(*)>1",
        example="Matricule='12345' en double → Masse salariale ×2"
    ),
    
    CoreAnomaly(
        id="DB#3",
        dimension=Dimension.DB,
        name="Formats email invalides",
        description="Email sans @ ou domaine invalide",
        criticality=Criticality.MOYEN,
        woodall_level="SAST",
        detector=detect_invalid_email,
        sql_template="SELECT * FROM {table} WHERE {email} NOT LIKE '%@%.%'",
        example="Email invalide → Notification échoue"
    ),
    
    CoreAnomaly(
        id="DB#4",
        dimension=Dimension.DB,
        name="Valeurs hors domaine",
        description="Valeur ∉ ensemble autorisé",
        criticality=Criticality.ÉLEVÉ,
        woodall_level="SAST",
        detector=detect_out_of_domain,
        sql_template="SELECT * FROM {table} WHERE {column} NOT IN ({values})",
        example="Statut='Actif' au lieu CDI/CDD/Stage"
    ),
    
    CoreAnomaly(
        id="DB#5",
        dimension=Dimension.DB,
        name="Valeurs négatives interdites",
        description="< 0 sur champs positifs",
        criticality=Criticality.MOYEN,
        woodall_level="SAST",
        detector=detect_negative_values,
        sql_template="SELECT * FROM {table} WHERE {column} < 0",
        example="Age=-5 → Calcul primes faussé"
    ),
    
    # ──────────── DP (3) ────────────
    CoreAnomaly(
        id="DP#1",
        dimension=Dimension.DP,
        name="Calculs dérivés incorrects",
        description="Formule F(A,...) non respectée",
        criticality=Criticality.ÉLEVÉ,
        woodall_level="MAST",
        detector=detect_derived_calc_error,
        sql_template="SELECT * WHERE {target} != F({sources})",
        example="Age=35 mais né en 1985 → Écart 4 ans"
    ),
    
    CoreAnomaly(
        id="DP#2",
        dimension=Dimension.DP,
        name="Divisions par zéro",
        description="Dénominateur = 0 ou NULL",
        criticality=Criticality.MOYEN,
        woodall_level="SAST",
        detector=detect_division_by_zero,
        sql_template="SELECT * WHERE {denominator} = 0 OR {denominator} IS NULL",
        example="Marge=(prix-cout)/cout avec cout=0"
    ),
    
    CoreAnomaly(
        id="DP#3",
        dimension=Dimension.DP,
        name="Type données incorrect",
        description="Type réel ≠ type attendu",
        criticality=Criticality.MOYEN,
        woodall_level="SAST",
        detector=detect_data_type_mismatch,
        sql_template="SELECT * WHERE TYPEOF({column}) != {expected}",
        example="Prix stocké VARCHAR au lieu DECIMAL"
    ),
    
    # ──────────── BR (4) ────────────
    CoreAnomaly(
        id="BR#1",
        dimension=Dimension.BR,
        name="Incohérences temporelles",
        description="date_début > date_fin",
        criticality=Criticality.ÉLEVÉ,
        woodall_level="MAST",
        detector=detect_temporal_inconsistency,
        sql_template="SELECT * WHERE {start_date} > {end_date}",
        example="Date_sortie < date_entrée → Ancienneté négative"
    ),
    
    CoreAnomaly(
        id="BR#2",
        dimension=Dimension.BR,
        name="Valeurs hors bornes métier",
        description="Hors [min_business, max_business]",
        criticality=Criticality.CRITIQUE,
        woodall_level="MAST",
        detector=detect_out_of_business_range,
        sql_template="SELECT * WHERE {column} NOT BETWEEN {min} AND {max}",
        example="Age=150 ans → Donnée aberrante"
    ),
    
    CoreAnomaly(
        id="BR#3",
        dimension=Dimension.BR,
        name="Combinaisons interdites",
        description="États mutuellement exclusifs",
        criticality=Criticality.ÉLEVÉ,
        woodall_level="MAST",
        detector=detect_forbidden_combination,
        sql_template="SELECT * WHERE {col1}={val1} AND {col2}={val2}",
        example="Forfait_jour=OUI ET heures_sup≠NULL"
    ),
    
    CoreAnomaly(
        id="BR#4",
        dimension=Dimension.BR,
        name="Obligations métier",
        description="SI A ALORS B obligatoire",
        criticality=Criticality.ÉLEVÉ,
        woodall_level="MAST",
        detector=detect_mandatory_business_rule,
        sql_template="SELECT * WHERE {condition} AND {required} IS NULL",
        example="Ancienneté>0 MAIS prime_ancienneté=0"
    ),
    
    # ──────────── UP (3) ────────────
    CoreAnomaly(
        id="UP#1",
        dimension=Dimension.UP,
        name="Données obsolètes",
        description="Date MAJ trop ancienne",
        criticality=Criticality.ÉLEVÉ,
        woodall_level="SAMT",
        detector=detect_obsolete_data,
        sql_template="SELECT * WHERE {date_col} < NOW() - INTERVAL {days} DAY",
        example="Prix catalogue 2019 en 2025"
    ),
    
    CoreAnomaly(
        id="UP#2",
        dimension=Dimension.UP,
        name="Granularité excessive",
        description="Trop de valeurs uniques",
        criticality=Criticality.FAIBLE,
        woodall_level="SAMT",
        detector=detect_excessive_granularity,
        sql_template="SELECT COUNT(DISTINCT {column}) / COUNT(*) FROM {table}",
        example="Reporting annuel avec données secondes"
    ),
    
    CoreAnomaly(
        id="UP#3",
        dimension=Dimension.UP,
        name="Granularité insuffisante",
        description="Pas assez de détail",
        criticality=Criticality.MOYEN,
        woodall_level="SAMT",
        detector=lambda df, col, min_unique: {
            'detected': df[col].nunique() < min_unique if col in df.columns else False,
            'unique_count': df[col].nunique() if col in df.columns else 0,
            'min_expected': min_unique
        },
        sql_template="SELECT COUNT(DISTINCT {column}) FROM {table}",
        example="Analyse pays avec 3 valeurs uniquement"
    ),
]


class CoreCatalogManager:
    """Gestionnaire catalogue core avec apprentissage"""
    
    def __init__(self, persistence_file: str = "core_anomaly_stats.json"):
        self.catalog = CORE_CATALOG
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
    
    def update_stats(self, anomaly_id: str, detected: bool):
        """Met à jour stats après scan"""
        anomaly = self.get_by_id(anomaly_id)
        if anomaly:
            anomaly.update_stats(detected)
            self._save_stats()
    
    def add_anomaly(self, anomaly: CoreAnomaly):
        """Ajoute nouvelle anomalie"""
        self.catalog.append(anomaly)
        self._save_stats()
    
    def get_stats_df(self) -> pd.DataFrame:
        """Stats en DataFrame"""
        data = []
        for a in self.catalog:
            score = a.get_priority_score()
            data.append({
                'ID': a.id,
                'Nom': a.name,
                'Dimension': a.dimension.value,
                'Criticité': a.criticality.name,
                'Woodall': a.woodall_level,
                'Détections': a.detection_count,
                'Scans': a.scan_count,
                'Fréquence': f"{a.frequency:.1%}" if a.scan_count > 0 else "N/A",
                'Score Priorité': f"{score:.1f}",
                '_score_numeric': score  # Colonne cachée pour tri/calculs
            })
        
        df = pd.DataFrame(data)
        return df.sort_values('_score_numeric', ascending=False)


if __name__ == "__main__":
    manager = CoreCatalogManager()
    
    print("📊 CATALOGUE CORE - 15 ANOMALIES")
    print(f"Total: {len(manager.catalog)}")
    print(f"\nPar dimension:")
    for dim in ['DB', 'DP', 'BR', 'UP']:
        count = len(manager.get_by_dimension(dim))
        print(f"  {dim}: {count}")
    
    print("\n📋 LISTE COMPLÈTE:")
    stats_df = manager.get_stats_df()
    print(stats_df.to_string(index=False))
