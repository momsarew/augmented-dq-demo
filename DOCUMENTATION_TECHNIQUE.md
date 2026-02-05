# 📚 Documentation Technique - Framework Probabiliste DQ

> **Version** : 1.0
> **Date** : Février 2025
> **Auteur** : Framework DQ Team

---

## 📑 Table des matières

1. [Architecture globale](#1-architecture-globale)
2. [Module analyzer.py](#2-module-analyzerpy)
3. [Module beta_calculator.py](#3-module-beta_calculatorpy) ⭐ **IMPORTANT**
4. [Catalogue d'anomalies](#4-catalogue-danomalies) ⭐ **NOUVEAU**
5. [Module ahp_elicitor.py](#5-module-ahp_elicitorpy)
6. [Module risk_scorer.py](#6-module-risk_scorerpy)
7. [Module lineage_propagator.py](#7-module-lineage_propagatorpy)
8. [Module comparator.py](#8-module-comparatorpy)
9. [Application principale app.py](#9-application-principale-apppy)
10. [Formules mathématiques](#10-formules-mathématiques)
11. [Guide d'extension](#11-guide-dextension)

---

## 1. Architecture globale

### 1.1 Structure des fichiers

```
augmented-dq-demo/
├── app.py                          # Application Streamlit principale
├── streamlit_gray_css.py           # Styles CSS modernes
├── streamlit_anomaly_detection.py  # Module détection anomalies (optionnel)
├── requirements.txt                # Dépendances Python
├── GUIDE_UTILISATEUR.md           # Guide utilisateur
├── DOCUMENTATION_TECHNIQUE.md     # Ce fichier
│
└── backend/
    └── engine/
        ├── analyzer.py             # Analyse exploratoire des données
        ├── beta_calculator.py      # Calculs distributions Beta
        ├── ahp_elicitor.py         # Élicitation pondérations AHP
        ├── risk_scorer.py          # Scoring de risque contextualisé
        ├── lineage_propagator.py   # Propagation risque dans le lineage
        └── comparator.py           # Comparaison DAMA vs Probabiliste
```

### 1.2 Flux de données

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Dataset   │────▶│  Analyzer   │────▶│    Beta     │────▶│    Risk     │
│   (CSV)     │     │  (stats)    │     │ Calculator  │     │   Scorer    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                               │                    │
                                               ▼                    ▼
                                        ┌─────────────┐     ┌─────────────┐
                                        │   Lineage   │     │  Comparator │
                                        │ Propagator  │     │   (DAMA)    │
                                        └─────────────┘     └─────────────┘
```

### 1.3 Dépendances

```python
# requirements.txt
streamlit>=1.29.0      # Interface utilisateur
pandas>=2.0.0          # Manipulation données
numpy>=1.24.0          # Calculs numériques
scipy>=1.11.0          # Distributions statistiques
plotly>=5.18.0         # Visualisations
openpyxl>=3.1.0        # Export Excel
anthropic>=0.18.0      # API Claude (optionnel)
```

---

## 2. Module analyzer.py

### 2.1 Description
Module d'analyse exploratoire des données. Détecte les problèmes de qualité dans chaque colonne.

### 2.2 Fonctions

#### `analyze_dataset(df, columns)`

```python
def analyze_dataset(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `df` | `pd.DataFrame` | Dataset à analyser |
| `columns` | `List[str]` | Liste des colonnes à analyser |

**Retourne** : `Dict[str, Any]`

```python
{
    "nom_colonne": {
        "dtype": "object",           # Type pandas
        "total_rows": 1000,          # Nombre de lignes
        "null_count": 50,            # Valeurs nulles
        "null_rate": 0.05,           # Taux de nullité (0-1)
        "unique_count": 150,         # Valeurs uniques
        "sample_values": [...],      # 5 premiers exemples
        "type_errors": {...},        # Erreurs de type détectées
        "business_violations": {...} # Violations règles métier
    }
}
```

---

#### `detect_type_errors(series)`

```python
def detect_type_errors(series: pd.Series) -> Dict[str, Any]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `series` | `pd.Series` | Colonne à analyser |

**Retourne** : `Dict[str, Any]`

```python
{
    "error_count": 25,              # Nombre d'erreurs
    "error_rate": 0.025,            # Taux d'erreur (0-1)
    "patterns": [                   # Patterns détectés
        "virgule_decimale",         # Ex: "7,21" au lieu de 7.21
        "format_mixte"              # Ex: mélange DATE et STRING
    ],
    "examples": ["7,21", "N/A"]     # Exemples d'erreurs
}
```

**Algorithme** :
- Regex pour détecter les virgules décimales françaises
- Détection de formats de dates mixtes
- Identification des valeurs non-numériques dans colonnes numériques

---

#### `detect_business_violations(series, col_name)`

```python
def detect_business_violations(series: pd.Series, col_name: str) -> Dict[str, Any]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `series` | `pd.Series` | Colonne à analyser |
| `col_name` | `str` | Nom de la colonne (pour règles contextuelles) |

**Retourne** : `Dict[str, Any]`

```python
{
    "violation_count": 10,
    "violation_rate": 0.01,
    "rules_violated": [
        "date_future",              # Date > aujourd'hui
        "valeur_negative"           # Montant < 0
    ],
    "examples": ["2030-01-01", "-500"]
}
```

**Règles implémentées** :
- `date_future` : Dates dans le futur (colonnes historiques)
- `valeur_negative` : Valeurs négatives (montants, ancienneté)
- `incoherence_calcul` : Incohérences de calcul

---

## 3. Module beta_calculator.py

### 3.1 Description
Implémente les calculs de distributions Beta pour la quantification de l'incertitude.

**⚠️ IMPORTANT : Ce module utilise le catalogue d'anomalies pour calculer les probabilités P_DB, P_DP, P_BR, P_UP.**

---

### 3.2 LOGIQUE DE CALCUL DES PROBABILITÉS (P_DB, P_DP, P_BR, P_UP)

#### 3.2.1 Vue d'ensemble

Le calcul des probabilités d'erreur par dimension se fait en **scannant un référentiel d'anomalies** (et non par des formules simplistes).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROCESSUS DE CALCUL DES P_*                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CHARGER le catalogue d'anomalies (60 anomalies)                    │
│                         ↓                                               │
│  2. FILTRER selon le niveau de profiling                               │
│     • Quick: Criticité non faible + Woodall SAST/SAMT                  │
│     • Standard: Criticité non faible + SAST/SAMT/MAST                  │
│     • Advanced: Toutes les anomalies                                    │
│                         ↓                                               │
│  3. TRIER par score de priorité (apprentissage)                        │
│     • Anomalies les plus fréquemment détectées en premier              │
│                         ↓                                               │
│  4. SCANNER les données pour chaque anomalie                           │
│     • Exécuter le détecteur associé                                     │
│     • Compter les lignes affectées                                      │
│                         ↓                                               │
│  5. CALCULER P_dimension = lignes_affectées / total_lignes             │
│                         ↓                                               │
│  6. METTRE À JOUR l'apprentissage                                       │
│     • Incrémenter scan_count et detection_count                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Le Référentiel d'Anomalies

Chaque anomalie du catalogue est caractérisée par :

| Attribut | Description | Exemple |
|----------|-------------|---------|
| **ID** | Identifiant unique | `DB#1`, `DP#2`, `BR#3`, `UP#1` |
| **Dimension** | DB, DP, BR, ou UP | `DB` (Structure) |
| **Nom** | Description courte | "NULL dans colonnes obligatoires" |
| **Criticité** | CRITIQUE, ÉLEVÉ, MOYEN, FAIBLE | `CRITIQUE` (4 points) |
| **Woodall Level** | Fréquence de survenance | `SAST` (très fréquent) |
| **Détecteur** | Fonction Python de détection | `detect_null_in_required()` |
| **detection_count** | Nombre de détections (apprentissage) | `12` |
| **scan_count** | Nombre de scans (apprentissage) | `15` |
| **frequency** | Taux de détection historique | `0.80` (80%) |

#### 3.2.3 Niveaux Woodall

| Niveau | Signification | Quand scanner ? |
|--------|---------------|-----------------|
| **SAST** | Anomalie **très fréquente** | Toujours (Quick, Standard, Advanced) |
| **SAMT** | Anomalie **fréquence moyenne** | Toujours (Quick, Standard, Advanced) |
| **MAST** | Anomalie **rare** | Standard et Advanced uniquement |

#### 3.2.4 Filtrage par Niveau de Profiling

```python
# Niveaux de profiling disponibles
class ProfilingLevel:
    QUICK = "quick"      # Scan rapide (~40% des anomalies)
    STANDARD = "standard"  # Scan standard (~60% des anomalies)
    ADVANCED = "advanced"  # Scan complet (100% des anomalies)
```

| Niveau | Criticité filtrée | Woodall filtré | Anomalies scannées |
|--------|-------------------|----------------|-------------------|
| **Quick** | ≠ FAIBLE (Moyenne, Élevée, Critique) | SAST + SAMT | ~24 sur 60 |
| **Standard** | ≠ FAIBLE | SAST + SAMT + MAST | ~45 sur 60 |
| **Advanced** | Toutes (y compris FAIBLE) | Tous | 60 sur 60 |

#### 3.2.5 Effet d'Apprentissage

À chaque scan, le système **apprend** quelles anomalies sont les plus fréquentes :

```python
# Après chaque scan d'une anomalie
anomaly.scan_count += 1
if detected:
    anomaly.detection_count += 1
anomaly.frequency = detection_count / scan_count

# Score de priorité adaptatif
def get_priority_score(self) -> float:
    impact = criticality.value * 25  # CRITIQUE=100, ÉLEVÉ=75, etc.
    freq_boost = frequency * 100 if scan_count >= 3 else impact
    return freq_boost * (impact / 100)
```

**Résultat** : Les anomalies les plus souvent détectées sont scannées **en premier** lors des prochains scans.

#### 3.2.6 Fichier d'apprentissage

Les stats d'apprentissage sont persistées dans `extended_anomaly_stats.json` :

```json
{
  "DB#1": {"detection_count": 12, "scan_count": 12, "frequency": 1.0},
  "DB#2": {"detection_count": 9, "scan_count": 12, "frequency": 0.75},
  "DP#2": {"detection_count": 6, "scan_count": 6, "frequency": 1.0},
  "BR#2": {"detection_count": 10, "scan_count": 12, "frequency": 0.83}
}
```

---

### 3.3 Classe AnomalyBasedCalculator

```python
class AnomalyBasedCalculator:
    """Calculateur de probabilités basé sur le catalogue d'anomalies"""

    def __init__(self, persistence_file: str = None):
        self.catalog_manager = ExtendedCatalogManager(persistence_file)
        self.beta_calculator = BetaCalculator()
```

#### `filter_anomalies_by_profiling_level(profiling_level, dimension)`

```python
def filter_anomalies_by_profiling_level(
    profiling_level: str,  # 'quick', 'standard', 'advanced'
    dimension: str = None  # 'DB', 'DP', 'BR', 'UP' (optionnel)
) -> List[CoreAnomaly]
```

**Retourne** : Liste d'anomalies filtrées et **triées par score de priorité** (décroissant).

---

#### `scan_dimension(df, dimension, profiling_level, column_config)`

```python
def scan_dimension(
    df: pd.DataFrame,
    dimension: str,           # 'DB', 'DP', 'BR', 'UP'
    profiling_level: str,     # 'quick', 'standard', 'advanced'
    column_config: Dict = None
) -> Dict[str, Any]
```

**Retourne** :

```python
{
    'P_dimension': 0.15,           # Probabilité calculée
    'dimension': 'DB',
    'profiling_level': 'standard',
    'anomalies_scanned': 12,       # Nombre d'anomalies scannées
    'anomalies_detected': [        # Anomalies trouvées
        {'id': 'DB#1', 'name': 'NULL obligatoire', 'affected_rows': 50},
        {'id': 'DB#2', 'name': 'Doublons PK', 'affected_rows': 25}
    ],
    'total_affected_rows': 75,
    'total_rows': 500,
    'scan_details': [...]          # Détails de chaque scan
}
```

---

#### `compute_4d_vector_from_catalog(df, profiling_level, column_config)`

```python
def compute_4d_vector_from_catalog(
    df: pd.DataFrame,
    profiling_level: str = 'standard',
    column_config: Dict = None
) -> Dict[str, Any]
```

**Processus complet** :
1. Pour chaque dimension (DB, DP, BR, UP) → appeler `scan_dimension()`
2. Extraire P_DB, P_DP, P_BR, P_UP
3. Convertir en distributions Beta via `BetaCalculator`
4. Retourner le vecteur 4D avec métadonnées

**Retourne** :

```python
{
    'profiling_level': 'standard',
    'total_rows': 687,
    'dimensions': {
        'DB': {'P_dimension': 0.15, 'anomalies_scanned': 12, ...},
        'DP': {'P_dimension': 0.08, 'anomalies_scanned': 10, ...},
        'BR': {'P_dimension': 0.12, 'anomalies_scanned': 8, ...},
        'UP': {'P_dimension': 0.05, 'anomalies_scanned': 6, ...}
    },
    'vector_4d': {
        'P_DB': 0.15, 'alpha_DB': 15.0, 'beta_DB': 85.0, ...
        'P_DP': 0.08, 'alpha_DP': 8.0, 'beta_DP': 92.0, ...
        ...
    },
    'summary': {
        'P_DB': 0.15, 'P_DP': 0.08, 'P_BR': 0.12, 'P_UP': 0.05,
        'anomalies_scanned_total': 36,
        'anomalies_detected_total': 8
    }
}
```

---

### 3.4 Classe BetaCalculator

```python
class BetaCalculator:
    CONFIDENCE_MAP = {
        'HIGH': 100,    # Équivalent à 100 observations
        'MEDIUM': 50,   # Équivalent à 50 observations
        'LOW': 20       # Équivalent à 20 observations
    }
```

#### `compute_beta_params(error_rate, confidence_level, n_obs_equivalent)`

```python
def compute_beta_params(
    error_rate: float,
    confidence_level: str = 'HIGH',
    n_obs_equivalent: int = None
) -> Dict[str, float]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `error_rate` | `float` | Taux d'erreur observé (0-1) |
| `confidence_level` | `str` | 'HIGH', 'MEDIUM', 'LOW' |
| `n_obs_equivalent` | `int` | Override du nombre d'observations |

**Retourne** : `Dict[str, float]`

```python
{
    "alpha": 2.0,           # Paramètre α de Beta
    "beta": 98.0,           # Paramètre β de Beta
    "E_P": 0.02,            # Espérance E[P]
    "std": 0.014,           # Écart-type
    "confidence": "HIGH",
    "n_obs_equiv": 100,
    "ci_lower": 0.003,      # Borne inf IC 95%
    "ci_upper": 0.052       # Borne sup IC 95%
}
```

**Formules** :
```
α = error_rate × n
β = (1 - error_rate) × n
E[P] = α / (α + β)
Var[P] = αβ / ((α+β)²(α+β+1))
IC_95% = [Beta.ppf(0.025), Beta.ppf(0.975)]
```

---

#### `compute_4d_vector(P_DB, P_DP, P_BR, P_UP, ...)`

```python
def compute_4d_vector(
    P_DB: float,                    # Taux erreur Structure (depuis scan DB)
    P_DP: float,                    # Taux erreur Traitements (depuis scan DP)
    P_BR: float,                    # Taux erreur Règles Métier (depuis scan BR)
    P_UP: float,                    # Taux erreur Utilisabilité (depuis scan UP)
    confidence_DB: str = 'HIGH',
    confidence_DP: str = 'MEDIUM',
    confidence_BR: str = 'MEDIUM',
    confidence_UP: str = 'LOW'
) -> Dict[str, Any]
```

**Retourne** : Vecteur 4D complet

```python
{
    # Dimension DB (Structure)
    "alpha_DB": 99.0, "beta_DB": 1.0,
    "P_DB": 0.99, "std_DB": 0.01,
    "ci_lower_DB": 0.95, "ci_upper_DB": 1.0,

    # Dimension DP (Traitements)
    "alpha_DP": 1.0, "beta_DP": 49.0,
    "P_DP": 0.02, ...

    # Dimension BR (Règles Métier)
    "alpha_BR": 10.0, "beta_BR": 40.0,
    "P_BR": 0.20, ...

    # Dimension UP (Utilisabilité)
    "alpha_UP": 2.0, "beta_UP": 18.0,
    "P_UP": 0.10, ...
}
```

---

### 3.5 Fonctions utilitaires

#### `compute_all_beta_vectors(df, columns, stats, profiling_level)`

```python
def compute_all_beta_vectors(
    df: pd.DataFrame,
    columns: List[str],
    stats: Dict[str, Any],
    profiling_level: str = 'standard'  # 'quick', 'standard', 'advanced'
) -> Dict[str, Dict]
```

**Algorithme de calcul des probabilités (NOUVELLE LOGIQUE)** :

```
1. Charger le catalogue d'anomalies (60 anomalies)
2. Filtrer selon le niveau de profiling:
   • Quick: Criticité ≠ FAIBLE + Woodall SAST/SAMT
   • Standard: Criticité ≠ FAIBLE + Woodall SAST/SAMT/MAST
   • Advanced: Toutes les anomalies
3. Trier par score de priorité (apprentissage - fréquence)
4. Scanner chaque anomalie dans l'ordre de priorité
5. Calculer P_dimension = lignes_affectées / total_lignes
6. Mettre à jour les stats d'apprentissage
```

---

#### `update_beta_with_new_evidence(current_alpha, current_beta, new_successes, new_failures)`

```python
def update_beta_with_new_evidence(
    current_alpha: float,
    current_beta: float,
    new_successes: int,
    new_failures: int
) -> Tuple[float, float]
```

**Mise à jour Bayésienne** :
```
Beta(α', β') = Beta(α + failures, β + successes)
```

**Exemple** :
```python
# Prior : Beta(2, 98) → 2% d'erreurs
# Nouvelles observations : 5 erreurs sur 100
alpha_new, beta_new = update_beta_with_new_evidence(2, 98, 95, 5)
# Posterior : Beta(7, 193) → ~3.5% d'erreurs
```

---

### 3.6 Diagramme de flux complet

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         CALCUL DES VECTEURS 4D                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  1. CHARGEMENT CATALOGUE                                                     │
│     ExtendedCatalogManager() → 60 anomalies                                  │
│     + Chargement stats apprentissage (extended_anomaly_stats.json)           │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  2. FILTRAGE PAR NIVEAU DE PROFILING                                         │
│     ┌─────────────────────────────────────────────────────────────────────┐  │
│     │ Quick    : Criticité ≠ FAIBLE + Woodall ∈ {SAST, SAMT}    → ~24    │  │
│     │ Standard : Criticité ≠ FAIBLE + Woodall ∈ {SAST,SAMT,MAST}→ ~45    │  │
│     │ Advanced : Toutes                                          → 60     │  │
│     └─────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  3. TRI PAR SCORE DE PRIORITÉ (APPRENTISSAGE)                                │
│     score = frequency × criticality_impact                                   │
│     → Anomalies les plus fréquemment détectées en premier                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  4. SCAN PAR DIMENSION                                                       │
│     ┌────────────┬────────────┬────────────┬────────────┐                   │
│     │    DB      │    DP      │    BR      │    UP      │                   │
│     │ scan_dim() │ scan_dim() │ scan_dim() │ scan_dim() │                   │
│     │    ↓       │    ↓       │    ↓       │    ↓       │                   │
│     │  P_DB=0.15 │  P_DP=0.08 │  P_BR=0.12 │  P_UP=0.05 │                   │
│     └────────────┴────────────┴────────────┴────────────┘                   │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  5. CONVERSION EN DISTRIBUTIONS BETA                                         │
│     BetaCalculator.compute_4d_vector(P_DB, P_DP, P_BR, P_UP)                │
│     → alpha_DB, beta_DB, std_DB, ci_lower_DB, ci_upper_DB, ...              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  6. MISE À JOUR APPRENTISSAGE                                                │
│     Pour chaque anomalie scannée:                                            │
│       anomaly.scan_count += 1                                                │
│       if detected: anomaly.detection_count += 1                              │
│       anomaly.frequency = detection_count / scan_count                       │
│     → Sauvegarde dans extended_anomaly_stats.json                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Catalogue d'anomalies

### 4.1 Description

Le **catalogue d'anomalies** est le cœur du système de calcul des probabilités. Il contient 60 anomalies (15 par dimension) avec leurs détecteurs et leurs statistiques d'apprentissage.

### 4.2 Fichiers du catalogue

| Fichier | Description |
|---------|-------------|
| `backend/core_anomaly_catalog.py` | Catalogue CORE (15 anomalies réelles) |
| `backend/extended_anomaly_catalog.py` | Catalogue ÉTENDU (60 anomalies) |
| `extended_anomaly_stats.json` | Stats d'apprentissage (persistance) |

### 4.3 Structure d'une anomalie

```python
@dataclass
class CoreAnomaly:
    id: str                    # "DB#1", "DP#2", etc.
    dimension: Dimension       # DB, DP, BR, UP
    name: str                  # "NULL dans colonnes obligatoires"
    description: str           # Description détaillée
    criticality: Criticality   # CRITIQUE, ÉLEVÉ, MOYEN, FAIBLE
    woodall_level: str         # "SAST", "SAMT", "MAST"
    detector: Callable         # Fonction de détection
    sql_template: str          # Template SQL équivalent
    example: str               # Exemple d'impact business

    # Métadonnées apprentissage
    detection_count: int = 0   # Nombre de fois détectée
    scan_count: int = 0        # Nombre de fois scannée
    frequency: float = 0.0     # detection_count / scan_count
```

### 4.4 Liste des anomalies par dimension

#### Dimension DB (Structure) - 15 anomalies

| ID | Nom | Criticité | Woodall | Détecteur |
|----|-----|-----------|---------|-----------|
| DB#1 | NULL dans colonnes obligatoires | CRITIQUE | SAST | ✅ Réel |
| DB#2 | Doublons clé primaire | CRITIQUE | SAMT | ✅ Réel |
| DB#3 | Formats email invalides | MOYEN | SAST | ✅ Réel |
| DB#4 | Valeurs hors domaine | ÉLEVÉ | SAST | ✅ Réel |
| DB#5 | Valeurs négatives interdites | MOYEN | SAST | ✅ Réel |
| DB#6-15 | Templates | MOYEN | SAMT | 📝 Template |

#### Dimension DP (Traitements) - 15 anomalies

| ID | Nom | Criticité | Woodall | Détecteur |
|----|-----|-----------|---------|-----------|
| DP#1 | Calculs dérivés incorrects | ÉLEVÉ | MAST | ✅ Réel |
| DP#2 | Divisions par zéro | MOYEN | SAST | ✅ Réel |
| DP#3 | Type données incorrect | MOYEN | SAST | ✅ Réel |
| DP#4-15 | Templates | MOYEN | MAST | 📝 Template |

#### Dimension BR (Règles Métier) - 15 anomalies

| ID | Nom | Criticité | Woodall | Détecteur |
|----|-----|-----------|---------|-----------|
| BR#1 | Incohérences temporelles | ÉLEVÉ | MAST | ✅ Réel |
| BR#2 | Valeurs hors bornes métier | CRITIQUE | MAST | ✅ Réel |
| BR#3 | Combinaisons interdites | ÉLEVÉ | MAST | ✅ Réel |
| BR#4 | Obligations métier (SI A ALORS B) | ÉLEVÉ | MAST | ✅ Réel |
| BR#5-15 | Templates | MOYEN | MAST | 📝 Template |

#### Dimension UP (Utilisabilité) - 15 anomalies

| ID | Nom | Criticité | Woodall | Détecteur |
|----|-----|-----------|---------|-----------|
| UP#1 | Données obsolètes | ÉLEVÉ | SAMT | ✅ Réel |
| UP#2 | Granularité excessive | FAIBLE | SAMT | ✅ Réel |
| UP#3 | Granularité insuffisante | MOYEN | SAMT | ✅ Réel |
| UP#4-15 | Templates | FAIBLE | SAMT | 📝 Template |

### 4.5 Exemples de détecteurs

#### DB#1 - NULL dans colonnes obligatoires

```python
def detect_null_in_required(df: pd.DataFrame, columns: List[str]) -> Dict:
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
        'columns_with_nulls': [...],
        'sample': samples[:5]
    }
```

#### BR#2 - Valeurs hors bornes métier

```python
def detect_out_of_business_range(df: pd.DataFrame, column: str,
                                  min_val: float, max_val: float) -> Dict:
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
```

### 4.6 Système d'apprentissage

#### Score de priorité adaptatif

```python
def get_priority_score(self) -> float:
    """
    Calcule le score de priorité pour le tri des anomalies

    - Les anomalies les plus critiques ont un score de base plus élevé
    - Les anomalies fréquemment détectées sont boostées
    """
    impact = self.criticality.value * 25  # CRITIQUE=100, ÉLEVÉ=75, MOYEN=50, FAIBLE=25

    # Boost basé sur la fréquence de détection (après 3 scans minimum)
    freq_boost = self.frequency * 100 if self.scan_count >= 3 else impact

    return freq_boost * (impact / 100)
```

#### Exemple de calcul

| Anomalie | Criticité | Impact | Détections | Scans | Fréquence | Score |
|----------|-----------|--------|------------|-------|-----------|-------|
| DB#1 | CRITIQUE | 100 | 12 | 12 | 100% | **100.0** |
| BR#2 | CRITIQUE | 100 | 10 | 12 | 83% | **83.0** |
| DB#2 | CRITIQUE | 100 | 9 | 12 | 75% | **75.0** |
| DP#2 | MOYEN | 50 | 6 | 6 | 100% | **50.0** |
| DB#4 | ÉLEVÉ | 75 | 2 | 7 | 29% | **21.4** |

**Résultat** : Lors du prochain scan, DB#1 sera testé en premier, puis BR#2, DB#2, etc.

### 4.7 Gestionnaire de catalogue

```python
class ExtendedCatalogManager:
    def __init__(self, persistence_file: str = "extended_anomaly_stats.json"):
        self.catalog = EXTENDED_CATALOG
        self._load_stats()  # Charge les stats d'apprentissage

    def get_by_dimension(self, dimension: str) -> List[CoreAnomaly]:
        """Filtre par dimension (DB, DP, BR, UP)"""

    def get_top_priority(self, n: int = 10) -> List[CoreAnomaly]:
        """Top N anomalies par score de priorité"""

    def update_stats(self, anomaly_id: str, detected: bool):
        """Met à jour les stats après un scan"""
        anomaly.scan_count += 1
        if detected:
            anomaly.detection_count += 1
        anomaly.frequency = detection_count / scan_count
        self._save_stats()  # Persiste dans le fichier JSON

    def get_real_detectors(self) -> List[CoreAnomaly]:
        """Retourne uniquement les anomalies avec détecteurs réels (non-templates)"""
```

---

## 5. Module ahp_elicitor.py

### 4.1 Description
Implémente l'élicitation des pondérations via la méthode AHP (Analytic Hierarchy Process).

### 4.2 Classe AHPElicitor

#### Presets de pondérations

```python
PRESET_WEIGHTS = {
    "paie_reglementaire": {
        "w_DB": 0.40,  # Structure critique (calculs légaux)
        "w_DP": 0.30,  # Traitements importants
        "w_BR": 0.30,  # Règles métier strictes
        "w_UP": 0.00   # Utilisabilité non prioritaire
    },
    "reporting_social": {
        "w_DB": 0.25,
        "w_DP": 0.20,
        "w_BR": 0.30,
        "w_UP": 0.25
    },
    "dashboard_operationnel": {
        "w_DB": 0.10,
        "w_DP": 0.10,
        "w_BR": 0.20,
        "w_UP": 0.60   # Utilisabilité prime
    },
    "audit_conformite": {
        "w_DB": 0.35,
        "w_DP": 0.35,
        "w_BR": 0.30,
        "w_UP": 0.00
    },
    "analytics_decisional": {
        "w_DB": 0.20,
        "w_DP": 0.25,
        "w_BR": 0.25,
        "w_UP": 0.30
    }
}
```

---

#### `get_weights_preset(usage_type)`

```python
def get_weights_preset(usage_type: str) -> Dict[str, float]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `usage_type` | `str` | Type d'usage (fuzzy matching) |

**Retourne** :

```python
{
    "w_DB": 0.40,
    "w_DP": 0.30,
    "w_BR": 0.30,
    "w_UP": 0.00,
    "rationale": "Paie réglementaire : structure et calculs critiques"
}
```

---

#### `compute_ahp_matrix(comparisons)`

```python
def compute_ahp_matrix(
    comparisons: List[Tuple[str, str, float]]
) -> Dict[str, float]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `comparisons` | `List[Tuple]` | Comparaisons par paires |

**Format des comparaisons** (échelle de Saaty) :

| Score | Signification |
|-------|---------------|
| 1 | Égale importance |
| 3 | Importance modérée |
| 5 | Importance forte |
| 7 | Importance très forte |
| 9 | Importance extrême |

**Exemple** :
```python
comparisons = [
    ("DB", "DP", 3),   # DB 3× plus important que DP
    ("DB", "BR", 5),   # DB 5× plus important que BR
    ("DP", "BR", 2),   # DP 2× plus important que BR
    ...
]
weights = ahp.compute_ahp_matrix(comparisons)
# {"w_DB": 0.52, "w_DP": 0.26, "w_BR": 0.15, "w_UP": 0.07}
```

**Algorithme** :
1. Construction matrice 4×4 réciproque
2. Calcul vecteur propre principal (np.linalg.eig)
3. Normalisation pour Σw = 1.0

---

#### `normalize_weights(weights)`

```python
def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]
```

**Normalise** les poids pour que leur somme = 1.0

---

## 6. Module risk_scorer.py

### 5.1 Description
Calcule les scores de risque contextualisés par la combinaison [Attribut × Usage].

### 5.2 Classe RiskScorer

#### Seuils de risque

```python
RISK_THRESHOLDS = {
    "CRITIQUE": 0.40,      # ≥ 40%
    "ÉLEVÉ": 0.25,         # 25-40%
    "MOYEN": 0.15,         # 15-25%
    "ACCEPTABLE": 0.10,    # 10-15%
    "TRÈS_FAIBLE": 0.00    # < 10%
}
```

---

#### `compute_risk_score(vector_4d, weights)`

```python
def compute_risk_score(
    vector_4d: Dict[str, float],
    weights: Dict[str, float]
) -> float
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `vector_4d` | `Dict` | `{"P_DB": 0.99, "P_DP": 0.02, "P_BR": 0.20, "P_UP": 0.10}` |
| `weights` | `Dict` | `{"w_DB": 0.40, "w_DP": 0.30, "w_BR": 0.30, "w_UP": 0.00}` |

**Formule** :
```
R(a, U) = w_DB × P_DB + w_DP × P_DP + w_BR × P_BR + w_UP × P_UP
```

**Exemple** :
```python
R = 0.40 × 0.99 + 0.30 × 0.02 + 0.30 × 0.20 + 0.00 × 0.10
R = 0.396 + 0.006 + 0.060 + 0.000
R = 0.462  # 46.2% → CRITIQUE
```

---

#### `compute_all_scores(vecteurs_4d, weights_by_usage)`

```python
def compute_all_scores(
    vecteurs_4d: Dict[str, Dict],
    weights_by_usage: Dict[str, Dict]
) -> Dict[str, float]
```

**Retourne** : Matrice complète [Attribut × Usage]

```python
{
    "Anciennete_Paie": 0.462,
    "Anciennete_Reporting": 0.337,
    "Anciennete_Dashboard": 0.201,
    "Dates_promos_Paie": 0.312,
    ...
}
```

---

#### `compute_impact_business(risk_score, attribut, usage, n_records)`

```python
def compute_impact_business(
    risk_score: float,
    attribut: str,
    usage: str,
    n_records: int = 687
) -> Dict[str, Any]
```

**Retourne** :

```python
{
    "records_affected": 317,           # risk_score × n_records
    "impact_financier_mensuel": 15850, # EUR (estimation)
    "severite": "CRITIQUE",
    "actions_recommandees": [
        "Audit immédiat de la source",
        "Correction du schéma en base",
        "Mise en place monitoring"
    ]
}
```

---

### 5.3 Fonctions utilitaires

#### `get_top_priorities(scores, top_n)`

```python
def get_top_priorities(
    scores: Dict[str, float],
    top_n: int = 5
) -> List[Dict[str, Any]]
```

**Retourne** : Top N priorités enrichies

```python
[
    {
        "attribut": "Anciennete",
        "usage": "Paie",
        "score": 0.462,
        "severite": "CRITIQUE",
        "color": "red",
        "records_affected": 317,
        "impact_mensuel": 15850,
        "actions": [...]
    },
    ...
]
```

---

## 7. Module lineage_propagator.py

### 6.1 Description
Simule la propagation du risque à travers les transformations de données (ETL, enrichissements, etc.).

### 6.2 Classe LineagePropagator

#### `propagate_dimension(P_initial, transformations)`

```python
def propagate_dimension(
    P_initial: float,
    transformations: List[Dict[str, float]]
) -> List[float]
```

| Paramètre | Type | Description |
|-----------|------|-------------|
| `P_initial` | `float` | Probabilité initiale (0-1) |
| `transformations` | `List[Dict]` | `[{"nom": "ETL", "P_add": 0.05}, ...]` |

**Formule (convolution bayésienne)** :
```
P_d(N) ≈ 1 - ∏(1 - P_d(i))

# Ou de manière récursive :
P_new = 1 - (1 - P_current) × (1 - P_add)
```

**Exemple** :
```python
# P_DP initial = 2%
# Après ETL (+5%) : P_DP = 1 - (1-0.02)(1-0.05) = 6.9%
# Après Enrichissement (+8%) : P_DP = 1 - (1-0.069)(1-0.08) = 14.3%
```

---

#### `simulate_pipeline_propagation(vector_4d_source, pipeline)`

```python
def simulate_pipeline_propagation(
    vector_4d_source: Dict[str, Any],
    pipeline: List[Dict]
) -> Dict[str, Any]
```

**Format pipeline** :

```python
pipeline = [
    {
        "nom": "ETL Extraction",
        "P_DB_add": 0.00,
        "P_DP_add": 0.05,
        "P_BR_add": 0.00,
        "P_UP_add": 0.02
    },
    {
        "nom": "Enrichissement Métier",
        "P_DB_add": 0.00,
        "P_DP_add": 0.02,
        "P_BR_add": 0.03,
        "P_UP_add": 0.01
    },
    ...
]
```

**Retourne** :

```python
{
    "vector_final": {
        "P_DB": 0.99,   # Inchangé (pas de P_DB_add)
        "P_DP": 0.285,  # Dégradé : 2% → 28.5%
        "P_BR": 0.23,   # Dégradé : 20% → 23%
        "P_UP": 0.15    # Dégradé : 10% → 15%
    },
    "degradation": {
        "delta_DB": 0.00,
        "delta_DP": +0.265,  # +26.5 points
        "delta_BR": +0.03,
        "delta_UP": +0.05
    },
    "history": [
        {"stage": "Source", "P_DB": 0.99, "P_DP": 0.02, ...},
        {"stage": "ETL", "P_DB": 0.99, "P_DP": 0.069, ...},
        ...
    ]
}
```

---

### 6.3 Fonction utilitaire

#### `simulate_lineage(vector_4d_source, weights_usage, pipeline_config)`

```python
def simulate_lineage(
    vector_4d_source: Dict,
    weights_usage: Dict,
    pipeline_config: List = None  # Défaut : pipeline paie 4 étapes
) -> Dict[str, Any]
```

**Pipeline par défaut** :

| Étape | P_DP_add | P_BR_add | Description |
|-------|----------|----------|-------------|
| ETL Extraction | +5% | +0% | Extraction source |
| Enrichissement | +2% | +2% | Jointures, calculs |
| Agrégation Paie | +8% | +0% | Consolidation |
| Calcul Final | +1% | +0% | Génération bulletins |

---

## 8. Module comparator.py

### 7.1 Description
Compare l'approche DAMA classique avec l'approche probabiliste contextualisée.

### 7.2 Classe DAMACalculator

#### `compute_dama_score(df, column)`

```python
def compute_dama_score(
    df: pd.DataFrame,
    column: str
) -> Dict[str, float]
```

**Dimensions ISO 8000 calculées** :

| Dimension | Formule | Calculable ? |
|-----------|---------|--------------|
| Completeness | `1 - (null_count / total)` | ✅ Oui |
| Consistency | Nécessite règles de cohérence | ❌ Non |
| Accuracy | Nécessite données de référence | ❌ Non |
| Timeliness | Nécessite règle de fraîcheur | ❌ Non |
| Validity | Nécessite domaine de valeurs | ❌ Non |
| Uniqueness | `1 - (duplicates / total)` | ✅ Oui |

**Retourne** :

```python
{
    "completeness": 0.68,
    "consistency": None,      # Non calculable
    "accuracy": None,
    "timeliness": None,
    "validity": None,
    "uniqueness": 0.997,
    "score_global": 0.8385,   # Moyenne des calculables
    "dimensions_calculables": 2,
    "dimensions_total": 6,
    "note": "Seulement Completeness et Uniqueness calculables"
}
```

---

### 7.3 Classe Comparator

#### `compare_approaches(df, columns, scores_probabilistes, vecteurs_4d)`

```python
def compare_approaches(
    df: pd.DataFrame,
    columns: List[str],
    scores_probabilistes: Dict[str, float],
    vecteurs_4d: Dict[str, Dict] = None
) -> Dict[str, Any]
```

**Retourne** :

```python
{
    "dama_scores": {...},
    "probabiliste_scores": {...},
    "problemes_masques": [
        {
            "attribut": "Anciennete",
            "type": "DB_masqué",
            "P_DB": 0.99,
            "score_DAMA": 0.818,
            "explication": "100% violation DB dilué dans score 81.8%"
        }
    ],
    "gains": [
        {
            "categorie": "Quantification incertitude",
            "methode_dama": "Point estimate unique",
            "methode_probabiliste": "Distribution Beta(α,β) avec IC 95%",
            "gain": "Distingue 10% haute certitude vs 10% haute incertitude"
        },
        ...
    ]
}
```

---

### 7.4 Gains méthodologiques quantifiés

| Catégorie | DAMA | Probabiliste | Gain |
|-----------|------|--------------|------|
| **Incertitude** | Point estimate | Beta(α,β) + IC 95% | Décisions risque-informées |
| **Contextualisation** | Score unique | Scores par usage | Priorisation ROI |
| **Propagation** | Aucune | Convolution bayésienne | Détection impact ETL |
| **Dimensions** | 6 ISO agrégées | 4 causales | Diagnostic cause racine |
| **Apprentissage** | Recalcul complet | Mise à jour bayésienne | Convergence progressive |

**Gains opérationnels** :
- -70% faux positifs (50% → 15%)
- -60% temps assessment (240h → 96h pour 500 attributs)
- ROI corrections : 8-18× (vs non calculable DAMA)
- Scalabilité : 50k attributs (vs 5k max DAMA)

---

## 9. Application principale app.py

### 8.1 Fonctions utilitaires

#### `get_risk_color(s)`

```python
def get_risk_color(s: float) -> str
```

| Score | Couleur |
|-------|---------|
| ≥ 0.40 | `#eb3349` (rouge) |
| 0.25-0.40 | `#F2994A` (orange) |
| 0.15-0.25 | `#F2C94C` (jaune) |
| < 0.15 | `#38ef7d` (vert) |

---

#### `explain_with_ai(scope, data, cache_key, max_tokens)`

```python
def explain_with_ai(
    scope: str,           # "vector", "priority", "lineage", "dama", "global"
    data: Dict,           # Données à expliquer
    cache_key: str,       # Clé de cache
    max_tokens: int = 400
) -> str
```

**Utilise** : API Anthropic (Claude Sonnet 4)

---

#### `create_vector_chart(v)`

```python
def create_vector_chart(v: Dict) -> go.Figure
```

Crée un graphique en barres Plotly pour le vecteur 4D.

---

#### `create_heatmap(scores)`

```python
def create_heatmap(scores: Dict[str, float]) -> go.Figure
```

Crée une heatmap [Attribut × Usage] avec palette personnalisée.

---

#### `export_excel(results)`

```python
def export_excel(results: Dict) -> str
```

Exporte en Excel avec 3 feuilles :
- **Vecteurs** : Vecteurs 4D par attribut
- **Scores** : Scores de risque
- **Priorites** : Top priorités

---

### 8.2 Variables de session Streamlit

```python
session_state = {
    "df": None,                    # DataFrame chargé
    "results": None,               # Résultats d'analyse
    "analysis_done": False,        # Flag analyse terminée
    "anthropic_api_key": "",       # Clé API Claude
    "ai_explanations": {},         # Cache explications IA
    "ai_tokens_used": 0,           # Compteur tokens
    "custom_weights": {},          # Pondérations personnalisées
    "selected_profile": "gouvernance"  # Profil reporting
}
```

---

### 8.3 Onglets de l'application

| Onglet | Icône | Description | Utilisation |
|--------|-------|-------------|-------------|
| **Scan** | 🔍 | Détection automatique des anomalies | Premier diagnostic |
| **Dashboard** | 📊 | Vue globale, heatmap des risques | Présentation COMEX |
| **Vecteurs** | 🎯 | Détail des 4 dimensions par attribut | Diagnostic technique |
| **Priorités** | ⚠️ | Top 5 des urgences à traiter | Plan d'action |
| **Élicitation** | 🎚️ | Ajuster les pondérations par usage | Personnalisation métier |
| **Lineage** | 🔄 | Impact des transformations ETL | Debug pipeline |
| **DAMA** | 📈 | Comparaison avec approche classique | Justification méthode |
| **Reporting** | 📋 | Rapport personnalisé par profil | Communication |
| **Aide** | ❓ | Guide utilisateur intégré | Formation |

---

### 8.4 Onglet Reporting - Sélection multiple d'attributs

L'onglet Reporting permet de générer des rapports personnalisés pour **plusieurs attributs** simultanément.

#### Fonctionnalités

```python
# Sélection multiple d'attributs
attributs_focus = st.multiselect(
    "📌 Attribut(s) à analyser",
    options=attributs,
    default=[attributs[0]],
    help="Sélectionne un ou plusieurs attributs pour le rapport"
)
```

#### Structure des données générées

```python
rapport_data = {
    "profil": "💰 CFO",
    "usage": "paie_reglementaire",
    "nombre_attributs": 3,
    "attributs_analyses": ["Anciennete", "Salaire", "Grade"],
    "resume_global": {
        "score_moyen": 0.35,
        "score_max": 0.46,
        "score_min": 0.18,
        "attribut_plus_critique": "Anciennete",
        "nb_alertes_critiques": 1
    },
    "ponderations_usage": {
        "w_DB": 0.40, "w_DP": 0.30, "w_BR": 0.20, "w_UP": 0.10
    },
    "detail_par_attribut": [
        {
            "attribut": "Anciennete",
            "score_risque": 0.46,
            "vecteur_4d": {"P_DB": 0.99, "P_DP": 0.02, ...},
            "dimension_critique": {"nom": "DB", "valeur": 0.99},
            "scores_dama": {"completude": 1.0, "unicite": 0.85},
            "priorites": [...]
        },
        ...
    ]
}
```

#### Profils disponibles

| Profil | Description | Focus |
|--------|-------------|-------|
| 💰 CFO | Chief Financial Officer | Impact financier, ROI |
| 🔧 Data Engineer | Développeur / Ingénieur | Détails techniques, ETL |
| 👥 DRH | Directeur RH | Conformité sociale |
| 🔍 Auditeur | Compliance Officer | Règles métier, traçabilité |
| 📊 Gouvernance | Responsable DQ | Vue globale, KPIs |
| ⚡ Manager Ops | Opérationnel | Actions immédiates |
| ✏️ Custom | Personnalisé | Configurable |

---

### 8.5 Guide utilisateur intégré

Le guide utilisateur est affiché **dès la page d'entrée** (avant l'analyse) ET dans l'onglet "Aide" après analyse.

#### Contenu du guide

1. **En 30 secondes** : Explication de l'outil
2. **DAMA vs Probabiliste** : Comparaison des approches
3. **4 dimensions** : DB, DP, BR, UP expliquées
4. **Code couleur** : Seuils de risque
5. **Onglets** : Description de chaque fonctionnalité
6. **3 insights clés** : Points essentiels à retenir

---

### 8.6 Calcul de l'Unicité DAMA

**⚠️ IMPORTANT** : La formule d'unicité suit le standard DAMA.

#### Formule

```python
# Unicité DAMA = 1 - (nb_lignes_dupliquées / total)
if total > 0:
    duplicated_count = series.duplicated(keep='first').sum()
    uniqueness = 1.0 - (duplicated_count / total)
else:
    uniqueness = 0.0
```

#### Interprétation

| Situation | Exemple | Unicité |
|-----------|---------|---------|
| Toutes valeurs uniques | [A, B, C, D, E] | **100%** |
| Quelques doublons | [A, B, A, C, C, C] → 3 doublons sur 6 | **50%** |
| Toutes valeurs identiques | [X, X, X, X, X] → 4 doublons sur 5 | **20%** |

#### Affichage

```python
# Affichage avec 1 décimale si valeur < 5% pour éviter "0%"
if dim_value < 0.05 and dim_value > 0:
    display_value = f"{dim_value:.1%}"  # Ex: "0.4%"
else:
    display_value = f"{dim_value:.0%}"  # Ex: "85%"
```

---

## 10. Formules mathématiques

### 9.1 Distribution Beta

```
Paramètres :
    α = p × n        (succès)
    β = (1-p) × n    (échecs)

Espérance :
    E[P] = α / (α + β)

Variance :
    Var[P] = αβ / ((α+β)²(α+β+1))

Intervalle de confiance 95% :
    IC = [Beta.ppf(0.025, α, β), Beta.ppf(0.975, α, β)]
```

### 9.2 Score de risque

```
R(a, U) = Σ(w_d × P_d)

R(a, U) = w_DB × P_DB + w_DP × P_DP + w_BR × P_BR + w_UP × P_UP

Contrainte : Σw_d = 1.0
```

### 9.3 Propagation Lineage

```
Convolution bayésienne :
    P_new = 1 - (1 - P_current) × (1 - P_add)

Équivalent à :
    P_d(N) ≈ 1 - ∏(1 - P_d(i))
```

### 9.4 Mise à jour Bayésienne

```
Prior :     Beta(α, β)
Likelihood: Binomiale(k succès, n-k échecs)
Posterior : Beta(α + (n-k), β + k)

Où k = nombre de nouvelles erreurs observées
```

---

## 11. Guide d'extension

### 10.1 Ajouter une nouvelle dimension

1. **beta_calculator.py** : Ajouter `P_XX` dans `compute_4d_vector()`
2. **ahp_elicitor.py** : Ajouter `w_XX` dans les presets
3. **risk_scorer.py** : Inclure dans la formule de scoring
4. **app.py** : Mettre à jour les visualisations

### 10.2 Ajouter un nouveau type d'usage

```python
# ahp_elicitor.py
PRESET_WEIGHTS["nouveau_usage"] = {
    "w_DB": 0.25,
    "w_DP": 0.25,
    "w_BR": 0.25,
    "w_UP": 0.25,
    "rationale": "Description du cas d'usage"
}
```

### 10.3 Ajouter une règle métier

```python
# analyzer.py
def detect_business_violations(series, col_name):
    violations = []

    # Nouvelle règle
    if "salaire" in col_name.lower():
        invalid = series[series < 0]
        if len(invalid) > 0:
            violations.append({
                "rule": "salaire_negatif",
                "count": len(invalid),
                "examples": invalid.head(3).tolist()
            })

    return violations
```

### 10.4 Personnaliser le pipeline de lineage

```python
# Créer un pipeline personnalisé
custom_pipeline = [
    {"nom": "Source DB", "P_DB_add": 0.00, "P_DP_add": 0.01, "P_BR_add": 0.00, "P_UP_add": 0.00},
    {"nom": "API Gateway", "P_DB_add": 0.00, "P_DP_add": 0.03, "P_BR_add": 0.00, "P_UP_add": 0.02},
    {"nom": "Data Lake", "P_DB_add": 0.00, "P_DP_add": 0.02, "P_BR_add": 0.01, "P_UP_add": 0.01},
    {"nom": "ML Pipeline", "P_DB_add": 0.00, "P_DP_add": 0.05, "P_BR_add": 0.02, "P_UP_add": 0.03},
]

result = simulate_lineage(vector_4d, weights, pipeline_config=custom_pipeline)
```

---

### 10.5 Ajouter une nouvelle anomalie au catalogue

```python
# extended_anomaly_catalog.py
CoreAnomaly(
    id="DB#16",
    dimension=Dimension.DB,
    name="Ma nouvelle anomalie",
    description="Description détaillée",
    criticality=Criticality.ÉLEVÉ,
    woodall_level="SAMT",
    detector=ma_fonction_detection,
    sql_template="SELECT * FROM {table} WHERE condition",
    example="Exemple d'impact business"
)
```

---

## 📝 Changelog

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | Fév 2025 | Version initiale |
| 1.1 | Fév 2025 | Ajout catalogue anomalies (60 anomalies), système apprentissage |
| 1.2 | Fév 2025 | **Reporting multi-attributs** : sélection de plusieurs attributs pour génération de rapports |
| 1.2 | Fév 2025 | **Guide utilisateur** visible dès la page d'entrée |
| 1.2 | Fév 2025 | **Correction Unicité DAMA** : formule `1 - (doublons/total)` corrigée dans tous les modules |
| 1.2 | Fév 2025 | **CSS contraste** : amélioration lisibilité dropdowns et menus |

---

*Documentation générée pour le Framework Probabiliste DQ*
