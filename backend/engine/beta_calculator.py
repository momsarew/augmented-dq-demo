"""
Module de calcul des distributions Beta bayésiennes
Convertit taux d'erreur observés en Beta(α, β) avec incertitude quantifiée

LOGIQUE DE CALCUL DES PROBABILITÉS P_DB, P_DP, P_BR, P_UP:
=========================================================
1. Charger le catalogue d'anomalies (core_anomaly_catalog / extended_anomaly_catalog)
2. Filtrer selon le niveau de profiling:
   - Quick: Criticité non faible + Woodall SAST/SAMT
   - Standard: Criticité non faible + Woodall SAST/SAMT/MAST
   - Advanced: Toutes criticités + Tous niveaux Woodall
3. Trier par score de priorité (basé sur l'apprentissage - fréquence de détection)
4. Scanner les anomalies dans l'ordre de priorité
5. Calculer P_dimension = anomalies_détectées / total_lignes_vérifiées
"""

import numpy as np
from scipy.stats import beta as beta_dist
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import sys
from pathlib import Path

# Ajouter le chemin pour importer les catalogues
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from extended_anomaly_catalog import ExtendedCatalogManager, Dimension, Criticality
except ImportError:
    from backend.extended_anomaly_catalog import ExtendedCatalogManager, Dimension, Criticality


class ProfilingLevel:
    """Niveaux de profiling disponibles"""
    QUICK = "quick"      # Rapide: SAST+SAMT, criticité non faible
    STANDARD = "standard"  # Standard: SAST+SAMT+MAST, criticité non faible
    ADVANCED = "advanced"  # Avancé: Toutes anomalies


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
            P_DB: Taux erreur Database (depuis scan anomalies DB)
            P_DP: Taux erreur Data Processing (depuis scan anomalies DP)
            P_BR: Taux erreur Business Rules (depuis scan anomalies BR)
            P_UP: Taux erreur Usage-fit (depuis scan anomalies UP)
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


