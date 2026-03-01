# Documentation Technique - Augmented DQ Framework

> **Version** : 3.0
> **Date** : Mars 2026
> **Auteur** : Framework DQ Team

---

## Table des matieres

1. [Architecture globale](#1-architecture-globale)
2. [Module analyzer.py](#2-module-analyzerpy)
3. [Module beta_calculator.py](#3-module-beta_calculatorpy)
4. [Catalogue d'anomalies (YAML)](#4-catalogue-danomalies-yaml)
5. [Module ahp_elicitor.py](#5-module-ahp_elicitorpy)
6. [Module risk_scorer.py](#6-module-risk_scorerpy)
7. [Module lineage_propagator.py](#7-module-lineage_propagatorpy)
8. [Module comparator.py](#8-module-comparatorpy)
9. [Module Data Contracts](#9-module-data-contracts)
10. [Application principale app.py](#10-application-principale-apppy)
11. [Formules mathematiques](#11-formules-mathematiques)
12. [Guide d'extension](#12-guide-dextension)

---

## 1. Architecture globale

### 1.1 Structure des fichiers

```
augmented-dq-demo/
├── app.py                              # Orchestrateur principal Streamlit
├── setup_mac.sh                        # Script setup Mac automatique
├── requirements.txt                    # Dependances Python
├── DOCUMENTATION_TECHNIQUE.md          # Ce fichier
├── GUIDE_UTILISATEUR.md                # Guide utilisateur
│
├── frontend/                           # Couche presentation
│   ├── __init__.py
│   ├── components/                     # Composants partages
│   │   ├── __init__.py
│   │   ├── theme.py                    # Couleurs et styles (get_risk_color)
│   │   ├── charts.py                   # Graphiques Plotly (vecteur 4D, heatmap)
│   │   ├── ai_explain.py              # Helper Claude API (explain_with_ai)
│   │   └── export.py                   # Export Excel multi-feuilles
│   └── tabs/                           # Un module par onglet
│       ├── __init__.py
│       ├── home.py                     # Accueil
│       ├── dashboard.py               # Dashboard global
│       ├── vectors.py                  # Vecteurs 4D detailles
│       ├── priorities.py               # Top priorites
│       ├── elicitation.py              # Elicitation AHP
│       ├── risk_profile.py             # Profil de risque
│       ├── lineage.py                  # Propagation ETL
│       ├── dama.py                     # Comparaison DAMA
│       ├── reporting.py                # Rapports contextuels IA
│       ├── data_contracts.py           # Data Contracts (v4 — dynamique YAML)
│       ├── settings.py                 # Parametres et admin
│       └── help.py                     # Guide utilisateur
│
├── backend/                            # Couche metier
│   ├── __init__.py
│   ├── rules_catalog.yaml             # REFERENTIEL : 128 anomalies (source unique)
│   ├── rules_catalog_loader.py        # Chargeur YAML + API ODCS + import CSV
│   ├── anomaly_referential.py         # Couche compatibilite (lit le YAML)
│   ├── security.py                     # Securite (XSS, validation, sanitization)
│   ├── audit_trail.py                  # Audit trail complet
│   ├── adaptive_scan_engine.py         # Scan adaptatif
│   ├── scan_to_beta_connector.py       # Scan -> Beta distribution
│   └── engine/                         # Moteur de calcul
│       ├── __init__.py
│       ├── analyzer.py                 # Analyse exploratoire des donnees
│       ├── beta_calculator.py          # Calculs distributions Beta
│       ├── ahp_elicitor.py             # Elicitation ponderations AHP
│       ├── risk_scorer.py              # Scoring de risque contextualise
│       ├── lineage_propagator.py       # Propagation risque dans le lineage
│       └── comparator.py              # Comparaison DAMA vs Probabiliste
│
├── tests/                              # Tests pre-deploiement
│   ├── test_comprehensive.py           # 32 tests (coherence, edge cases, stress)
│   ├── test_advanced.py                # 8 tests modules avances
│   ├── test_dama_complete.py           # Test complet DAMA vs 4D
│   └── test_end_to_end.py             # Test pipeline bout en bout
│
└── docs/                               # Documentation architecture
    ├── ARCHITECTURE.md                 # Architecture C4
    └── ARCHITECTURE_DIAGRAMS.md        # Diagrammes Mermaid
```

### 1.2 Flux de donnees

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Dataset   │────>│  Analyzer   │────>│    Beta     │────>│    Risk     │
│   (CSV)     │     │  (stats)    │     │ Calculator  │     │   Scorer    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                               │                    │
                                               v                    v
                                        ┌─────────────┐     ┌─────────────┐
                                        │   Lineage   │     │  Comparator │
                                        │ Propagator  │     │   (DAMA)    │
                                        └─────────────┘     └─────────────┘
```

### 1.3 Dependances

```python
# requirements.txt
streamlit>=1.29.0      # Interface utilisateur
pandas>=2.0.0          # Manipulation donnees
numpy>=1.24.0          # Calculs numeriques
scipy>=1.11.0          # Distributions statistiques
plotly>=5.18.0         # Visualisations
openpyxl>=3.1.0        # Export Excel
pyyaml>=6.0            # Chargement catalogue YAML
anthropic>=0.18.0      # API Claude (optionnel)
```

---

## 2. Module analyzer.py

### 2.1 Description
Module d'analyse exploratoire des donnees. Detecte les problemes de qualite dans chaque colonne.

### 2.2 Fonctions

#### `analyze_dataset(df, columns)`

```python
def analyze_dataset(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]
```

| Parametre | Type | Description |
|-----------|------|-------------|
| `df` | `pd.DataFrame` | Dataset a analyser |
| `columns` | `List[str]` | Liste des colonnes a analyser |

**Retourne** : `Dict[str, Any]`

```python
{
    "nom_colonne": {
        "dtype": "object",           # Type pandas
        "total_rows": 1000,          # Nombre de lignes
        "null_count": 50,            # Valeurs nulles
        "null_rate": 0.05,           # Taux de nullite (0-1)
        "unique_count": 150,         # Valeurs uniques
        "sample_values": [...],      # 5 premiers exemples
        "type_errors": {...},        # Erreurs de type detectees
        "business_violations": {...} # Violations regles metier
    }
}
```

---

#### `detect_type_errors(series)`

```python
def detect_type_errors(series: pd.Series) -> Dict[str, Any]
```

**Retourne** : `Dict[str, Any]`

```python
{
    "error_count": 25,
    "error_rate": 0.025,
    "patterns": ["virgule_decimale", "format_mixte"],
    "examples": ["7,21", "N/A"]
}
```

**Algorithme** :
- Regex pour detecter les virgules decimales francaises
- Detection de formats de dates mixtes
- Identification des valeurs non-numeriques dans colonnes numeriques

---

#### `detect_business_violations(series, col_name)`

```python
def detect_business_violations(series: pd.Series, col_name: str) -> Dict[str, Any]
```

**Retourne** : `Dict[str, Any]`

```python
{
    "violation_count": 10,
    "violation_rate": 0.01,
    "rules_violated": ["date_future", "valeur_negative"],
    "examples": ["2030-01-01", "-500"]
}
```

**Regles implementees** :
- `date_future` : Dates dans le futur (colonnes historiques)
- `valeur_negative` : Valeurs negatives (montants, anciennete)
- `incoherence_calcul` : Incoherences de calcul

---

## 3. Module beta_calculator.py

### 3.1 Description
Implemente les calculs de distributions Beta pour la quantification de l'incertitude.

**Ce module utilise le catalogue d'anomalies YAML pour calculer les probabilites P_DB, P_DP, P_BR, P_UP.**

---

### 3.2 Logique de calcul des probabilites (P_DB, P_DP, P_BR, P_UP)

#### 3.2.1 Vue d'ensemble

Le calcul des probabilites d'erreur par dimension se fait en **scannant le referentiel d'anomalies** (128 anomalies dans `rules_catalog.yaml`).

```
┌────────────────────────────────────────────────────────────────────┐
│                 PROCESSUS DE CALCUL DES P_*                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. CHARGER le catalogue d'anomalies (128 anomalies YAML)         │
│                         |                                          │
│  2. FILTRER selon le budget de scan                                │
│     - QUICK   : top 5 anomalies par priorite                      │
│     - STANDARD: top 10 anomalies par priorite                     │
│     - DEEP    : toutes les anomalies                              │
│                         |                                          │
│  3. TRIER par score de priorite (apprentissage)                    │
│     - Anomalies les plus frequemment detectees en premier          │
│                         |                                          │
│  4. SCANNER les donnees pour chaque anomalie                       │
│     - Executer le detecteur associe                                │
│     - Compter les lignes affectees                                 │
│                         |                                          │
│  5. CALCULER P_dimension = lignes_affectees / total_lignes         │
│                         |                                          │
│  6. METTRE A JOUR l'apprentissage                                  │
│     - Incrementer scan_count et detection_count                    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 Le referentiel d'anomalies (YAML)

Le referentiel est stocke dans `backend/rules_catalog.yaml` et charge par `backend/rules_catalog_loader.py`.

Chaque anomalie est caracterisee par :

| Attribut | Description | Exemple |
|----------|-------------|---------|
| **ID** | Identifiant unique | `DB#1`, `DP#2`, `BR#3`, `UP#1` |
| **dimension** | DB, DP, BR, ou UP | `DB` |
| **nom** | Description courte | "NULL dans colonnes obligatoires" |
| **criticite** | CRITIQUE, ELEVE, MOYEN, FAIBLE | `CRITIQUE` |
| **detection** | Auto, Semi, Manuel | `Auto` |
| **default_rule_type** | Type de regle pour validation auto | `null_check` |

Chaque `rule_type` dans la section `rule_types:` contient :

| Attribut | Description | Exemple |
|----------|-------------|---------|
| **category** | Categorie DAMA/ISO 8000 | `Completude` |
| **validator** | Nom du validateur Python | `null_check` |
| **odcs** | Configuration export ODCS v3.1.0 | `{type: library, metric: nullValues}` |

#### 3.2.3 Budgets de scan

| Budget | Anomalies scannees | Cas d'usage |
|--------|-------------------|-------------|
| **QUICK** | Top 5 par priorite | Diagnostic rapide |
| **STANDARD** | Top 10 par priorite | Analyse courante |
| **DEEP** | Toutes (128) | Audit complet |

#### 3.2.4 Effet d'apprentissage

A chaque scan, le systeme **apprend** quelles anomalies sont les plus frequentes :

```python
# Apres chaque scan d'une anomalie
anomaly.scan_count += 1
if detected:
    anomaly.detection_count += 1
anomaly.frequency = detection_count / scan_count

# Score de priorite adaptatif
def get_priority_score(self) -> float:
    impact = criticality.value * 25  # CRITIQUE=100, ELEVE=75, etc.
    freq_boost = frequency * 100 if scan_count >= 3 else impact
    return freq_boost * (impact / 100)
```

**Resultat** : Les anomalies les plus souvent detectees sont scannees **en premier** lors des prochains scans.

---

### 3.3 Classe BetaCalculator

```python
class BetaCalculator:
    CONFIDENCE_MAP = {
        'HIGH': 100,    # Equivalent a 100 observations
        'MEDIUM': 50,   # Equivalent a 50 observations
        'LOW': 20       # Equivalent a 20 observations
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

| Parametre | Type | Description |
|-----------|------|-------------|
| `error_rate` | `float` | Taux d'erreur observe (0-1) |
| `confidence_level` | `str` | 'HIGH', 'MEDIUM', 'LOW' |
| `n_obs_equivalent` | `int` | Override du nombre d'observations |

**Retourne** : `Dict[str, float]`

```python
{
    "alpha": 2.0,           # Parametre alpha de Beta
    "beta": 98.0,           # Parametre beta de Beta
    "E_P": 0.02,            # Esperance E[P]
    "std": 0.014,           # Ecart-type
    "confidence": "HIGH",
    "n_obs_equiv": 100,
    "ci_lower": 0.003,      # Borne inf IC 95%
    "ci_upper": 0.052       # Borne sup IC 95%
}
```

**Formules** :
```
alpha = error_rate * n
beta  = (1 - error_rate) * n
E[P]  = alpha / (alpha + beta)
Var[P]= alpha*beta / ((alpha+beta)^2 * (alpha+beta+1))
IC_95%= [Beta.ppf(0.025), Beta.ppf(0.975)]
```

---

#### `compute_4d_vector(P_DB, P_DP, P_BR, P_UP, ...)`

```python
def compute_4d_vector(
    P_DB: float,
    P_DP: float,
    P_BR: float,
    P_UP: float,
    confidence_DB: str = 'HIGH',
    confidence_DP: str = 'MEDIUM',
    confidence_BR: str = 'MEDIUM',
    confidence_UP: str = 'LOW'
) -> Dict[str, Any]
```

**Retourne** : Vecteur 4D complet avec alpha, beta, std, ci_lower, ci_upper pour chaque dimension.

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

**Mise a jour Bayesienne** :
```
Beta(alpha', beta') = Beta(alpha + failures, beta + successes)
```

---

## 4. Catalogue d'anomalies (YAML)

### 4.1 Description

Le **catalogue d'anomalies** est le coeur du systeme. Il est stocke dans un fichier YAML unique (`backend/rules_catalog.yaml`) qui sert de **source unique de verite**.

| Fichier | Role |
|---------|------|
| `backend/rules_catalog.yaml` | 128 anomalies + 35 rule_types (source de verite) |
| `backend/rules_catalog_loader.py` | Chargeur YAML, API Python, export ODCS, import CSV |
| `backend/anomaly_referential.py` | Couche de compatibilite (lit le YAML, expose `REFERENTIAL`) |

### 4.2 Structure du fichier YAML

```yaml
# backend/rules_catalog.yaml

rule_types:
  null_check:
    category: Completude
    validator: null_check
    odcs:
      type: library
      metric: nullValues
      threshold_operator: mustBeLessThan
      threshold_unit: percent

  range:
    category: Validite
    validator: range
    odcs:
      type: library
      metric: invalidValues
      threshold_operator: mustBeBetween

  # ... 35 rule_types au total

anomalies:
  DB#1:
    dimension: DB
    nom: NULL dans colonnes obligatoires
    criticite: CRITIQUE
    detection: Auto
    default_rule_type: null_check

  DB#2:
    dimension: DB
    nom: Doublons sur cle primaire
    criticite: CRITIQUE
    detection: Auto
    default_rule_type: pk_unique

  # ... 128 anomalies au total
```

### 4.3 Les 35 rule_types

| rule_type | Categorie DAMA | Validateur | Description |
|-----------|---------------|------------|-------------|
| `null_check` | Completude | null_check | Taux de valeurs nulles |
| `pk_unique` | Unicite | pk_unique | Unicite cle primaire |
| `unique` | Unicite | unique | Unicite colonne |
| `exact_duplicates` | Unicite | exact_duplicates | Lignes exactement identiques |
| `enum` | Validite | enum | Valeurs dans un domaine autorise |
| `range` | Validite | range | Valeurs dans un intervalle |
| `email_format` | Validite | email_format | Format email valide |
| `type_mix` | Validite | type_mix | Coherence de type |
| `no_negative` | Validite | no_negative | Pas de valeurs negatives |
| `no_zero` | Validite | no_zero | Pas de valeurs a zero |
| `overflow` | Validite | overflow | Valeurs hors limites systeme |
| `ratio_bounds` | Validite | ratio_bounds | Ratios dans des bornes |
| `null_legitimate` | Completude | null_legitimate | Nulls dans colonnes opt. |
| `column_empty` | Completude | column_empty | Colonne entierement vide |
| `fill_rate` | Completude | fill_rate | Taux de remplissage |
| `length` | Validite | length | Longueur de chaine |
| `freshness` | Fraicheur | freshness | Fraicheur des donnees |
| `whitespace` | Validite | whitespace | Espaces superflus |
| `encoding_issues` | Validite | encoding_issues | Problemes d'encodage |
| `special_chars` | Validite | special_chars | Caracteres speciaux |
| `case_inconsistency` | Coherence | case_inconsistency | Casse inconsistante |
| `fuzzy_duplicates` | Unicite | fuzzy_duplicates | Quasi-doublons (Levenshtein) |
| `synonyms` | Coherence | synonyms | Synonymes non normalises |
| `unit_heterogeneity` | Coherence | unit_heterogeneity | Unites de mesure mixtes |
| `format_consistency` | Coherence | format_consistency | Formats inconsistants |
| `missing_rows` | Completude | missing_rows | Lignes manquantes (gaps) |
| `date_format_ambiguity` | Validite | date_format_ambiguity | Dates ambigues |
| `cartesian_join_risk` | Validite | cartesian_join_risk | Risque de jointure cartesienne |
| `temporal_order` | Coherence | temporal_order | Ordre temporel (multi-col) |
| `conditional_required` | Coherence | conditional_required | Requis conditionnel (multi-col) |
| `derived_calc` | Coherence | derived_calc | Calcul derive (multi-col) |
| `granularity_max` | Coherence | granularity_max | Granularite excessive |
| `granularity_min` | Coherence | granularity_min | Granularite insuffisante |
| `outlier_iqr` | Validite | outlier_iqr | Valeurs aberrantes (IQR) |
| `causal` | Coherence | causal | Incoherences causales |

### 4.4 Repartition des 128 anomalies par dimension

| Dimension | Code | Nombre | Description |
|-----------|------|--------|-------------|
| Database Integrity | DB | 32 | Contraintes structurelles (NULL, PK, types) |
| Data Processing | DP | 32 | Transformations ETL (calculs, jointures, troncatures) |
| Business Rules | BR | 32 | Regles metier (temporelles, bornes, conformite) |
| Usage Appropriateness | UP | 32 | Adequation contextuelle (fraicheur, granularite) |

### 4.5 Classe RulesCatalog (rules_catalog_loader.py)

```python
class RulesCatalog:
    """Charge et expose le catalogue YAML."""

    def __init__(self, yaml_path=None):
        # Charge rules_catalog.yaml
        self.rule_types: Dict[str, dict]   # 35 rule_types
        self.anomalies: Dict[str, dict]    # 128 anomalies

    def get_by_dimension(self, dim: str) -> Dict[str, dict]:
        """Filtre les anomalies par dimension (DB, DP, BR, UP)."""

    def get_by_rule_type(self, rt: str) -> Dict[str, dict]:
        """Filtre les anomalies par rule_type."""

    def build_odcs_entry(self, rule_type, col, params) -> dict:
        """Genere une entree ODCS v3.1.0 pour une regle."""

    def import_from_dataframe(self, df: pd.DataFrame):
        """Importe des anomalies depuis un CSV/DataFrame."""

    def export_full_odcs(self, contracts, dataset_name) -> dict:
        """Exporte tous les contrats au format ODCS v3.1.0."""

# Singleton
catalog = RulesCatalog()
```

### 4.6 Import CSV de nouvelles anomalies

Le systeme permet d'ajouter des anomalies metier sans toucher au code Python :

```csv
id,dimension,nom,criticite,detection,default_rule_type
BR#33,BR,Salaire brut negatif,CRITIQUE,Auto,no_negative
BR#34,BR,Code postal hors France,ELEVE,Auto,range
```

L'import se fait depuis l'onglet Data Contracts via `catalog.import_from_dataframe()`. Si le `default_rule_type` existe deja dans le catalogue, l'anomalie est prise en charge automatiquement.

### 4.7 Export ODCS v3.1.0

Le catalogue supporte l'export au format **Open Data Contract Standard** (Bitol / Linux Foundation) :

```yaml
# Exemple de sortie ODCS
datasetName: mon_dataset
version: 3.1.0
quality:
  - column: salaire_brut
    type: library
    metric: invalidValues
    mustBeBetween:
      min: 0
      max: 999999
    description: "Intervalle attendu [0 - 999999]"
```

---

## 5. Module ahp_elicitor.py

### 5.1 Description
Implemente l'elicitation des ponderations via la methode AHP (Analytic Hierarchy Process).

### 5.2 Classe AHPElicitor

#### Presets de ponderations

```python
PRESET_WEIGHTS = {
    "paie_reglementaire": {
        "w_DB": 0.40,  # Structure critique (calculs legaux)
        "w_DP": 0.30,  # Traitements importants
        "w_BR": 0.30,  # Regles metier strictes
        "w_UP": 0.00   # Utilisabilite non prioritaire
    },
    "reporting_social": {
        "w_DB": 0.25, "w_DP": 0.20, "w_BR": 0.30, "w_UP": 0.25
    },
    "dashboard_operationnel": {
        "w_DB": 0.10, "w_DP": 0.10, "w_BR": 0.20, "w_UP": 0.60
    },
    "audit_conformite": {
        "w_DB": 0.35, "w_DP": 0.35, "w_BR": 0.30, "w_UP": 0.00
    },
    "analytics_decisional": {
        "w_DB": 0.20, "w_DP": 0.25, "w_BR": 0.25, "w_UP": 0.30
    }
}
```

---

#### `get_weights_preset(usage_type)`

```python
def get_weights_preset(usage_type: str) -> Dict[str, float]
```

**Retourne** :

```python
{
    "w_DB": 0.40,
    "w_DP": 0.30,
    "w_BR": 0.30,
    "w_UP": 0.00,
    "rationale": "Paie reglementaire : structure et calculs critiques"
}
```

---

#### `compute_ahp_matrix(comparisons)`

```python
def compute_ahp_matrix(
    comparisons: List[Tuple[str, str, float]]
) -> Dict[str, float]
```

**Format des comparaisons** (echelle de Saaty) :

| Score | Signification |
|-------|---------------|
| 1 | Egale importance |
| 3 | Importance moderee |
| 5 | Importance forte |
| 7 | Importance tres forte |
| 9 | Importance extreme |

**Algorithme** :
1. Construction matrice 4x4 reciproque
2. Calcul vecteur propre principal (np.linalg.eig)
3. Normalisation pour Sigma(w) = 1.0

---

## 6. Module risk_scorer.py

### 6.1 Description
Calcule les scores de risque contextualises par la combinaison [Attribut x Usage].

### 6.2 Classe RiskScorer

#### Seuils de risque

```python
RISK_THRESHOLDS = {
    "CRITIQUE": 0.40,      # >= 40%
    "ELEVE": 0.25,          # 25-40%
    "MOYEN": 0.15,          # 15-25%
    "ACCEPTABLE": 0.10,     # 10-15%
    "TRES_FAIBLE": 0.00     # < 10%
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

**Formule** :
```
R(a, U) = w_DB * P_DB + w_DP * P_DP + w_BR * P_BR + w_UP * P_UP
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
    "records_affected": 317,
    "impact_financier_mensuel": 15850,
    "severite": "CRITIQUE",
    "actions_recommandees": [
        "Audit immediat de la source",
        "Correction du schema en base",
        "Mise en place monitoring"
    ]
}
```

---

## 7. Module lineage_propagator.py

### 7.1 Description
Simule la propagation du risque a travers les transformations de donnees (ETL, enrichissements, etc.).

### 7.2 Classe LineagePropagator

#### `propagate_dimension(P_initial, transformations)`

```python
def propagate_dimension(
    P_initial: float,
    transformations: List[Dict[str, float]]
) -> List[float]
```

**Formule (convolution bayesienne)** :
```
P_new = 1 - (1 - P_current) * (1 - P_add)
```

**Exemple** :
```python
# P_DP initial = 2%
# Apres ETL (+5%) : P_DP = 1 - (1-0.02)(1-0.05) = 6.9%
# Apres Enrichissement (+8%) : P_DP = 1 - (1-0.069)(1-0.08) = 14.3%
```

---

#### `simulate_pipeline_propagation(vector_4d_source, pipeline)`

```python
def simulate_pipeline_propagation(
    vector_4d_source: Dict[str, Any],
    pipeline: List[Dict]
) -> Dict[str, Any]
```

**Retourne** :

```python
{
    "vector_final": {"P_DB": 0.99, "P_DP": 0.285, "P_BR": 0.23, "P_UP": 0.15},
    "degradation": {"delta_DB": 0.00, "delta_DP": +0.265, ...},
    "history": [
        {"stage": "Source", "P_DB": 0.99, "P_DP": 0.02, ...},
        {"stage": "ETL", "P_DB": 0.99, "P_DP": 0.069, ...},
        ...
    ]
}
```

---

## 8. Module comparator.py

### 8.1 Description
Compare l'approche DAMA classique avec l'approche probabiliste contextualisee.

### 8.2 Gains methodologiques quantifies

| Categorie | DAMA | Probabiliste | Gain |
|-----------|------|--------------|------|
| **Incertitude** | Point estimate | Beta(alpha,beta) + IC 95% | Decisions risque-informees |
| **Contextualisation** | Score unique | Scores par usage | Priorisation ROI |
| **Propagation** | Aucune | Convolution bayesienne | Detection impact ETL |
| **Dimensions** | 6 ISO agregees | 4 causales | Diagnostic cause racine |
| **Apprentissage** | Recalcul complet | Mise a jour bayesienne | Convergence progressive |

---

## 9. Module Data Contracts

### 9.1 Description

Module de generation et validation dynamique de contrats de qualite de donnees. Utilise une **architecture evolutive** basee sur le catalogue YAML.

**Fichier** : `frontend/tabs/data_contracts.py` (v4)

### 9.2 Architecture des applicateurs dynamiques

Le coeur du systeme Data Contracts repose sur un **registre d'applicateurs** :

```python
# Registre global
_RULE_APPLICATORS = {}       # rule_type -> applicator (per-column)
_MULTI_COL_APPLICATORS = {}  # rule_type -> applicator (multi-column)

# Decorateur d'enregistrement
def _applicator(rule_type):
    """Enregistre un applicateur pour un rule_type per-column."""
    def decorator(fn):
        _RULE_APPLICATORS[rule_type] = fn
        return fn
    return decorator

def _multi_applicator(rule_type):
    """Enregistre un applicateur multi-colonnes."""
    def decorator(fn):
        _MULTI_COL_APPLICATORS[rule_type] = fn
        return fn
    return decorator
```

**Principe** : Chaque `rule_type` du catalogue YAML a un applicateur Python qui decide SI la regle s'applique a une colonne donnee et avec quels parametres.

### 9.3 Exemple d'applicateur

```python
@_applicator("null_check")
def _apply_null_check(series, col, col_config, df, contract):
    """Genere une regle de controle de nullite."""
    rate = series.isna().mean() * 100
    threshold = round(min(rate + 5, 100), 1) if rate > 0 else 5.0
    return [{"threshold": threshold,
             "description": f"Taux de NULL <= {threshold}%"}]
```

### 9.4 Generation dynamique de contrats

```python
def _auto_generate_contracts(df: pd.DataFrame) -> dict:
    contracts = {}
    col_config = _auto_detect_columns(df)

    # Phase 1 : Regles per-column (itere le catalogue)
    for col in df.columns:
        rules = []
        for anomaly_id, anomaly in _catalog.anomalies.items():
            rule_type = anomaly.get("default_rule_type")
            if not rule_type or rule_type in _MULTI_COL_APPLICATORS:
                continue
            applicator = _RULE_APPLICATORS.get(rule_type)
            if not applicator:
                continue
            results = applicator(series, col, col_config, df, contract)
            if results:
                for params in results:
                    rules.append(_rule(anomaly_id, desc, rule_type, **params))

    # Phase 2 : Regles multi-colonnes
    for anomaly_id, anomaly in _catalog.anomalies.items():
        rule_type = anomaly.get("default_rule_type")
        if rule_type in _MULTI_COL_APPLICATORS:
            applicator = _MULTI_COL_APPLICATORS[rule_type]
            # ... applique sur combinaisons de colonnes
    return contracts
```

**Avantage** : Ajouter une anomalie avec un `rule_type` existant dans le YAML = prise en charge **zero code**.

### 9.5 Validation automatique

La fonction `_check_rule()` valide chaque regle generee contre les donnees reelles :

| rule_type | Validation |
|-----------|-----------|
| `null_check` | Taux de NULL > threshold |
| `range` | Valeurs hors [min, max] |
| `enum` | Valeurs hors du domaine autorise |
| `email_format` | Regex email invalide |
| `freshness` | Derniere date > N jours |
| `outlier_iqr` | Valeurs hors Q1 - 1.5*IQR / Q3 + 1.5*IQR |
| ... | ... (35 validateurs au total) |

### 9.6 Scores DAMA / ISO 8000

Les contrats calculent des scores sur les 6 dimensions DAMA :

| Dimension | Calcul |
|-----------|--------|
| Completude | 1 - (violations null / total) |
| Coherence | 1 - (violations coherence / total) |
| Exactitude | 1 - (violations exactitude / total) |
| Fraicheur | 1 - (violations fraicheur / total) |
| Validite | 1 - (violations validite / total) |
| Unicite | 1 - (violations unicite / total) |

La resolution anomaly_id -> categorie DAMA se fait dynamiquement via :
```python
def _get_dama_category(anomaly_id: str) -> str:
    anomaly = _catalog.anomalies.get(anomaly_id, {})
    rule_type = anomaly.get("default_rule_type", "")
    rt_config = _catalog.rule_types.get(rule_type, {})
    return rt_config.get("category", "")
```

### 9.7 Exports disponibles

| Format | Contenu |
|--------|---------|
| **ODCS v3.1.0 (YAML)** | Contrat au standard Open Data Contract (Bitol / Linux Foundation) |
| **JSON** | Contrats complets avec version et timestamp |
| **Rapport violations** | Resume des violations detectees |

### 9.8 Import CSV d'anomalies metier

L'onglet permet d'importer des anomalies personnalisees via un fichier CSV :

```csv
id,dimension,nom,criticite,detection,default_rule_type
BR#33,BR,Salaire brut negatif,CRITIQUE,Auto,no_negative
```

Les anomalies importees sont immediatement disponibles pour la generation de contrats.

---

## 10. Application principale app.py

### 10.1 Variables de session Streamlit

```python
session_state = {
    "df": None,                    # DataFrame charge
    "results": None,               # Resultats d'analyse
    "analysis_done": False,        # Flag analyse terminee
    "anthropic_api_key": "",       # Cle API Claude
    "ai_explanations": {},         # Cache explications IA
    "ai_tokens_used": 0,           # Compteur tokens
    "custom_weights": {},          # Ponderations personnalisees
    "selected_profile": "gouvernance",  # Profil reporting
    "data_contracts": None,        # Contrats generes
}
```

### 10.2 Onglets de l'application

| Onglet | Description | Utilisation |
|--------|-------------|-------------|
| **Accueil** | Chargement CSV + guide | Point d'entree |
| **Dashboard** | Vue globale, heatmap des risques | Presentation COMEX |
| **Vecteurs** | Detail des 4 dimensions par attribut | Diagnostic technique |
| **Priorites** | Top 5 des urgences a traiter | Plan d'action |
| **Elicitation** | Ajuster les ponderations par usage | Personnalisation metier |
| **Profil de risque** | Profil de risque contextualise | Analyse approfondie |
| **Lineage** | Impact des transformations ETL | Debug pipeline |
| **DAMA** | Comparaison avec approche classique | Justification methode |
| **Reporting** | Rapport personnalise par profil | Communication |
| **Data Contracts** | Contrats de qualite, ODCS export | Gouvernance donnees |
| **Parametres** | Configuration et administration | Admin |
| **Aide** | Guide utilisateur integre | Formation |

### 10.3 Profils de reporting

| Profil | Focus |
|--------|-------|
| CFO | Impact financier, ROI |
| Data Engineer | Details techniques, ETL |
| DRH | Conformite sociale |
| Auditeur | Regles metier, tracabilite |
| Gouvernance | Vue globale, KPIs |
| Manager Ops | Actions immediates |
| Custom | Configurable |

---

## 11. Formules mathematiques

### 11.1 Distribution Beta

```
Parametres :
    alpha = p * n        (succes)
    beta  = (1-p) * n    (echecs)

Esperance :
    E[P] = alpha / (alpha + beta)

Variance :
    Var[P] = alpha*beta / ((alpha+beta)^2 * (alpha+beta+1))

Intervalle de confiance 95% :
    IC = [Beta.ppf(0.025, alpha, beta), Beta.ppf(0.975, alpha, beta)]
```

### 11.2 Score de risque

```
R(a, U) = Sum(w_d * P_d)

R(a, U) = w_DB * P_DB + w_DP * P_DP + w_BR * P_BR + w_UP * P_UP

Contrainte : Sum(w_d) = 1.0
```

### 11.3 Propagation Lineage

```
Convolution bayesienne :
    P_new = 1 - (1 - P_current) * (1 - P_add)

Equivalent a :
    P_d(N) = 1 - Prod(1 - P_d(i))
```

### 11.4 Mise a jour Bayesienne

```
Prior :     Beta(alpha, beta)
Likelihood: Binomiale(k succes, n-k echecs)
Posterior : Beta(alpha + (n-k), beta + k)

Ou k = nombre de nouvelles erreurs observees
```

---

## 12. Guide d'extension

### 12.1 Ajouter une anomalie (zero code)

Si le `rule_type` existe deja, il suffit d'ajouter une entree dans `rules_catalog.yaml` :

```yaml
# backend/rules_catalog.yaml
anomalies:
  BR#33:
    dimension: BR
    nom: Salaire brut negatif
    criticite: CRITIQUE
    detection: Auto
    default_rule_type: no_negative
```

La generation de contrats detectera automatiquement cette anomalie.

### 12.2 Ajouter un nouveau rule_type

1. Ajouter le type dans la section `rule_types:` du YAML :
```yaml
rule_types:
  mon_nouveau_type:
    category: Validite
    validator: mon_nouveau_type
    odcs:
      type: custom
      metric: invalidValues
```

2. Ajouter un applicateur dans `frontend/tabs/data_contracts.py` :
```python
@_applicator("mon_nouveau_type")
def _apply_mon_nouveau_type(series, col, col_config, df, contract):
    # Decide si la regle s'applique + parametres
    if condition_applicable:
        return [{"description": "Ma description", "param": valeur}]
    return None
```

3. Ajouter un validateur dans `_check_rule()` (meme fichier) :
```python
elif rtype == "mon_nouveau_type":
    # Logique de validation
    violations = ...
    return {"status": "PASS" if not violations else "FAIL", ...}
```

### 12.3 Ajouter une nouvelle dimension

1. **beta_calculator.py** : Ajouter `P_XX` dans `compute_4d_vector()`
2. **ahp_elicitor.py** : Ajouter `w_XX` dans les presets
3. **risk_scorer.py** : Inclure dans la formule de scoring
4. **app.py** : Mettre a jour les visualisations

### 12.4 Ajouter un nouveau type d'usage

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

### 12.5 Personnaliser le pipeline de lineage

```python
custom_pipeline = [
    {"nom": "Source DB", "P_DB_add": 0.00, "P_DP_add": 0.01, "P_BR_add": 0.00, "P_UP_add": 0.00},
    {"nom": "API Gateway", "P_DB_add": 0.00, "P_DP_add": 0.03, "P_BR_add": 0.00, "P_UP_add": 0.02},
    {"nom": "Data Lake", "P_DB_add": 0.00, "P_DP_add": 0.02, "P_BR_add": 0.01, "P_UP_add": 0.01},
]
result = simulate_lineage(vector_4d, weights, pipeline_config=custom_pipeline)
```

### 12.6 Importer des anomalies par CSV

Preparer un fichier CSV avec les colonnes requises :

```csv
id,dimension,nom,criticite,detection,default_rule_type
BR#33,BR,Mon anomalie metier,CRITIQUE,Auto,range
```

Puis l'importer depuis l'onglet Data Contracts. Les `rule_type` existants sont pris en charge automatiquement.

---

## Changelog

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0 | Fev 2025 | Version initiale |
| 1.1 | Fev 2025 | Ajout catalogue anomalies (60 anomalies), systeme apprentissage |
| 1.2 | Fev 2025 | Reporting multi-attributs, guide utilisateur, correction unicite DAMA |
| 2.0 | Fev 2026 | Refactoring frontend/tabs, Data Contracts v2, onglet settings |
| 3.0 | Mars 2026 | **Refonte catalogue YAML** (128 anomalies, 35 rule_types), generation dynamique de contrats (applicateurs), export ODCS v3.1.0, import CSV, scores DAMA dynamiques |

---

*Documentation technique — Augmented DQ Framework v3.0*
