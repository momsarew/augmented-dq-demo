# Guide Utilisateur - Augmented DQ Framework

> Guide pratique pour analyser la qualite de vos donnees avec l'approche probabiliste bayesienne.

---

## 1. Demarrage rapide

### 1.1 Lancer l'application

```bash
# Option A : Setup automatique Mac
chmod +x setup_mac.sh
./setup_mac.sh

# Option B : Installation manuelle
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`.

### 1.2 Charger vos donnees

1. Ouvrez l'application dans votre navigateur
2. Utilisez le **chargeur de fichier** dans la barre laterale pour importer un fichier CSV
3. Selectionnez les **colonnes** a analyser
4. Choisissez un **type d'usage** (paie, reporting, audit...) ou utilisez les ponderations par defaut
5. Cliquez sur **Lancer l'analyse**

### 1.3 Formats supportes

| Format | Extension | Encodage |
|--------|-----------|----------|
| CSV | `.csv` | UTF-8, Latin-1 (auto-detecte) |

---

## 2. Comprendre les resultats

### 2.1 Le framework 4D

L'application analyse vos donnees selon 4 dimensions causales :

| Dimension | Code | Ce qu'elle mesure | Exemples |
|-----------|------|-------------------|----------|
| **Database Integrity** | DB | Problemes de structure des donnees | NULL dans colonnes obligatoires, doublons sur cle primaire, types invalides |
| **Data Processing** | DP | Erreurs dans les transformations | Calculs derives incorrects, divisions par zero, troncatures |
| **Business Rules** | BR | Violations des regles metier | Bornes metier depassees, incoherences temporelles, contraintes conditionnelles |
| **Usage Appropriateness** | UP | Adequation au contexte d'utilisation | Donnees obsoletes, granularite inadaptee, qualite insuffisante |

Pour chaque dimension, l'application calcule une **probabilite d'erreur** (P_DB, P_DP, P_BR, P_UP) modelisee par une distribution Beta bayesienne.

### 2.2 Code couleur des risques

| Couleur | Niveau | Score de risque | Action recommandee |
|---------|--------|----------------|-------------------|
| Rouge | CRITIQUE | >= 40% | Action immediate requise |
| Orange | ELEVE | 25-40% | Planifier une correction |
| Jaune | MOYEN | 15-25% | Surveiller et planifier |
| Vert | ACCEPTABLE | < 15% | Monitorer |

### 2.3 Ponderations par usage

Les ponderations determinent l'importance relative de chaque dimension selon votre contexte :

| Usage | DB | DP | BR | UP | Raison |
|-------|-----|-----|-----|-----|--------|
| Paie reglementaire | 40% | 30% | 30% | 0% | Precision calculs critique |
| Reporting social | 25% | 20% | 30% | 25% | Equilibre toutes dimensions |
| Dashboard operationnel | 10% | 10% | 20% | 60% | Utilisabilite prime |
| Audit conformite | 35% | 35% | 30% | 0% | Structure et traitements |
| Analytics decisionnel | 20% | 25% | 25% | 30% | Adequation usage |

---

## 3. Les onglets de l'application

### 3.1 Accueil

Chargement du fichier CSV et presentation de l'outil. C'est ici que vous :
- Importez vos donnees
- Selectionnez les colonnes a analyser
- Lancez l'analyse

### 3.2 Dashboard

Vue d'ensemble des resultats :
- **Heatmap** [Attribut x Usage] : visualisation matricielle des risques
- **Scores globaux** par colonne
- **Nombre d'anomalies** detectees

**Cas d'usage** : Presentation au COMEX, vue synthetique pour la gouvernance.

### 3.3 Vecteurs 4D

Detail de chaque dimension pour chaque attribut :
- Graphiques en barres des probabilites P_DB, P_DP, P_BR, P_UP
- Intervalles de confiance a 95%
- Parametres des distributions Beta (alpha, beta)

**Cas d'usage** : Diagnostic technique, comprendre la cause racine d'un risque.

### 3.4 Priorites

Top 5 des couples [Attribut x Usage] les plus a risque :
- Classement par score de risque decroissant
- Impact financier estime
- Actions recommandees

**Cas d'usage** : Plan d'action correctif, priorisation des interventions.

### 3.5 Elicitation AHP

Personnalisation des ponderations par usage :
- Choix d'un **preset** (paie, reporting, audit...) ou saisie manuelle
- **Comparaisons par paires** (methode AHP de Saaty)
- Dialogue guide par IA (si cle API Claude configuree)

**Cas d'usage** : Adapter l'analyse a un contexte metier specifique.

### 3.6 Profil de risque

Profil de risque contextualise :
- Distribution des risques par dimension
- Sensibilite aux ponderations
- Recommandations contextualisees

### 3.7 Lineage (Propagation ETL)

Simulation de l'impact des transformations sur la qualite :
- Pipeline ETL configurable (extraction, enrichissement, agregation)
- Degradation progressive des probabilites
- Visualisation de la propagation

**Exemple** : Un P_DP de 2% en source peut devenir 28% apres 4 etapes ETL.

### 3.8 Comparaison DAMA

Comparaison entre l'approche DAMA classique et l'approche probabiliste :
- Scores DAMA (6 dimensions ISO 8000) vs scores 4D
- Mise en evidence des problemes masques par DAMA
- Avantages quantifies de l'approche probabiliste

### 3.9 Reporting

Generation de rapports contextuels par profil :
- Selection d'un ou plusieurs attributs
- Choix du profil (CFO, Data Engineer, DRH, Auditeur, Gouvernance, Manager Ops)
- Rapport enrichi par IA (si cle API Claude configuree)