class AnomalyBasedCalculator:
    """
    Calculateur de probabilités basé sur le catalogue d'anomalies
    avec système d'apprentissage adaptatif
    """

    def __init__(self, persistence_file: str = None):
        """
        Initialise le calculateur avec le catalogue d'anomalies

        Args:
            persistence_file: Chemin vers le fichier de stats d'apprentissage
        """
        if persistence_file:
            self.catalog_manager = ExtendedCatalogManager(persistence_file)
        else:
            self.catalog_manager = ExtendedCatalogManager()

        self.beta_calculator = BetaCalculator()

    def filter_anomalies_by_profiling_level(self,
                                            profiling_level: str,
                                            dimension: str = None) -> List:
        """
        Filtre les anomalies selon le niveau de profiling

        LOGIQUE DE FILTRAGE:
        - Quick: Criticité non FAIBLE + Woodall SAST ou SAMT
        - Standard: Criticité non FAIBLE + Woodall SAST, SAMT ou MAST
        - Advanced: Toutes les anomalies (pas de filtre)

        Args:
            profiling_level: 'quick', 'standard', 'advanced'
            dimension: Optionnel, filtrer par dimension ('DB', 'DP', 'BR', 'UP')

        Returns:
            Liste d'anomalies filtrées et triées par score de priorité
        """
        all_anomalies = self.catalog_manager.catalog

        # Filtrer par dimension si spécifié
        if dimension:
            all_anomalies = [a for a in all_anomalies if a.dimension.value == dimension]

        # Filtrer selon niveau de profiling
        if profiling_level == ProfilingLevel.QUICK:
            # Quick: Criticité non FAIBLE + SAST/SAMT uniquement
            filtered = [
                a for a in all_anomalies
                if a.criticality != Criticality.FAIBLE
                and a.woodall_level in ['SAST', 'SAMT']
            ]

        elif profiling_level == ProfilingLevel.STANDARD:
            # Standard: Criticité non FAIBLE + SAST/SAMT/MAST
            filtered = [
                a for a in all_anomalies
                if a.criticality != Criticality.FAIBLE
                and a.woodall_level in ['SAST', 'SAMT', 'MAST']
            ]

        else:  # ADVANCED
            # Advanced: Toutes les anomalies
            filtered = all_anomalies

        # Trier par score de priorité (apprentissage) - décroissant
        # Les anomalies les plus fréquemment détectées sont scannées en premier
        sorted_anomalies = sorted(
            filtered,
            key=lambda a: a.get_priority_score(),
            reverse=True
        )

        return sorted_anomalies

    def scan_dimension(self,
                      df: pd.DataFrame,
                      dimension: str,
                      profiling_level: str = ProfilingLevel.STANDARD,
                      column_config: Dict = None) -> Dict[str, Any]:
        """
        Scanne les anomalies d'une dimension sur le DataFrame

        ALGORITHME:
        1. Filtrer anomalies par niveau de profiling
        2. Trier par score de priorité (apprentissage)
        3. Scanner chaque anomalie dans l'ordre
        4. Mettre à jour les stats d'apprentissage
        5. Calculer P_dimension = lignes_affectées / total_lignes

        Args:
            df: DataFrame à analyser
            dimension: 'DB', 'DP', 'BR', 'UP'
            profiling_level: Niveau de profiling
            column_config: Configuration des colonnes pour les détecteurs

        Returns:
            {
                'P_dimension': 0.15,
                'anomalies_detected': [...],
                'total_affected_rows': 150,
                'total_rows': 1000,
                'scan_details': [...]
            }
        """
        # Filtrer et trier les anomalies
        anomalies = self.filter_anomalies_by_profiling_level(profiling_level, dimension)

        total_rows = len(df)
        affected_rows_set = set()  # Pour éviter de compter 2 fois la même ligne
        anomalies_detected = []
        scan_details = []

        # Configuration par défaut si non fournie
        if column_config is None:
            column_config = self._auto_detect_column_config(df)

        # Scanner chaque anomalie dans l'ordre de priorité
        for anomaly in anomalies:
            try:
                # Préparer les paramètres selon l'anomalie
                params = self._get_detector_params(anomaly, df, column_config)

                if params is None:
                    continue

                # Exécuter le détecteur
                result = anomaly.detector(df, **params)

                # Enregistrer le résultat
                detected = result.get('detected', False)
                affected = result.get('affected_rows', 0)

                scan_details.append({
                    'anomaly_id': anomaly.id,
                    'anomaly_name': anomaly.name,
                    'detected': detected,
                    'affected_rows': affected,
                    'woodall_level': anomaly.woodall_level,
                    'criticality': anomaly.criticality.name,
                    'priority_score': anomaly.get_priority_score()
                })

                # Mettre à jour l'apprentissage
                self.catalog_manager.update_stats(anomaly.id, detected)

                if detected:
                    anomalies_detected.append({
                        'id': anomaly.id,
                        'name': anomaly.name,
                        'affected_rows': affected,
                        'sample': result.get('sample', [])[:3]
                    })
                    # Ajouter les lignes affectées (approximation)
                    # En réalité il faudrait les indices exacts
                    for i in range(min(affected, total_rows)):
                        affected_rows_set.add(i)

            except Exception as e:
                scan_details.append({
                    'anomaly_id': anomaly.id,
                    'anomaly_name': anomaly.name,
                    'error': str(e)
                })

        # Calculer P_dimension
        total_affected = len(affected_rows_set)
        P_dimension = total_affected / total_rows if total_rows > 0 else 0.0

        return {
            'P_dimension': round(P_dimension, 4),
            'dimension': dimension,
            'profiling_level': profiling_level,
            'anomalies_scanned': len(anomalies),
            'anomalies_detected': anomalies_detected,
            'total_affected_rows': total_affected,
            'total_rows': total_rows,
            'scan_details': scan_details
        }

    def _auto_detect_column_config(self, df: pd.DataFrame) -> Dict:
        """
        Détecte automatiquement la configuration des colonnes
        basée sur les noms et types
        """
        config = {
            'pk_columns': [],
            'email_columns': [],
            'date_columns': [],
            'numeric_positive_columns': [],
            'all_columns': list(df.columns)
        }

        for col in df.columns:
            col_lower = col.lower()

            # Clés primaires potentielles
            if any(kw in col_lower for kw in ['id', 'matricule', 'code', 'key', 'pk']):
                config['pk_columns'].append(col)

            # Colonnes email
            if any(kw in col_lower for kw in ['email', 'mail', 'courriel']):
                config['email_columns'].append(col)

            # Colonnes date
            if any(kw in col_lower for kw in ['date', 'datetime', 'time', 'jour', 'mois']):
                config['date_columns'].append(col)

            # Colonnes numériques positives
            if any(kw in col_lower for kw in ['age', 'anciennete', 'salaire', 'montant', 'prix', 'quantite']):
                config['numeric_positive_columns'].append(col)

        return config

    def _get_detector_params(self, anomaly, df: pd.DataFrame, column_config: Dict) -> Optional[Dict]:
        """
        Prépare les paramètres pour un détecteur d'anomalie
        """
        anomaly_id = anomaly.id

        # DB#1: NULL dans colonnes obligatoires
        if anomaly_id == "DB#1":
            return {'columns': column_config.get('all_columns', list(df.columns))}

        # DB#2: Doublons clé primaire
        elif anomaly_id == "DB#2":
            pk_cols = column_config.get('pk_columns', [])
            if pk_cols:
                return {'pk_column': pk_cols[0]}
            return None

        # DB#3: Email invalide
        elif anomaly_id == "DB#3":
            email_cols = column_config.get('email_columns', [])
            if email_cols:
                return {'email_columns': email_cols}
            return None

        # DB#4: Valeurs hors domaine - nécessite config spécifique
        elif anomaly_id == "DB#4":
            return None  # Nécessite configuration manuelle

        # DB#5: Valeurs négatives
        elif anomaly_id == "DB#5":
            numeric_cols = column_config.get('numeric_positive_columns', [])
            if numeric_cols:
                return {'columns': numeric_cols}
            return None

        # DP#2: Division par zéro
        elif anomaly_id == "DP#2":
            return {'denominator_cols': column_config.get('numeric_positive_columns', [])}

        # DP#3: Type incorrect
        elif anomaly_id == "DP#3":
            numeric_cols = column_config.get('numeric_positive_columns', [])
            if numeric_cols:
                return {'column': numeric_cols[0], 'expected_type': 'numeric'}
            return None

        # BR#1: Incohérences temporelles
        elif anomaly_id == "BR#1":
            date_cols = column_config.get('date_columns', [])
            if len(date_cols) >= 2:
                return {'start_col': date_cols[0], 'end_col': date_cols[1]}
            return None

        # BR#2: Hors bornes métier
        elif anomaly_id == "BR#2":
            numeric_cols = column_config.get('numeric_positive_columns', [])
            if numeric_cols:
                # Bornes par défaut raisonnables
                return {'column': numeric_cols[0], 'min_val': 0, 'max_val': 100}
            return None

        # UP#1: Données obsolètes
        elif anomaly_id == "UP#1":
            date_cols = column_config.get('date_columns', [])
            if date_cols:
                return {'date_col': date_cols[0], 'max_age_days': 365}
            return None

        # UP#2: Granularité excessive
        elif anomaly_id == "UP#2":
            if column_config.get('all_columns'):
                return {'column': column_config['all_columns'][0], 'max_unique_ratio': 0.9}
            return None

        # Pour les templates et autres, retourner None
        return None

    def compute_4d_vector_from_catalog(self,
                                       df: pd.DataFrame,
                                       profiling_level: str = ProfilingLevel.STANDARD,
                                       column_config: Dict = None) -> Dict[str, Any]:
        """
        Calcule le vecteur 4D complet en scannant le catalogue d'anomalies

        PROCESSUS COMPLET:
        1. Pour chaque dimension (DB, DP, BR, UP):
           a. Filtrer anomalies selon niveau de profiling
           b. Trier par score de priorité (apprentissage)
           c. Scanner les données
           d. Calculer P_dimension
        2. Convertir en distributions Beta
        3. Retourner vecteur 4D avec détails

        Args:
            df: DataFrame à analyser
            profiling_level: 'quick', 'standard', 'advanced'
            column_config: Configuration des colonnes

        Returns:
            Vecteur 4D complet avec métadonnées de scan
        """
        results = {
            'profiling_level': profiling_level,
            'total_rows': len(df),
            'dimensions': {}
        }

        # Scanner chaque dimension
        for dim in ['DB', 'DP', 'BR', 'UP']:
            scan_result = self.scan_dimension(
                df, dim, profiling_level, column_config
            )
            results['dimensions'][dim] = scan_result

        # Extraire les probabilités
        P_DB = results['dimensions']['DB']['P_dimension']
        P_DP = results['dimensions']['DP']['P_dimension']
        P_BR = results['dimensions']['BR']['P_dimension']
        P_UP = results['dimensions']['UP']['P_dimension']

        # Calculer le vecteur Beta 4D
        vector = self.beta_calculator.compute_4d_vector(
            P_DB=P_DB,
            P_DP=P_DP,
            P_BR=P_BR,
            P_UP=P_UP,
            confidence_DB='HIGH' if P_DB > 0.1 else 'MEDIUM',
            confidence_DP='HIGH' if P_DP > 0.1 else 'MEDIUM',
            confidence_BR='HIGH' if P_BR > 0.1 else 'MEDIUM',
            confidence_UP='MEDIUM'
        )

        results['vector_4d'] = vector
        results['summary'] = {
            'P_DB': P_DB,
            'P_DP': P_DP,
            'P_BR': P_BR,
            'P_UP': P_UP,
            'anomalies_scanned_total': sum(
                d['anomalies_scanned'] for d in results['dimensions'].values()
            ),
            'anomalies_detected_total': sum(
                len(d['anomalies_detected']) for d in results['dimensions'].values()
            )
        }

        return results


