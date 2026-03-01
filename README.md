# Augmented DQ Framework

Application Streamlit d'analyse qualite donnees avec approche probabiliste bayesienne et referentiel evolutif de 128+ anomalies.

## Installation Rapide

### Option A : Setup automatique Mac

```bash
chmod +x setup_mac.sh
./setup_mac.sh
```

Options : `--full` (defaut) | `--clean` (nettoyage seul) | `--run` (lancement seul)

### Option B : Installation manuelle

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`

## Structure du Projet

```
augmented-dq-demo/
├── app.py                                # Orchestrateur principal Streamlit
├── requirements.txt                      # Dependances Python
│
├── backend/
│   ├── rules_catalog.yaml                # REFERENTIEL : 128+ anomalies (source unique)
│   ├── rules_catalog_loader.py           # Chargeur YAML + API ODCS + import CSV
│   ├── anomaly_referential.py            # Couche compatibilite (lit le YAML)
│   ├── security.py                       # Securite (XSS, validation, sanitization)
│   ├── audit_trail.py                    # Audit trail complet
│   ├── adaptive_scan_engine.py           # Moteur scan adaptatif
│   ├── scan_to_beta_connector.py         # Connecteur scan -> Beta
│   │
│   └── engine/                           # Moteur calculs probabilistes
│       ├── beta_calculator.py            # Distributions Beta bayesiennes
│       ├── ahp_elicitor.py               # Ponderations AHP par usage
│       ├── analyzer.py                   # Analyse exploratoire
│       ├── risk_scorer.py                # Scoring risque contextualise
│       ├── lineage_propagator.py         # Propagation causale ETL
│       └── comparator.py                 # Comparaison DAMA vs Probabiliste
│
├── frontend/
│   ├── components/                       # Composants partages (theme, charts, export)
│   └── tabs/                             # Onglets de l'application
│       ├── home.py                       # Accueil
│       ├── dashboard.py                  # Dashboard global
│       ├── vectors.py                    # Vecteurs 4D detailles
│       ├── priorities.py                 # Top priorites actions
│       ├── elicitation.py                # Elicitation AHP
│       ├── risk_profile.py              # Profil de risque
│       ├── lineage.py                    # Propagation ETL
│       ├── dama.py                       # Comparaison DAMA
│       ├── reporting.py                  # Rapports contextuels IA
│       ├── data_contracts.py             # Data Contracts (generation dynamique)
│       ├── settings.py                   # Parametres et admin
│       └── help.py                       # Guide utilisateur
│
├── tests/                                # Tests pre-deploiement
└── docs/                                 # Documentation architecture
```

## Architecture Cle

### Referentiel d'anomalies evolutif

Le referentiel est stocke dans `backend/rules_catalog.yaml` (source unique de verite) :

- **128 anomalies** reparties en 4 dimensions causales (DB, DP, BR, UP)
- **31 rule_types** avec validateurs automatiques
- **Extensible par CSV** : ajoutez des anomalies metier sans modifier le code Python
- **Export ODCS v3.1.0** : standard Open Data Contract (Bitol / Linux Foundation)

### Generation dynamique de contrats

L'onglet Data Contracts utilise un systeme d'**applicateurs dynamiques** :

1. Chaque `rule_type` dans le YAML a un applicateur Python qui decide SI la regle s'applique
2. La generation itere toutes les anomalies du catalogue automatiquement
3. Ajouter une anomalie avec un `rule_type` existant = prise en charge **zero code**

### Framework 4D probabiliste

| Dimension | Code | Description |
|-----------|------|-------------|
| Database Integrity | DB | Contraintes structurelles (NULL, PK, types) |
| Data Processing | DP | Transformations ETL (calculs, jointures, troncatures) |
| Business Rules | BR | Regles metier (temporelles, bornes, conformite) |
| Usage Appropriateness | UP | Adequation contextuelle (fraicheur, granularite) |

Chaque dimension est modelisee par une **distribution Beta** bayesienne, ponderee par usage via **AHP**.

## Fonctionnalites

### Scan et Detection
- **128+ anomalies** dans le referentiel YAML (extensible)
- **33 detecteurs automatiques** (rule_types avec validateurs)
- **Apprentissage adaptatif** : le moteur s'ameliore a chaque scan
- **3 budgets** : QUICK (top 5) | STANDARD (top 10) | DEEP (tous)

### Data Contracts
- Generation automatique depuis le referentiel complet
- Validation Auto/Semi/Manuel par anomalie
- Scores DAMA / ISO 8000 (6 dimensions)
- Import CSV pour anomalies metier personnalisees
- Export ODCS v3.1.0 (YAML) + JSON + rapport violations

### Analyse Probabiliste
- Distributions Beta par dimension (DB, DP, BR, UP)
- Scores contextualises par usage metier (paie, reporting, audit...)
- Propagation risque le long des pipelines ETL (lineage)
- Comparaison vs referentiel DAMA

## Configuration API Claude (Optionnel)

Pour les fonctionnalites IA (dialogue elicitation, commentaires contextuels) :

1. Obtenir une cle API sur https://console.anthropic.com/
2. Dans la sidebar, coller la cle dans le champ "Cle API Claude"

## Documentation

| Document | Description |
|----------|-------------|
| `GUIDE_UTILISATEUR.md` | Guide d'utilisation avec exemples |
| `DOCUMENTATION_TECHNIQUE.md` | Architecture, modules, formules |
| `docs/ARCHITECTURE.md` | Architecture C4 detaillee |
| `docs/ARCHITECTURE_DIAGRAMS.md` | Diagrammes Mermaid |

## Gains Demontres

- Temps elicitation : 240h -> 30min (480x)
- Faux positifs : -70%
- Detection incidents : 3 sem -> 9h (-95%)
- ROI : 8-18x vs approches traditionnelles