### 3.10 Data Contracts

Generation et validation de contrats de qualite de donnees :

1. **Generation automatique** : L'application genere des contrats depuis le referentiel de 128 anomalies
2. **Validation** : Chaque regle est validee contre les donnees reelles
3. **Scores DAMA** : 6 dimensions ISO 8000 calculees dynamiquement
4. **Export** : ODCS v3.1.0 (YAML), JSON, rapport de violations
5. **Import CSV** : Ajoutez vos propres anomalies metier

### 3.11 Parametres

Configuration de l'application :
- Cle API Claude (pour fonctionnalites IA)
- Budget de scan (QUICK / STANDARD / DEEP)
- Parametres avances

### 3.12 Aide

Guide utilisateur integre dans l'application.

---

## 4. Exemples pratiques

### 4.1 Exemple : Analyser un fichier RH

**Scenario** : Vous etes DRH et devez verifier la qualite du fichier de paie mensuel.

1. **Charger** le fichier `paie_mars_2026.csv`
2. **Selectionner** les colonnes : Matricule, Nom, Salaire_Brut, Anciennete, Grade
3. **Choisir** l'usage : "Paie reglementaire"
4. **Analyser** les resultats :
   - Dashboard : vue d'ensemble
   - Priorites : quels attributs corriger en premier ?
   - Data Contracts : quelles regles sont violees ?

**Resultat attendu** :
- `Anciennete` sera probablement CRITIQUE en dimension DB (NULL ou incoherences)
- `Salaire_Brut` sera surveille pour les valeurs negatives et les outliers
- Le score global donnera la qualite du fichier avant envoi

### 4.2 Exemple : Generer un contrat de qualite

1. Onglet **Data Contracts** > cliquer sur **Generer les contrats**
2. L'application genere automatiquement des regles pour chaque colonne
3. Passer en revue les regles generees
4. Exporter au format **ODCS v3.1.0** pour integration dans un pipeline de donnees

### 4.3 Exemple : Ajouter une anomalie metier personnalisee

**Scenario** : Votre entreprise a une regle metier specifique : "Le code postal doit etre entre 01000 et 99999".

1. Creer un fichier CSV `mes_anomalies.csv` :
```csv
id,dimension,nom,criticite,detection,default_rule_type
BR#33,BR,Code postal hors France,ELEVE,Auto,range
```

2. Onglet **Data Contracts** > section **Import CSV**
3. Charger le fichier
4. La regle est automatiquement disponible pour la generation de contrats

### 4.4 Exemple : Comparer DAMA vs Probabiliste

1. Onglet **DAMA** apres avoir lance l'analyse
2. Observer comment un score DAMA de 82% peut masquer un P_DB de 99%
3. Comprendre pourquoi l'approche probabiliste detecte des risques invisibles en DAMA

---

## 5. Configuration de l'API Claude (optionnel)

Les fonctionnalites IA enrichissent l'application avec :
- Commentaires contextuels sur les resultats
- Dialogue d'elicitation guide
- Rapports narratifs personnalises

### Configuration :
1. Obtenir une cle API sur [console.anthropic.com](https://console.anthropic.com/)
2. Dans la barre laterale, section "Configuration IA"
3. Coller la cle dans le champ "Cle API Claude"

L'application fonctionne parfaitement sans cle API, les fonctionnalites IA sont un complement.

---

## 6. Glossaire

| Terme | Definition |
|-------|-----------|
| **AHP** | Analytic Hierarchy Process - methode de ponderation par comparaisons par paires |
| **Beta (distribution)** | Distribution de probabilite modelisant l'incertitude sur un taux d'erreur |
| **DAMA** | Data Management Association - referentiel de 6 dimensions de qualite (ISO 8000) |
| **IC 95%** | Intervalle de confiance a 95% - plage dans laquelle le vrai taux se situe |
| **Lineage** | Tracabilite des transformations de donnees d'un point a un autre |
| **ODCS** | Open Data Contract Standard - format standard pour les contrats de donnees |
| **P_DB, P_DP, P_BR, P_UP** | Probabilites d'erreur pour chaque dimension du framework 4D |
| **rule_type** | Type de regle de qualite (null_check, range, enum...) defini dans le catalogue |
| **Vecteur 4D** | Ensemble des 4 probabilites (P_DB, P_DP, P_BR, P_UP) pour un attribut |

---

## 7. FAQ

**Q : Combien d'anomalies sont detectees automatiquement ?**
R : Le referentiel contient 128 anomalies reparties sur 35 types de regles. Environ 33 ont des detecteurs automatiques, les autres sont Semi-automatiques ou Manuels.

**Q : Puis-je ajouter mes propres regles metier ?**
R : Oui, par import CSV dans l'onglet Data Contracts. Si le type de regle (rule_type) existe deja, aucun code Python n'est necessaire.

**Q : Comment interpreter un P_DB de 99% ?**
R : Cela signifie que 99% des lignes presentent une anomalie de structure dans cette colonne. C'est un signal d'alerte majeur.

**Q : L'application a-t-elle besoin d'internet ?**
R : Non, sauf pour les fonctionnalites IA (API Claude). Toute l'analyse est locale.

**Q : Quel est le format d'export recommande pour les contrats ?**
R : Le format ODCS v3.1.0 (YAML) est recommande pour l'integration dans des pipelines de donnees. Il suit le standard Bitol / Linux Foundation.

---

*Guide utilisateur — Augmented DQ Framework v3.0*