def compute_all_beta_vectors(df: pd.DataFrame,
                             columns: List[str],
                             stats: Dict[str, Any],
                             profiling_level: str = ProfilingLevel.STANDARD) -> Dict[str, Dict]:
    """
    Calcule vecteurs 4D pour tous attributs - ANALYSE PAR COLONNE

    LOGIQUE:
    Pour chaque colonne, calcule les probabilités d'anomalie selon :
    - P_DB: Problèmes de structure (types, nulls, formats)
    - P_DP: Problèmes de traitement (parsing, conversion)
    - P_BR: Violations règles métier (valeurs hors domaine)
    - P_UP: Problèmes d'utilisabilité (nulls, outliers)

    Args:
        df: DataFrame pandas
        columns: Liste colonnes à analyser
        stats: Stats exploratoires (depuis analyzer.py)
        profiling_level: 'quick', 'standard', 'advanced'

    Returns:
        {
            "Colonne1": {"P_DB": 0.05, "P_DP": 0.02, "P_BR": 0.10, "P_UP": 0.15, ...},
            ...
        }
    """
    # Utiliser la méthode de fallback qui calcule PAR COLONNE
    # C'est plus précis que le scan global du catalogue
    return _compute_vectors_fallback(df, columns, stats)


def _compute_vectors_fallback(df: pd.DataFrame,
                              columns: List[str],
                              stats: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Calcul des vecteurs 4D par colonne basé sur l'analyse des données réelles

    LOGIQUE AMÉLIORÉE:
    - P_DB: Problèmes de structure (types incorrects, formats mixtes)
    - P_DP: Problèmes de traitement (erreurs parsing, conversions)
    - P_BR: Violations règles métier (valeurs hors domaine, incohérences)
    - P_UP: Problèmes d'utilisabilité (nulls, outliers, doublons)
    """
    calculator = BetaCalculator()
    vectors = {}

    for col in columns:
        if col not in stats:
            continue

        col_stats = stats[col]
        series = df[col]
        total = len(series)

        # ====================================================================
        # [DB] Database Structure - Problèmes de structure/types
        # ====================================================================
        P_DB = 0.0

        # 1. Type errors explicitement détectés
        P_DB += col_stats.get('type_errors', {}).get('error_rate', 0)

        # 2. Types mixtes dans une colonne object
        if col_stats['dtype'] == 'object':
            # Vérifier si on a des types mixtes (strings + numbers)
            non_null = series.dropna()
            if len(non_null) > 0:
                # Tenter conversion numérique
                numeric_converted = pd.to_numeric(non_null, errors='coerce')
                numeric_rate = numeric_converted.notna().sum() / len(non_null)
                # Si conversion partielle, c'est un problème de type
                if 0 < numeric_rate < 1:
                    P_DB = max(P_DB, 1 - numeric_rate)  # % qui ne sont pas numériques

        # 3. Cas spécial: colonnes censées être numériques mais stockées en VARCHAR
        if col_stats['dtype'] == 'object':
            # Vérifier si contient des virgules (format numérique européen)
            comma_count = series.astype(str).str.contains(r'^\d+,\d+$', regex=True, na=False).sum()
            if comma_count > 0:
                P_DB = max(P_DB, comma_count / total)

        # 4. Formats de dates mixtes = problème de structure
        date_formats_mixed = False
        if 'date' in col.lower() or col_stats['dtype'] == 'datetime64[ns]':
            non_null = series.dropna().astype(str)
            if len(non_null) > 0:
                formats = set()
                # Utiliser échantillon aléatoire pour détecter tous les formats
                # (pas head() qui pourrait rater des formats en fin de dataset)
                sample_size = min(200, len(non_null))
                sample = non_null.sample(n=sample_size, random_state=42) if len(non_null) > sample_size else non_null
                for val in sample:
                    if '/' in val:
                        formats.add('slash')
                    if '-' in val and not val.startswith('-'):  # Exclure nombres négatifs
                        formats.add('dash')
                if len(formats) > 1:
                    date_formats_mixed = True
                    # Formats de dates mixtes = 100% des données sont affectées
                    # Car l'incohérence structurelle touche TOUTE la colonne
                    P_DB = 1.0

        P_DB = min(1.0, P_DB)

        # ====================================================================
        # [DP] Data Processing - Erreurs de traitement
        # ====================================================================
        P_DP = 0.0

        # 1. Erreurs de parsing déjà détectées
        P_DP = col_stats.get('type_errors', {}).get('error_rate', 0)

        # 2. Formats de dates mixtes = problème de traitement aussi
        if date_formats_mixed:
            P_DP = max(P_DP, 0.5)  # Formats mixtes = problème de traitement significatif

        P_DP = min(1.0, P_DP)

        # ====================================================================
        # [BR] Business Rules - Violations métier
        # ====================================================================
        P_BR = col_stats.get('business_violations', {}).get('violation_rate', 0)

        # Détecter valeurs négatives dans colonnes numériques
        if col_stats['dtype'] in ['int64', 'float64']:
            numeric_vals = pd.to_numeric(series, errors='coerce')
            negative_count = (numeric_vals < 0).sum()
            if negative_count > 0:
                P_BR = max(P_BR, negative_count / total)

        # Détecter valeurs nulles/vides comme violation potentielle
        # (certaines colonnes ne devraient jamais être nulles)
        if col_stats['null_rate'] > 0.5:  # Plus de 50% nulls = problème sérieux
            P_BR = max(P_BR, col_stats['null_rate'] * 0.5)

        P_BR = min(1.0, P_BR)

        # ====================================================================
        # [UP] Usage-fit - Problèmes d'utilisabilité
        # ====================================================================
        P_UP = 0.0

        # 1. Taux de nulls (problème majeur d'utilisabilité)
        null_rate = col_stats['null_rate']
        P_UP = null_rate

        # 2. Outliers pour colonnes numériques
        outlier_rate = 0.0
        if col_stats['dtype'] in ['int64', 'float64']:
            try:
                numeric_vals = pd.to_numeric(series.dropna(), errors='coerce').dropna()
                if len(numeric_vals) > 10:
                    Q1 = numeric_vals.quantile(0.25)
                    Q3 = numeric_vals.quantile(0.75)
                    IQR = Q3 - Q1
                    if IQR > 0:
                        outliers = ((numeric_vals < Q1 - 1.5*IQR) | (numeric_vals > Q3 + 1.5*IQR)).sum()
                        outlier_rate = outliers / len(numeric_vals)
            except:
                pass

        # 3. Faible unicité (beaucoup de doublons)
        uniqueness_rate = col_stats['unique_count'] / total if total > 0 else 0
        if uniqueness_rate < 0.1:  # Moins de 10% unique = problème potentiel
            P_UP = max(P_UP, 0.3)

        P_UP = min(1.0, null_rate + outlier_rate * 0.5)  # Nulls + demi-outliers

        # ====================================================================
        # Calculer le vecteur Beta 4D
        # ====================================================================
        vector = calculator.compute_4d_vector(
            P_DB=P_DB,
            P_DP=P_DP,
            P_BR=P_BR,
            P_UP=P_UP,
            confidence_DB='HIGH' if P_DB > 0.05 else 'MEDIUM',
            confidence_DP='HIGH' if P_DP > 0.05 else 'MEDIUM',
            confidence_BR='HIGH' if P_BR > 0.05 else 'MEDIUM',
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

    # Test 4: Calculateur basé sur catalogue
    print("\n4. Test AnomalyBasedCalculator:")
    try:
        anomaly_calc = AnomalyBasedCalculator()
        print(f"   Catalogue chargé: {len(anomaly_calc.catalog_manager.catalog)} anomalies")

        # Afficher filtrage par niveau
        for level in [ProfilingLevel.QUICK, ProfilingLevel.STANDARD, ProfilingLevel.ADVANCED]:
            filtered = anomaly_calc.filter_anomalies_by_profiling_level(level)
            print(f"   Niveau {level}: {len(filtered)} anomalies à scanner")
    except Exception as e:
        print(f"   Erreur: {e}")
