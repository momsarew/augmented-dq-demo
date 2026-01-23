"""
adaptive_scan_engine.py
Moteur scan RÉEL uniquement avec apprentissage

- Pas de simulation
- 15 anomalies core non-chevauchantes
- Apprentissage adaptatif automatique
- Priorisation intelligente
"""

import pandas as pd
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

from core_anomaly_catalog import CoreCatalogManager, CoreAnomaly


@dataclass
class ScanResult:
    """Résultat scan UNE anomalie"""
    anomaly_id: str
    anomaly_name: str
    detected: bool
    affected_rows: int
    execution_time_ms: float
    details: Dict
    sample_data: List


@dataclass  
class ScanReport:
    """Rapport scan complet"""
    dataset_name: str
    total_rows: int
    total_columns: int
    scan_timestamp: datetime
    
    anomalies_scanned: int
    anomalies_detected: int
    
    results: List[ScanResult]
    total_execution_time_s: float
    
    def to_dict(self) -> Dict:
        """Sérialise en dict"""
        return {
            'dataset': self.dataset_name,
            'rows': self.total_rows,
            'columns': self.total_columns,
            'timestamp': self.scan_timestamp.isoformat(),
            'scanned': self.anomalies_scanned,
            'detected': self.anomalies_detected,
            'detection_rate': f"{self.anomalies_detected/self.anomalies_scanned:.1%}" if self.anomalies_scanned > 0 else "0%",
            'execution_time': f"{self.total_execution_time_s:.2f}s",
            'detected_by_dimension': self._get_detected_by_dim()
        }
    
    def _get_detected_by_dim(self) -> Dict:
        """Répartition détections par dimension"""
        by_dim = {}
        for r in self.results:
            if r.detected:
                dim = r.anomaly_id.split('#')[0]
                by_dim[dim] = by_dim.get(dim, 0) + 1
        return by_dim


