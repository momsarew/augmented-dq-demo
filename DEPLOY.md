# Guide de Déploiement - Streamlit Cloud

## Option 1: Streamlit Cloud (Recommandé - Gratuit)

### Étape 1: Créer le repo GitHub

```bash
cd /Users/tempnouvmac/Desktop/augmented-dq-demo

# Initialiser git
git init

# Ajouter les fichiers
git add app.py backend/ streamlit_gray_css.py streamlit_anomaly_detection.py contextual_reporting.py reporting_exports.py requirements.txt README.md .streamlit/ .gitignore DOCUMENTATION_TECHNIQUE.md

# Premier commit
git commit -m "Initial commit - Framework Probabiliste DQ"
```

### Étape 2: Pusher sur GitHub

```bash
# Créer un nouveau repo sur GitHub.com (vide, sans README)
# Puis:
git remote add origin https://github.com/VOTRE_USERNAME/augmented-dq-demo.git
git branch -M main
git push -u origin main
```

### Étape 3: Déployer sur Streamlit Cloud

1. Aller sur https://share.streamlit.io/
2. Se connecter avec GitHub
3. Cliquer "New app"
4. Sélectionner le repo `augmented-dq-demo`
5. Sélectionner `main` comme branch
6. Sélectionner `app.py` comme fichier principal
7. Cliquer "Deploy!"

**L'URL sera:** `https://augmented-dq-demo.streamlit.app`

---

## Option 2: Render (Gratuit aussi)

1. Aller sur https://render.com
2. Créer un "Web Service"
3. Connecter GitHub
4. Sélectionner le repo
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `streamlit run app.py --server.port $PORT`

---

## Option 3: Déploiement local temporaire avec ngrok

```bash
# Installer ngrok (brew install ngrok)
# Lancer l'app
streamlit run app.py

# Dans un autre terminal:
ngrok http 8501
```

Vous obtiendrez une URL publique temporaire.

---

## Configuration des Secrets (Clé API Claude)

### Pour Streamlit Cloud:
1. Après déploiement, aller dans "Settings" > "Secrets"
2. Ajouter:
```toml
[api]
anthropic_key = "sk-ant-..."
```

Ou laisser les utilisateurs entrer leur propre clé dans l'onglet "Paramètres".

---

## Fichiers nécessaires pour le déploiement

✅ `app.py` - Application principale
✅ `requirements.txt` - Dépendances
✅ `.streamlit/config.toml` - Configuration thème
✅ `backend/` - Moteur de calcul
✅ `streamlit_gray_css.py` - Styles CSS
✅ `streamlit_anomaly_detection.py` - Détection anomalies

---

## Tests avant déploiement

```bash
# Vérifier que tout fonctionne
source .venv/bin/activate
streamlit run app.py
```

Ouvrir http://localhost:8501 et vérifier:
- [ ] L'application charge
- [ ] Upload de fichier Excel fonctionne
- [ ] Les onglets sont accessibles
- [ ] Les graphiques s'affichent
