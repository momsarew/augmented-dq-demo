# 🚀 GUIDE DÉPLOIEMENT STREAMLIT CLOUD

## ✅ ÉTAPE 1 : CRÉER REPOSITORY GITHUB (5 min)

### 1.1 Connexion GitHub

1. Va sur https://github.com
2. Connecte-toi (ou crée compte si besoin)

### 1.2 Créer nouveau repository

1. Clique sur **"+" en haut à droite** → "New repository"
2. Remplis le formulaire :

```
Repository name: framework-dq-demo
Description: Framework Probabiliste Data Quality - Démo Interactive
☑️ Public (pour Streamlit Cloud gratuit)
☑️ Add a README file
☐ Add .gitignore (on a déjà le nôtre)
☐ Choose a license
```

3. Clique **"Create repository"**

### 1.3 Uploader les fichiers

**Méthode A : Via interface web (PLUS SIMPLE)**

1. Sur la page de ton nouveau repo, clique **"Add file" → "Upload files"**

2. Drag & drop TOUS les fichiers du dossier `streamlit_cloud_deploy/` :
   - ✅ app.py
   - ✅ requirements.txt
   - ✅ README.md
   - ✅ .gitignore
   - ✅ secrets.toml.template
   - ✅ Dossier backend/ (avec tous ses fichiers)

3. En bas, écris message commit :
   ```
   Initial commit - Framework DQ V9
   ```

4. Clique **"Commit changes"**

**Méthode B : Via terminal (si tu es à l'aise)**

```bash
cd ~/Desktop
cp -r /chemin/vers/streamlit_cloud_deploy framework-dq-demo
cd framework-dq-demo

git init
git add .
git commit -m "Initial commit - Framework DQ V9"
git branch -M main
git remote add origin https://github.com/TON_USERNAME/framework-dq-demo.git
git push -u origin main
```

---

## ✅ ÉTAPE 2 : DÉPLOYER SUR STREAMLIT CLOUD (5 min)

### 2.1 Connexion Streamlit Cloud

1. Va sur https://share.streamlit.io/
2. Clique **"Sign in"**
3. Sélectionne **"Continue with GitHub"**
4. Autorise Streamlit à accéder à ton GitHub

### 2.2 Créer nouvelle app

1. Clique **"New app"** (bouton en haut à droite)

2. Remplis le formulaire :

```
Repository: TON_USERNAME/framework-dq-demo
Branch: main
Main file path: app.py
App URL (optional): framework-dq-demo (ou choisis ton nom)
```

3. **NE CLIQUE PAS "Deploy" TOUT DE SUITE !**

### 2.3 Configurer les secrets (IMPORTANT!)

1. Clique sur **"Advanced settings"**

2. Dans la section **"Secrets"**, colle ceci :

```toml
ANTHROPIC_API_KEY = "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"
```

3. Clique **"Save"**

### 2.4 Lancer le déploiement

1. Clique **"Deploy!"**

2. Attends 2-5 minutes pendant que Streamlit :
   - ✅ Clone ton repo
   - ✅ Installe les dépendances
   - ✅ Lance l'application

3. Tu verras des logs défiler en temps réel

### 2.5 Succès !

Quand tu vois :
```
🎉 Your app is live!
URL: https://framework-dq-demo.streamlit.app
```

**C'est bon ! L'app est en ligne ! 🚀**

---

## ✅ ÉTAPE 3 : TESTER L'APP DÉPLOYÉE (2 min)

### 3.1 Accéder à l'URL

1. Ouvre https://TON-APP.streamlit.app
2. L'app devrait charger en quelques secondes

### 3.2 Test rapide

1. ✅ Charge dataset démo (sidebar)
2. ✅ Lance analyse (bouton 🚀)
3. ✅ Va dans onglet "💬 Élicitation IA"
4. ✅ Dialogue avec Claude fonctionne
5. ✅ Va dans "🔄 Lineage"
6. ✅ Vérifie que "✏️ Personnalisé" apparaît (6ème option)

### 3.3 Partager l'URL

**Ton URL publique** :
```
https://framework-dq-demo.streamlit.app
```

Tu peux la partager avec :
- ✅ Clients (démos)
- ✅ Collègues
- ✅ Prospects
- ✅ N'importe qui sur Internet

**Sécurité** :
- ✅ Clé API cachée (dans secrets Streamlit)
- ✅ Pas visible dans le code GitHub
- ✅ Seul toi peux modifier via dashboard Streamlit

---

## ✅ ÉTAPE 4 : GÉRER L'APP (BONUS)

### 4.1 Voir les logs

1. Va sur https://share.streamlit.io/
2. Clique sur ton app
3. Onglet **"Logs"** → Voir activité en temps réel

### 4.2 Modifier secrets

1. Sur dashboard Streamlit Cloud
2. Clique sur ton app → **"Settings"** → **"Secrets"**
3. Modifie et clique **"Save"**
4. App redémarre automatiquement

### 4.3 Mettre à jour l'app

**Méthode simple** :

1. Va sur GitHub : https://github.com/TON_USERNAME/framework-dq-demo
2. Clique sur le fichier à modifier (ex: app.py)
3. Clique sur icône crayon ✏️ "Edit this file"
4. Fais tes modifications
5. Scroll en bas, clique **"Commit changes"**
6. Streamlit Cloud redéploie automatiquement en 1-2 min !

### 4.4 Redémarrer l'app

Si besoin de forcer redémarrage :

1. Dashboard Streamlit Cloud
2. Clique sur ton app
3. Menu **"⋮"** → **"Reboot app"**

---

## 🎯 RÉCAPITULATIF FINAL

### Ce que tu as maintenant :

✅ **App en ligne 24/7** sur Streamlit Cloud  
✅ **URL publique** partageable avec clients  
✅ **Clé API sécurisée** (pas dans code GitHub)  
✅ **Mises à jour faciles** via GitHub  
✅ **Gratuit** (limite : 1GB RAM, OK pour ta démo)  

### URLs importantes :

- 📱 **Ton app** : https://TON-APP.streamlit.app
- ⚙️ **Dashboard** : https://share.streamlit.io
- 💻 **Code source** : https://github.com/TON_USERNAME/framework-dq-demo

---

## 🐛 TROUBLESHOOTING

### Erreur "Module not found"

**Cause** : Dépendance manquante dans requirements.txt

**Solution** :
1. Édite `requirements.txt` sur GitHub
2. Ajoute la ligne manquante
3. Commit → Redéploiement auto

### Erreur "ANTHROPIC_API_KEY not found"

**Cause** : Secret mal configuré

**Solution** :
1. Dashboard Streamlit → Settings → Secrets
2. Vérifie le format :
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
3. Pas d'espace avant/après =
4. Guillemets nécessaires
5. Save → Reboot app

### App lente ou crash

**Cause** : Dépassement limite RAM (1GB)

**Solution** :
1. Réduis taille dataset démo
2. Optimise imports
3. Ou upgrade plan Streamlit ($20/mois pour 4GB)

---

## 📞 BESOIN D'AIDE ?

**Support Streamlit** : https://discuss.streamlit.io/

**Documentation** : https://docs.streamlit.io/streamlit-community-cloud

---

**Bonne chance pour le déploiement ! 🚀**

**Une fois terminé, tu auras une URL que tu pourras mettre dans ta signature email, LinkedIn, CV... 😎**
