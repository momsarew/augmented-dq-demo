# Framework Probabiliste DQ - Backend API

API REST FastAPI pour calculs qualité données probabilistes bayésiens.

## 🎯 Vue d'ensemble

Ce backend implémente le moteur de calcul du Framework Probabiliste :
- **Analyse exploratoire** : Détection automatique erreurs type/business
- **Calcul Beta bayésien** : Distributions Beta(α,β) pour 4 dimensions (DB-DP-BR-UP)
- **Élicitation AHP** : Pondérations contextualisées par usage métier
- **Scores risque** : R(a,U) = Σ w_d × P_d
- **Propagation lineage** : Convolution bayésienne le long pipelines
- **Comparaison DAMA** : Gains méthodologiques quantifiés

---

## 📁 Structure

```
backend/
├── engine/                 # Moteur de calcul
│   ├── analyzer.py         # Analyse exploratoire
│   ├── beta_calculator.py  # Calculs Beta
│   ├── ahp_elicitor.py     # Élicitation pondérations
│   ├── risk_scorer.py      # Scores risque
│   ├── lineage_propagator.py # Propagation lineage
│   └── comparator.py       # Comparaison DAMA
│
├── api/
│   └── main.py             # API FastAPI
│
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier
```

---

## 🚀 Installation

### 1. Prérequis
```bash
Python 3.9+
pip
```

### 2. Installation dépendances
```bash
cd backend
pip install -r requirements.txt
```

**Note:** Pour éviter conflits système, utiliser virtualenv :
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

---

## 🔧 Démarrage

### Développement local
```bash
cd backend/api
python3 main.py
```

Ou avec uvicorn direct :
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur :
- **API** : http://localhost:8000
- **Documentation interactive** : http://localhost:8000/docs
- **OpenAPI schema** : http://localhost:8000/openapi.json

---

## 📡 Endpoints principaux

### 1. Health Check
```bash
GET /health
```
Retourne statut API + version moteur.

### 2. Analyse complète
```bash
POST /api/analyze

Body:
{
  "data": {
    "rows": [...],
    "columns": [...]
  },
  "columns_to_analyze": ["Anciennete", "LEVEL_ACN"],
  "usages": [
    {"nom": "Paie", "type": "paie_reglementaire", "criticite": "HIGH"}
  ]
}

Returns:
{
  "status": "success",
  "stats": {...},
  "vecteurs_4d": {...},
  "weights": {...},
  "scores": {...},
  "top_priorities": [...],
  "lineage": {...},
  "comparaison_dama": {...}
}
```

### 3. Upload fichier
```bash
POST /api/upload
Content-Type: multipart/form-data

file: dataset.csv (ou .xlsx)

Returns:
{
  "status": "success",
  "filename": "dataset.csv",
  "preview": {...},
  "suggested_columns": [...]
}
```

### 4. Dataset exemple
```bash
GET /api/examples/dataset

Returns:
{
  "data": {...},
  "suggested_config": {...}
}
```

---

## 🧪 Tests

### Test modules individuels
```bash
# Analyzer
python3 -m backend.engine.analyzer

# Beta Calculator
python3 -m backend.engine.beta_calculator

# Risk Scorer
python3 -m backend.engine.risk_scorer

# etc.
```

### Test API avec curl
```bash
# Health check
curl http://localhost:8000/health

# Analyse exemple
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### Test avec Postman
Importer collection depuis : http://localhost:8000/openapi.json

---

## 🔌 Intégration Frontend

### Exemple fetch JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    data: {
      rows: dataRows,
      columns: dataColumns
    },
    columns_to_analyze: ['Anciennete', 'LEVEL_ACN'],
    usages: [
      {nom: 'Paie', type: 'paie_reglementaire', criticite: 'HIGH'}
    ]
  })
});

const results = await response.json();
console.log('Scores risque:', results.scores);
```

### Exemple React Hook
```typescript
// useEngine.ts
import { useState } from 'react';

export const useEngine = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const analyze = async (data, columns, usages) => {
    setLoading(true);
    
    const response = await fetch('http://localhost:8000/api/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        data,
        columns_to_analyze: columns,
        usages
      })
    });
    
    const results = await response.json();
    setResults(results);
    setLoading(false);
    
    return results;
  };

  return { analyze, loading, results };
};
```

---

## 📊 Exemple réponse API

```json
{
  "status": "success",
  "vecteurs_4d": {
    "Anciennete": {
      "P_DB": 0.99,
      "alpha_DB": 99,
      "beta_DB": 1,
      "P_DP": 0.02,
      "alpha_DP": 2,
      "beta_DP": 98,
      "P_BR": 0.20,
      "alpha_BR": 20,
      "beta_BR": 80,
      "P_UP": 0.10,
      "alpha_UP": 5,
      "beta_UP": 45
    }
  },
  "scores": {
    "Anciennete_Paie": 0.463,
    "Anciennete_CSE": 0.337
  },
  "top_priorities": [
    {
      "attribut": "Anciennete",
      "usage": "Paie",
      "score": 0.463,
      "severite": "CRITIQUE",
      "records_affected": 196,
      "impact_mensuel": 45080,
      "actions": [
        "URGENT: Corriger Anciennete immédiatement"
      ]
    }
  ]
}
```

---

## 🚢 Déploiement

### Railway.app (Recommandé)
```bash
# 1. Créer compte Railway
# 2. Connecter repo GitHub
# 3. Railway détecte Python automatiquement
# 4. Variables env (si besoin):
#    - PYTHON_VERSION=3.11
# 5. Deploy !
```

### Render.com
```bash
# 1. Créer Web Service
# 2. Build: pip install -r requirements.txt
# 3. Start: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Docker (optionnel)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📚 Documentation modules

### analyzer.py
Analyse exploratoire datasets avec détection automatique :
- Erreurs parsing (virgules, formats mixtes)
- Violations métier (dates futures, négatifs)
- Stats descriptives (nulls, uniques, types)

### beta_calculator.py
Calculs distributions Beta bayésiennes :
- `compute_beta_params(error_rate, confidence)` → Beta(α,β)
- `compute_4d_vector(P_DB, P_DP, P_BR, P_UP)` → vecteur complet
- Intervalles confiance 95%

### ahp_elicitor.py
Élicitation pondérations AHP :
- Presets par type usage (Paie, CSE, Dashboard, ...)
- Calcul matrice comparaisons pairées
- Validation cohérence (somme=1)

### risk_scorer.py
Calcul scores risque contextualisés :
- `compute_risk_score(vector, weights)` → R(a,U)
- Classification (CRITIQUE, ÉLEVÉ, MOYEN, ...)
- Impact business estimé (€, enregistrements affectés)

### lineage_propagator.py
Propagation risque lineage :
- Convolution bayésienne P_d(N) ≈ 1 - ∏(1 - P_d(i))
- Simulation pipelines multi-étapes
- Calcul dégradation (delta risque)

### comparator.py
Comparaison DAMA vs Probabiliste :
- Scores DAMA ISO 8000 traditionnels
- Détection problèmes masqués
- Gains méthodologiques quantifiés

---

## 🤝 Contribution

1. Fork le repo
2. Créer branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir Pull Request

---

## 📝 License

MIT License - voir LICENSE file

---

## 👤 Contact

Thierno - Senior Manager Big 4
Email: thierno@big4.com
Project: Framework Probabiliste DQ

---

## 🙏 Remerciements

- SciPy pour distributions Beta
- FastAPI pour API moderne
- Pandas pour manipulation données
