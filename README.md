# 🎯 Framework Probabiliste DQ

Application Streamlit pour analyse qualité données avec approche probabiliste bayésienne.

## 🚀 Installation Rapide

### 1️⃣ Prérequis
```bash
Python 3.9+
pip
```

### 2️⃣ Installation
```bash
# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# OU
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt
```

### 3️⃣ Lancement
```bash
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur sur `http://localhost:8501`

## 📁 Structure Projet

```
augmented-dq-demo/
├── app.py                              # Application principale
├── streamlit_gray_css.py               # CSS (fond gris mat)
├── streamlit_anomaly_detection.py      # Module scan anomalies
├── requirements.txt                    # Dépendances
│
├── backend/
│   ├── adaptive_scan_engine.py         # Moteur scan adaptatif
│   ├── core_anomaly_catalog.py         # 15 anomalies détectées
│   ├── extended_anomaly_catalog.py     # 60 anomalies cataloguées
│   ├── scan_to_beta_connector.py       # Connecteur scan→Beta
│   │
│   └── engine/                         # Moteur calculs probabilistes
│       ├── __init__.py
│       ├── beta_calculator.py          # Distributions Beta
│       ├── ahp_elicitor.py             # Pondérations AHP
│       ├── analyzer.py                 # Stats exploratoires
│       ├── risk_scorer.py              # Calcul scores risque
│       ├── lineage_propagator.py       # Propagation causale
│       └── comparator.py               # Comparaison DAMA
```

## ✅ Fonctionnalités

### 🔍 Scan Anomalies
- **15 détecteurs réels** opérationnels
- **60 anomalies** cataloguées (15 implémentées)
- **Apprentissage adaptatif** : moteur s'améliore à chaque scan
- **3 budgets** : QUICK (top 5) | STANDARD (top 10) | DEEP (tous)

### 📊 Dashboard Qualité
- Vecteurs 4D (DB-DP-BR-UP)
- Heatmap scores risque
- Top priorités actions
- Export Excel multi-onglets

### 🎯 Analyse Probabiliste
- Distributions Beta par dimension
- Scores contextualisés par usage
- Propagation risque (lineage)
- Comparaison vs DAMA

## 🔑 Configuration API Claude (Optionnel)

Pour utiliser les fonctionnalités IA (dialogue élicitation, commentaires) :

1. Obtenir clé API sur https://console.anthropic.com/
2. Dans la sidebar, coller la clé dans le champ "Clé API Claude"

## 📚 Documentation

- **Guide déploiement** : Voir `GUIDE_DEPLOIEMENT.md`
- **Architecture** : Voir `backend/README.md`

## 🎓 Méthodologie

**Framework 4D** :
- **[DB]** Database : Contraintes structurelles
- **[DP]** Data Processing : Transformations ETL
- **[BR]** Business Rules : Règles métier
- **[UP]** Usage-fit : Adéquation contextuelle

**Approche Bayésienne** :
- Distributions Beta modélisant l'incertitude
- Pondérations AHP par usage métier
- Propagation causale le long des pipelines

## 💡 Gains Démontrés

- ⏱️ **Temps élicitation** : 240h → 30min (480×)
- 🎯 **Faux positifs** : -70%
- 🔔 **Détection incidents** : 3 sem → 9h (-95%)
- 💰 **ROI** : 8-18× vs approches traditionnelles

## 📞 Contact

Thierno DIAW - Senior Manager Data Governance