class AdaptiveScanEngine:
    """Moteur scan avec apprentissage adaptatif"""
    
    def __init__(self):
        self.catalog_manager = CoreCatalogManager()
        self.scan_history: List[ScanReport] = []
    
    def scan_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        budget: str = "STANDARD",
        learn: bool = True,
        verbose: bool = True
    ) -> ScanReport:
        """
        Scan dataset avec détections réelles
        
        Args:
            df: DataFrame à analyser
            dataset_name: Nom dataset
            budget: "QUICK" (top 5) | "STANDARD" (top 10) | "DEEP" (les 15)
            learn: Activer apprentissage
            verbose: Afficher progress
        
        Returns:
            ScanReport
        """
        if verbose:
            print(f"\n🔍 SCAN ADAPTATIF: {dataset_name}")
            print(f"   Lignes: {len(df):,} | Colonnes: {len(df.columns)}")
            print(f"   Budget: {budget}")
        
        start_time = time.time()
        
        # Sélection anomalies selon budget + apprentissage
        if budget == "QUICK":
            anomalies = self.catalog_manager.get_top_priority(n=5)
        elif budget == "STANDARD":
            anomalies = self.catalog_manager.get_top_priority(n=10)
        else:  # DEEP
            anomalies = self.catalog_manager.catalog
        
        if verbose:
            print(f"   Anomalies sélectionnées: {len(anomalies)}")
            if len([a for a in anomalies if a.scan_count > 0]) > 0:
                print(f"   📊 Priorisation adaptative activée (basée sur historique)")
        
        # Scan
        results = []
        detected_count = 0
        
        for i, anomaly in enumerate(anomalies, 1):
            if verbose:
                print(f"   [{i}/{len(anomalies)}] {anomaly.id}: {anomaly.name[:50]}...", end='', flush=True)
            
            # Détection avec paramètres auto-détectés
            params = self._auto_detect_params(df, anomaly)
            result = self._scan_anomaly(df, anomaly, params)
            
            results.append(result)
            
            if result.detected:
                detected_count += 1
            
            # Apprentissage
            if learn:
                self.catalog_manager.update_stats(anomaly.id, result.detected)
            
            if verbose:
                status = "✅ DÉTECTÉ" if result.detected else "⚪ OK"
                print(f" {status} ({result.execution_time_ms:.1f}ms)")
        
        execution_time = time.time() - start_time
        
        # Rapport
        report = ScanReport(
            dataset_name=dataset_name,
            total_rows=len(df),
            total_columns=len(df.columns),
            scan_timestamp=datetime.now(),
            anomalies_scanned=len(anomalies),
            anomalies_detected=detected_count,
            results=results,
            total_execution_time_s=execution_time
        )
        
        self.scan_history.append(report)
        
        if verbose:
            print(f"\n✅ SCAN TERMINÉ en {execution_time:.2f}s")
            print(f"   Anomalies détectées: {detected_count}/{len(anomalies)}")
        
        return report
    
    def _scan_anomaly(
        self,
        df: pd.DataFrame,
        anomaly: CoreAnomaly,
        params: Dict
    ) -> ScanResult:
        """Scan UNE anomalie"""
        start_time = time.time()
        
        try:
            # Appel détecteur réel
            result_dict = anomaly.detector(df, **params)
            
            execution_time = (time.time() - start_time) * 1000
            
            return ScanResult(
                anomaly_id=anomaly.id,
                anomaly_name=anomaly.name,
                detected=result_dict.get('detected', False),
                affected_rows=result_dict.get('affected_rows', 0),
                execution_time_ms=execution_time,
                details=result_dict,
                sample_data=result_dict.get('sample', [])
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            return ScanResult(
                anomaly_id=anomaly.id,
                anomaly_name=anomaly.name,
                detected=False,
                affected_rows=0,
                execution_time_ms=execution_time,
                details={'error': str(e), 'reason': 'detector_failed'},
                sample_data=[]
            )
    
    def _auto_detect_params(self, df: pd.DataFrame, anomaly: CoreAnomaly) -> Dict:
        """Détection automatique paramètres selon anomalie"""
        params = {}
        
        # DB#1: NULL dans colonnes
        if anomaly.id == "DB#1":
            # Cherche colonnes avec NULL
            null_cols = [c for c in df.columns if df[c].isnull().any()]
            params['columns'] = null_cols[:5] if null_cols else []
        
        # DB#2: PK duplicates
        elif anomaly.id == "DB#2":
            # Cherche colonne ID/PK
            id_cols = [c for c in df.columns if 'id' in c.lower() or 'pk' in c.lower() or c.lower() == 'matricule']
            params['pk_column'] = id_cols[0] if id_cols else (df.columns[0] if len(df.columns) > 0 else 'id')
        
        # DB#3: Email invalides
        elif anomaly.id == "DB#3":
            # Cherche colonnes email
            email_cols = [c for c in df.columns if 'email' in c.lower() or 'mail' in c.lower()]
            params['email_columns'] = email_cols if email_cols else []
        
        # DB#4: Hors domaine
        elif anomaly.id == "DB#4":
            # Cherche colonnes catégorielles
            cat_cols = [c for c in df.columns if df[c].dtype == 'object' and df[c].nunique() < 20]
            if cat_cols:
                col = cat_cols[0]
                params['column'] = col
                params['valid_values'] = df[col].value_counts().head(10).index.tolist()
            else:
                params['column'] = 'dummy'
                params['valid_values'] = []
        
        # DB#5: Valeurs négatives
        elif anomaly.id == "DB#5":
            # Cherche colonnes numériques positives (age, salaire, montant, etc.)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            positive_cols = [c for c in numeric_cols if 'age' in c.lower() or 'salaire' in c.lower() or 
                           'montant' in c.lower() or 'prix' in c.lower() or 'quantite' in c.lower()]
            params['columns'] = positive_cols if positive_cols else numeric_cols[:3]
        
        # DP#1: Calculs dérivés
        elif anomaly.id == "DP#1":
            # Cherche colonnes date_naissance + age
            if 'date_naissance' in df.columns and 'age' in df.columns:
                params['source_cols'] = ['date_naissance']
                params['target_col'] = 'age'
                params['formula'] = 'age_from_birthdate'
            # Ou montant_ht + tva + ttc
            elif all(c in df.columns for c in ['montant_ht', 'taux_tva', 'montant_ttc']):
                params['source_cols'] = ['montant_ht', 'taux_tva']
                params['target_col'] = 'montant_ttc'
                params['formula'] = 'montant_ttc'
            else:
                params['source_cols'] = []
                params['target_col'] = 'dummy'
                params['formula'] = 'unknown'
        
        # DP#2: Division par zéro
        elif anomaly.id == "DP#2":
            # Cherche colonnes dénominateurs potentiels
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            denom_cols = [c for c in numeric_cols if 'quantite' in c.lower() or 'nb' in c.lower() or 
                         'count' in c.lower() or 'total' in c.lower()]
            params['denominator_cols'] = denom_cols if denom_cols else numeric_cols[:2]
        
        # DP#3: Type incorrect
        elif anomaly.id == "DP#3":
            # Cherche colonnes avec type potentiellement incorrect
            numeric_expected = [c for c in df.columns if 'montant' in c.lower() or 'prix' in c.lower() or 
                               'age' in c.lower() or 'salaire' in c.lower()]
            if numeric_expected:
                params['column'] = numeric_expected[0]
                params['expected_type'] = 'numeric'
            else:
                date_expected = [c for c in df.columns if 'date' in c.lower()]
                if date_expected:
                    params['column'] = date_expected[0]
                    params['expected_type'] = 'date'
                else:
                    params['column'] = df.columns[0] if len(df.columns) > 0 else 'dummy'
                    params['expected_type'] = 'numeric'
        
        # BR#1: Incohérences temporelles
        elif anomaly.id == "BR#1":
            # Cherche paires de dates
            date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
            if len(date_cols) >= 2:
                # Cherche start/end, debut/fin, entree/sortie
                start_candidates = [c for c in date_cols if 'start' in c.lower() or 'debut' in c.lower() or 
                                   'entree' in c.lower() or 'embauche' in c.lower()]
                end_candidates = [c for c in date_cols if 'end' in c.lower() or 'fin' in c.lower() or 
                                 'sortie' in c.lower() or 'depart' in c.lower()]
                
                if start_candidates and end_candidates:
                    params['start_col'] = start_candidates[0]
                    params['end_col'] = end_candidates[0]
                else:
                    params['start_col'] = date_cols[0]
                    params['end_col'] = date_cols[1]
            else:
                params['start_col'] = 'dummy_start'
                params['end_col'] = 'dummy_end'
        
        # BR#2: Hors bornes métier
        elif anomaly.id == "BR#2":
            # Cherche colonnes avec bornes business évidentes
            if 'age' in df.columns:
                params['column'] = 'age'
                params['min_val'] = 18
                params['max_val'] = 67
            elif 'salaire' in df.columns:
                params['column'] = 'salaire'
                params['min_val'] = 15000  # SMIC annuel
                params['max_val'] = 500000
            else:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    col = numeric_cols[0]
                    params['column'] = col
                    params['min_val'] = float(df[col].quantile(0.01))
                    params['max_val'] = float(df[col].quantile(0.99))
                else:
                    params['column'] = 'dummy'
                    params['min_val'] = 0
                    params['max_val'] = 100
        
        # BR#3: Combinaisons interdites
        elif anomaly.id == "BR#3":
            # Cherche forfait_jour + heures_sup
            if 'forfait_jour' in df.columns and 'heures_sup' in df.columns:
                params['col1'] = 'forfait_jour'
                params['val1'] = True
                params['col2'] = 'heures_sup'
                params['val2'] = df['heures_sup'].dropna().iloc[0] if len(df['heures_sup'].dropna()) > 0 else 0
            else:
                params['col1'] = 'dummy1'
                params['val1'] = 'value1'
                params['col2'] = 'dummy2'
                params['val2'] = 'value2'
        
        # BR#4: Obligations métier
        elif anomaly.id == "BR#4":
            # Cherche anciennete + prime
            if 'anciennete' in df.columns and 'prime_anciennete' in df.columns:
                params['condition_col'] = 'anciennete'
                params['condition_val'] = df[df['anciennete'] > 0]['anciennete'].iloc[0] if len(df[df['anciennete'] > 0]) > 0 else 1
                params['required_col'] = 'prime_anciennete'
            else:
                params['condition_col'] = 'dummy_cond'
                params['condition_val'] = 'value'
                params['required_col'] = 'dummy_req'
        
        # UP#1: Données obsolètes
        elif anomaly.id == "UP#1":
            # Cherche colonnes date MAJ
            date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower() or 'maj' in c.lower() or 'update' in c.lower()]
            if date_cols:
                params['date_col'] = date_cols[-1]  # Dernière colonne date = probablement MAJ
                params['max_age_days'] = 365  # 1 an
            else:
                params['date_col'] = 'dummy_date'
                params['max_age_days'] = 365
        
        # UP#2: Granularité excessive
        elif anomaly.id == "UP#2":
            # Cherche colonnes avec beaucoup de valeurs uniques
            high_card_cols = [c for c in df.columns if df[c].nunique() / len(df) > 0.8]
            if high_card_cols:
                params['column'] = high_card_cols[0]
                params['max_unique_ratio'] = 0.9
            else:
                params['column'] = df.columns[0] if len(df.columns) > 0 else 'dummy'
                params['max_unique_ratio'] = 0.9
        
        # UP#3: Granularité insuffisante
        elif anomaly.id == "UP#3":
            # Cherche colonnes avec peu de valeurs uniques
            cat_cols = [c for c in df.columns if df[c].dtype == 'object']
            if cat_cols:
                params['col'] = cat_cols[0]
                params['min_unique'] = 5
            else:
                params['col'] = df.columns[0] if len(df.columns) > 0 else 'dummy'
                params['min_unique'] = 5
        
        return params
    
    def get_learning_stats(self) -> pd.DataFrame:
        """Stats apprentissage en DataFrame"""
        return self.catalog_manager.get_stats_df()
    
    def get_scan_history_summary(self) -> pd.DataFrame:
        """Historique scans"""
        data = []
        for report in self.scan_history:
            data.append({
                'Dataset': report.dataset_name,
                'Date': report.scan_timestamp.strftime('%Y-%m-%d %H:%M'),
                'Lignes': report.total_rows,
                'Scannées': report.anomalies_scanned,
                'Détectées': report.anomalies_detected,
                'Taux': f"{report.anomalies_detected/report.anomalies_scanned:.1%}" if report.anomalies_scanned > 0 else "0%",
                'Temps': f"{report.total_execution_time_s:.2f}s"
            })
        
        return pd.DataFrame(data)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    import numpy as np
    
    # Dataset test
    print("🧪 GÉNÉRATION DATASET TEST")
    np.random.seed(42)
    
    test_df = pd.DataFrame({
        'employee_id': range(1, 501),
        'matricule': [f'EMP{i:04d}' if i != 250 else 'EMP0249' for i in range(1, 501)],  # 1 doublon
        'name': [f'Employee_{i}' if i % 50 != 0 else None for i in range(1, 501)],  # 10 NULL
        'email': [f'user{i}@company.com' if i % 30 != 0 else f'invalidemail{i}' for i in range(1, 501)],  # 17 invalides
        'age': [np.random.randint(22, 65) if i % 40 != 0 else -5 for i in range(1, 501)],  # 12 négatifs
        'salary': np.random.uniform(30000, 120000, 500),
        'hire_date': pd.date_range('2010-01-01', periods=500, freq='D'),
        'end_date': pd.date_range('2015-01-01', periods=500, freq='D'),
        'status': np.random.choice(['CDI', 'CDD', 'Stage', 'INVALID'], 500, p=[0.6, 0.2, 0.15, 0.05])
    })
    
    print(f"Dataset: {len(test_df)} lignes × {len(test_df.columns)} colonnes")
    
    # Créer moteur
    engine = AdaptiveScanEngine()
    
    # Scan 1: STANDARD
    print("\n" + "="*70)
    print("SCAN 1: STANDARD (avec apprentissage)")
    print("="*70)
    
    report1 = engine.scan_dataset(test_df, "Test_Employee_Data_1", budget="STANDARD")
    print("\n📊 RÉSUMÉ:")
    for key, value in report1.to_dict().items():
        print(f"  {key}: {value}")
    
    # Scan 2: QUICK (utilise apprentissage scan 1)
    print("\n" + "="*70)
    print("SCAN 2: QUICK (priorisation adaptative)")
    print("="*70)
    
    report2 = engine.scan_dataset(test_df, "Test_Employee_Data_2", budget="QUICK")
    
    # Stats apprentissage
    print("\n" + "="*70)
    print("📈 STATS APPRENTISSAGE")
    print("="*70)
    stats_df = engine.get_learning_stats()
    print(stats_df.to_string(index=False))
    
    # Historique
    print("\n" + "="*70)
    print("📜 HISTORIQUE SCANS")
    print("="*70)
    history_df = engine.get_scan_history_summary()
    print(history_df.to_string(index=False))
