#!/usr/bin/env python3
"""
=============================================================================
TEST COMPLET INDICATEURS DAMA vs APPROCHE PROBABILISTE 4D
=============================================================================

Ce test génère un dataset contrôlé pour valider TOUS les indicateurs DAMA:
1. COMPLÉTUDE (Completeness) - Présence des données
2. UNICITÉ (Uniqueness) - Absence de doublons
3. VALIDITÉ (Validity) - Conformité aux formats/règles
4. COHÉRENCE (Consistency) - Cohérence inter-champs
5. FRAÎCHEUR (Timeliness) - Actualité des données
6. EXACTITUDE (Accuracy) - Précision des valeurs

Et compare avec notre approche 4D:
- P_DB (Database Structure)
- P_DP (Data Processing)
- P_BR (Business Rules)
- P_UP (Usage-fit/Pertinence)

=============================================================================
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

from backend.engine.analyzer import analyze_dataset
from backend.engine.beta_calculator import compute_all_beta_vectors
from backend.engine.ahp_elicitor import AHPElicitor
from backend.engine.risk_scorer import RiskScorer
from backend.engine.comparator import DAMACalculator

# =============================================================================
# GÉNÉRATION DU DATASET DE TEST COMPLET
# =============================================================================

def generate_complete_test_dataset(n=500):
    """
    Génère un dataset RH complet avec des anomalies contrôlées
    pour tester TOUS les indicateurs DAMA
    """
    np.random.seed(42)
    random.seed(42)

    print("="*70)
    print("GÉNÉRATION DU DATASET DE TEST COMPLET")
    print("="*70)

    data = {}
    anomalies_injected = {}

    # =========================================================================
    # 1. MATRICULE - Test UNICITÉ
    # =========================================================================
    # 95% uniques, 5% doublons
    matricules = [f"EMP{i:05d}" for i in range(n)]
    # Injecter 5% de doublons
    n_dupes = int(n * 0.05)
    for i in range(n_dupes):
        matricules[random.randint(0, n-1)] = matricules[random.randint(0, n-1)]
    data['Matricule'] = matricules
    anomalies_injected['Matricule'] = {
        'type': 'UNICITÉ',
        'description': f'{n_dupes} doublons injectés (~5%)',
        'expected_uniqueness': 0.95
    }
    print(f"✓ Matricule: {n_dupes} doublons injectés")

    # =========================================================================
    # 2. NOM_COMPLET - Test COMPLÉTUDE
    # =========================================================================
    # 85% remplis, 15% nulls
    noms = []
    prenoms = ["Jean", "Marie", "Pierre", "Sophie", "Lucas", "Emma", "Hugo", "Léa"]
    noms_famille = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit"]
    for i in range(n):
        if i < int(n * 0.15):  # 15% nulls
            noms.append(None)
        else:
            noms.append(f"{random.choice(prenoms)} {random.choice(noms_famille)}")
    random.shuffle(noms)
    data['Nom_Complet'] = noms
    anomalies_injected['Nom_Complet'] = {
        'type': 'COMPLÉTUDE',
        'description': '15% de valeurs nulles',
        'expected_completeness': 0.85
    }
    print(f"✓ Nom_Complet: 15% nulls injectés")

    # =========================================================================
    # 3. EMAIL - Test VALIDITÉ (format)
    # =========================================================================
    # 80% emails valides, 20% invalides
    emails = []
    for i in range(n):
        if i < int(n * 0.20):  # 20% invalides
            invalid_types = [
                "email_sans_arobase.com",
                "email@@double.com",
                "@manque_debut.com",
                "manque_fin@",
                "espaces dans@email.com",
                "special!char@email.com",
                "",  # vide
                "juste_texte"
            ]
            emails.append(random.choice(invalid_types))
        else:
            emails.append(f"employe{i}@entreprise.com")
    random.shuffle(emails)
    data['Email'] = emails
    anomalies_injected['Email'] = {
        'type': 'VALIDITÉ',
        'description': '20% emails invalides (format incorrect)',
        'expected_validity': 0.80
    }
    print(f"✓ Email: 20% formats invalides injectés")

    # =========================================================================
    # 4. TELEPHONE - Test VALIDITÉ (pattern)
    # =========================================================================
    # 75% valides (format FR), 25% invalides
    telephones = []
    for i in range(n):
        if i < int(n * 0.25):  # 25% invalides
            invalid_phones = [
                "123",  # trop court
                "abcdefghij",  # lettres
                "01234567890123",  # trop long
                "+33 6 12",  # incomplet
                "06-12-34-56-7a",  # avec lettre
                None,  # null
            ]
            telephones.append(random.choice(invalid_phones))
        else:
            # Format FR valide: 06 XX XX XX XX
            telephones.append(f"06{random.randint(10000000, 99999999)}")
    random.shuffle(telephones)
    data['Telephone'] = telephones
    anomalies_injected['Telephone'] = {
        'type': 'VALIDITÉ',
        'description': '25% téléphones invalides',
        'expected_validity': 0.75
    }
    print(f"✓ Telephone: 25% formats invalides injectés")

    # =========================================================================
    # 5. DATE_NAISSANCE - Test COHÉRENCE (avec Date_Embauche)
    # =========================================================================
    # On génère des dates qui seront comparées avec Date_Embauche
    # 10% incohérents (embauché avant la naissance!)
    dates_naissance = []
    base_year = 1970
    for i in range(n):
        year = random.randint(base_year, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        dates_naissance.append(datetime(year, month, day))
    data['Date_Naissance'] = dates_naissance

    # =========================================================================
    # 6. DATE_EMBAUCHE - Test COHÉRENCE + FRAÎCHEUR
    # =========================================================================
    # 10% incohérents avec Date_Naissance (embauché avant naissance)
    # 20% données "périmées" (> 5 ans sans mise à jour)
    dates_embauche = []
    for i in range(n):
        if i < int(n * 0.10):  # 10% incohérents
            # Date embauche AVANT naissance (impossible!)
            dates_embauche.append(dates_naissance[i] - timedelta(days=random.randint(365, 3650)))
        elif i < int(n * 0.30):  # 20% supplémentaires très anciennes (fraîcheur)
            # Embauche > 20 ans (données potentiellement obsolètes)
            dates_embauche.append(datetime.now() - timedelta(days=random.randint(7300, 10000)))
        else:
            # Date normale: entre naissance+18 ans et aujourd'hui
            min_date = dates_naissance[i] + timedelta(days=18*365)
            max_date = datetime.now()
            if min_date < max_date:
                days_range = (max_date - min_date).days
                dates_embauche.append(min_date + timedelta(days=random.randint(0, max(1, days_range))))
            else:
                dates_embauche.append(datetime.now() - timedelta(days=random.randint(0, 3650)))
    data['Date_Embauche'] = dates_embauche
    anomalies_injected['Date_Embauche'] = {
        'type': 'COHÉRENCE + FRAÎCHEUR',
        'description': '10% incohérents (avant naissance), 20% très anciennes',
        'expected_consistency': 0.90,
        'expected_timeliness': 0.80
    }
    print(f"✓ Date_Embauche: 10% incohérents + 20% obsolètes")

    # =========================================================================
    # 7. SALAIRE - Test EXACTITUDE (outliers) + VALIDITÉ (négatifs)
    # =========================================================================
    # 5% négatifs (erreur), 5% outliers extrêmes, 5% à 0
    salaires = []
    for i in range(n):
        if i < int(n * 0.05):  # 5% négatifs
            salaires.append(-random.randint(1000, 5000))
        elif i < int(n * 0.10):  # 5% outliers (salaires impossibles)
            salaires.append(random.randint(500000, 10000000))  # 500K-10M
        elif i < int(n * 0.15):  # 5% à zéro
            salaires.append(0)
        else:
            salaires.append(round(random.uniform(25000, 120000), 2))
    random.shuffle(salaires)
    data['Salaire'] = salaires
    anomalies_injected['Salaire'] = {
        'type': 'EXACTITUDE + VALIDITÉ',
        'description': '5% négatifs, 5% outliers extrêmes, 5% zéro',
        'expected_accuracy': 0.85
    }
    print(f"✓ Salaire: 15% anomalies (négatifs/outliers/zéros)")

    # =========================================================================
    # 8. CODE_POSTAL - Test VALIDITÉ (format strict)
    # =========================================================================
    # 70% valides (5 chiffres FR), 30% invalides
    codes_postaux = []
    for i in range(n):
        if i < int(n * 0.30):  # 30% invalides
            invalid_cp = [
                "7500",  # 4 chiffres
                "750001",  # 6 chiffres
                "ABCDE",  # lettres
                "75 000",  # espace
                "75-001",  # tiret
                None,
                "",
            ]
            codes_postaux.append(random.choice(invalid_cp))
        else:
            # Code postal FR valide
            codes_postaux.append(f"{random.randint(10000, 99999)}")
    random.shuffle(codes_postaux)
    data['Code_Postal'] = codes_postaux
    anomalies_injected['Code_Postal'] = {
        'type': 'VALIDITÉ',
        'description': '30% codes postaux invalides',
        'expected_validity': 0.70
    }
    print(f"✓ Code_Postal: 30% formats invalides")

    # =========================================================================
    # 9. DEPARTEMENT - Test UNICITÉ (faible par design) + COHÉRENCE
    # =========================================================================
    # Seulement 5 valeurs possibles → unicité ~1%
    # 10% incohérents avec Code_Postal
    departements = ["RH", "Finance", "IT", "Commercial", "Production"]
    deps = [random.choice(departements) for _ in range(n)]
    data['Departement'] = deps
    anomalies_injected['Departement'] = {
        'type': 'UNICITÉ (attendue basse)',
        'description': '5 valeurs pour 500 lignes',
        'expected_uniqueness': 0.01  # ~1%
    }
    print(f"✓ Departement: Unicité volontairement basse (5 valeurs)")

    # =========================================================================
    # 10. DATE_DERNIERE_MAJ - Test FRAÎCHEUR explicite
    # =========================================================================
    # 60% récentes (< 1 an), 20% moyennes (1-3 ans), 20% obsolètes (> 3 ans)
    dates_maj = []
    now = datetime.now()
    for i in range(n):
        if i < int(n * 0.60):  # 60% récentes
            dates_maj.append(now - timedelta(days=random.randint(0, 365)))
        elif i < int(n * 0.80):  # 20% moyennes
            dates_maj.append(now - timedelta(days=random.randint(366, 1095)))
        else:  # 20% obsolètes
            dates_maj.append(now - timedelta(days=random.randint(1096, 3650)))
    random.shuffle(dates_maj)
    data['Date_Derniere_MAJ'] = dates_maj
    anomalies_injected['Date_Derniere_MAJ'] = {
        'type': 'FRAÎCHEUR',
        'description': '60% récentes, 20% moyennes, 20% obsolètes',
        'expected_timeliness': 0.60  # Si seuil = 1 an
    }
    print(f"✓ Date_Derniere_MAJ: Distribution fraîcheur contrôlée")

    # =========================================================================
    # 11. STATUT - Test VALIDITÉ (domaine de valeurs)
    # =========================================================================
    # 85% valeurs du domaine, 15% hors domaine
    statuts_valides = ["CDI", "CDD", "Alternance", "Stage", "Interim"]
    statuts = []
    for i in range(n):
        if i < int(n * 0.15):  # 15% hors domaine
            statuts_invalides = ["CDDI", "cdi", "Permanent", "Contractuel", "???", "N/A", ""]
            statuts.append(random.choice(statuts_invalides))
        else:
            statuts.append(random.choice(statuts_valides))
    random.shuffle(statuts)
    data['Statut'] = statuts
    anomalies_injected['Statut'] = {
        'type': 'VALIDITÉ (domaine)',
        'description': '15% valeurs hors domaine autorisé',
        'expected_validity': 0.85
    }
    print(f"✓ Statut: 15% valeurs hors domaine")

    # =========================================================================
    # 12. ANCIENNETE_ANNEES - Test COHÉRENCE avec Date_Embauche
    # =========================================================================
    # Calculer ancienneté réelle et injecter 15% incohérences
    anciennetes = []
    for i in range(n):
        real_anciennete = (datetime.now() - dates_embauche[i]).days / 365.25
        if i < int(n * 0.15):  # 15% incohérents
            # Ancienneté très différente du calcul
            anciennetes.append(round(real_anciennete + random.uniform(5, 20), 1))
        else:
            anciennetes.append(round(real_anciennete, 1))
    data['Anciennete_Annees'] = anciennetes
    anomalies_injected['Anciennete_Annees'] = {
        'type': 'COHÉRENCE',
        'description': '15% incohérents avec Date_Embauche',
        'expected_consistency': 0.85
    }
    print(f"✓ Anciennete_Annees: 15% incohérents")

    # =========================================================================
    # 13. NOTE_EVALUATION - Test VALIDITÉ (plage) + EXACTITUDE
    # =========================================================================
    # Notes sur 20, mais 10% hors plage, 5% granularité incorrecte
    notes = []
    for i in range(n):
        if i < int(n * 0.10):  # 10% hors plage [0, 20]
            notes.append(random.choice([-5, 25, 100, -10, 50]))
        elif i < int(n * 0.15):  # 5% granularité bizarre
            notes.append(round(random.uniform(0, 20), 5))  # Trop de décimales
        else:
            notes.append(round(random.uniform(8, 20), 1))
    random.shuffle(notes)
    data['Note_Evaluation'] = notes
    anomalies_injected['Note_Evaluation'] = {
        'type': 'VALIDITÉ (plage)',
        'description': '10% hors plage [0,20], 5% granularité incorrecte',
        'expected_validity': 0.85
    }
    print(f"✓ Note_Evaluation: 15% anomalies plage/granularité")

    # =========================================================================
    # 14. IBAN - Test VALIDITÉ (format complexe)
    # =========================================================================
    # 65% valides, 35% invalides
    ibans = []
    for i in range(n):
        if i < int(n * 0.35):  # 35% invalides
            invalid_ibans = [
                "FR7630001007941234567890185",  # Trop long
                "FR761234",  # Trop court
                "XX7630001007941234567890",  # Pays invalide
                "FR76ABCDEFGHIJ1234567890",  # Lettres au milieu
                None,
                "",
                "NOTANIBAN",
            ]
            ibans.append(random.choice(invalid_ibans))
        else:
            # IBAN FR valide (simplifié)
            ibans.append(f"FR76{random.randint(10000000000000000000, 99999999999999999999)}")
    random.shuffle(ibans)
    data['IBAN'] = ibans
    anomalies_injected['IBAN'] = {
        'type': 'VALIDITÉ (format complexe)',
        'description': '35% IBANs invalides',
        'expected_validity': 0.65
    }
    print(f"✓ IBAN: 35% formats invalides")

    # =========================================================================
    # 15. COMMENTAIRE - Test données libres (longueur, caractères)
    # =========================================================================
    # Texte libre avec anomalies diverses
    commentaires = []
    for i in range(n):
        if i < int(n * 0.10):  # 10% vides
            commentaires.append("")
        elif i < int(n * 0.15):  # 5% trop longs
            commentaires.append("A" * 5000)
        elif i < int(n * 0.20):  # 5% caractères spéciaux/injection
            commentaires.append("<script>alert('xss')</script>")
        elif i < int(n * 0.25):  # 5% nulls
            commentaires.append(None)
        else:
            commentaires.append(f"Commentaire standard pour employé {i}")
    random.shuffle(commentaires)
    data['Commentaire'] = commentaires
    anomalies_injected['Commentaire'] = {
        'type': 'QUALITÉ TEXTE',
        'description': '10% vides, 5% trop longs, 5% injection, 5% nulls',
        'expected_quality': 0.75
    }
    print(f"✓ Commentaire: 25% anomalies texte")

    # Créer DataFrame
    df = pd.DataFrame(data)

    print(f"\n✅ Dataset généré: {len(df)} lignes × {len(df.columns)} colonnes")
    print("="*70)

    return df, anomalies_injected


# =============================================================================
# CALCUL DES MÉTRIQUES DAMA
# =============================================================================

def calculate_dama_metrics(df, anomalies_info):
    """
    Calcule les 6 dimensions DAMA pour chaque colonne
    """
    print("\n" + "="*70)
    print("CALCUL DES MÉTRIQUES DAMA")
    print("="*70)

    dama_calc = DAMACalculator()
    columns = list(df.columns)

    # Calcul DAMA standard
    dama_scores = dama_calc.compute_all_dama_scores(df, columns)

    # Calculs supplémentaires pour les dimensions non couvertes
    extended_dama = {}

    for col in columns:
        extended_dama[col] = {
            'completeness': dama_scores[col].get('completeness', 0),
            'uniqueness': dama_scores[col].get('uniqueness', 0),
            'validity': 0,
            'consistency': 0,
            'timeliness': 0,
            'accuracy': 0,
        }

        series = df[col]
        non_null = series.dropna()
        n_total = len(series)
        n_non_null = len(non_null)

        # -----------------------------------------------------------------
        # VALIDITÉ - Conformité au format attendu
        # -----------------------------------------------------------------
        if col == 'Email':
            # Regex simple pour email
            valid_count = non_null.astype(str).str.match(
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            ).sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        elif col == 'Telephone':
            # Format FR: 10 chiffres commençant par 0
            valid_count = non_null.astype(str).str.match(r'^0[1-9]\d{8}$').sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        elif col == 'Code_Postal':
            # 5 chiffres
            valid_count = non_null.astype(str).str.match(r'^\d{5}$').sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        elif col == 'IBAN':
            # IBAN FR: FR + 2 chiffres + 23 caractères
            valid_count = non_null.astype(str).str.match(r'^FR\d{2}[A-Z0-9]{23}$').sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        elif col == 'Statut':
            # Domaine de valeurs
            valeurs_valides = {"CDI", "CDD", "Alternance", "Stage", "Interim"}
            valid_count = non_null.isin(valeurs_valides).sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        elif col == 'Note_Evaluation':
            # Plage [0, 20]
            numeric = pd.to_numeric(series, errors='coerce')
            valid_count = ((numeric >= 0) & (numeric <= 20)).sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        elif col == 'Salaire':
            # Positif et raisonnable (< 500K)
            numeric = pd.to_numeric(series, errors='coerce')
            valid_count = ((numeric > 0) & (numeric < 500000)).sum()
            extended_dama[col]['validity'] = valid_count / n_total if n_total > 0 else 0

        else:
            extended_dama[col]['validity'] = extended_dama[col]['completeness']

        # -----------------------------------------------------------------
        # COHÉRENCE - Relations inter-champs
        # -----------------------------------------------------------------
        if col == 'Date_Embauche':
            # Embauche doit être après naissance + 16 ans
            try:
                embauche = pd.to_datetime(df['Date_Embauche'], errors='coerce')
                naissance = pd.to_datetime(df['Date_Naissance'], errors='coerce')
                age_embauche = (embauche - naissance).dt.days / 365.25
                coherent_count = (age_embauche >= 16).sum()
                extended_dama[col]['consistency'] = coherent_count / n_total
            except:
                extended_dama[col]['consistency'] = 0

        elif col == 'Anciennete_Annees':
            # Doit correspondre à Date_Embauche
            try:
                embauche = pd.to_datetime(df['Date_Embauche'], errors='coerce')
                now = datetime.now()
                calc_anciennete = (now - embauche).dt.days / 365.25
                declared = df['Anciennete_Annees']
                # Tolérance de 1 an
                coherent_count = (abs(calc_anciennete - declared) < 1).sum()
                extended_dama[col]['consistency'] = coherent_count / n_total
            except:
                extended_dama[col]['consistency'] = 0
        else:
            extended_dama[col]['consistency'] = 1.0  # Pas de règle de cohérence

        # -----------------------------------------------------------------
        # FRAÎCHEUR - Actualité des données
        # -----------------------------------------------------------------
        if col == 'Date_Derniere_MAJ':
            try:
                dates = pd.to_datetime(series, errors='coerce')
                now = datetime.now()
                age_days = (now - dates).dt.days
                # Frais si < 365 jours
                fresh_count = (age_days < 365).sum()
                extended_dama[col]['timeliness'] = fresh_count / n_total
            except:
                extended_dama[col]['timeliness'] = 0

        elif col == 'Date_Embauche':
            try:
                dates = pd.to_datetime(series, errors='coerce')
                now = datetime.now()
                age_years = (now - dates).dt.days / 365.25
                # Considérer "frais" si < 10 ans
                fresh_count = (age_years < 10).sum()
                extended_dama[col]['timeliness'] = fresh_count / n_total
            except:
                extended_dama[col]['timeliness'] = 0
        else:
            extended_dama[col]['timeliness'] = 1.0  # Non applicable

        # -----------------------------------------------------------------
        # EXACTITUDE - Précision des valeurs
        # -----------------------------------------------------------------
        if col == 'Salaire':
            # Pas de valeurs aberrantes (z-score < 3)
            numeric = pd.to_numeric(series, errors='coerce').dropna()
            if len(numeric) > 0:
                mean = numeric.mean()
                std = numeric.std()
                if std > 0:
                    z_scores = abs((numeric - mean) / std)
                    accurate_count = (z_scores < 3).sum()
                    extended_dama[col]['accuracy'] = accurate_count / n_total
                else:
                    extended_dama[col]['accuracy'] = 1.0
            else:
                extended_dama[col]['accuracy'] = 0

        elif col == 'Note_Evaluation':
            # Valeurs dans plage raisonnable [0, 20] avec 1 décimale max
            numeric = pd.to_numeric(series, errors='coerce')
            valid = ((numeric >= 0) & (numeric <= 20))
            decimals_ok = (numeric * 10 == (numeric * 10).round())
            accurate_count = (valid & decimals_ok).sum()
            extended_dama[col]['accuracy'] = accurate_count / n_total
        else:
            extended_dama[col]['accuracy'] = extended_dama[col]['validity']

    return extended_dama


# =============================================================================
# CALCUL DES MÉTRIQUES 4D PROBABILISTES
# =============================================================================

def calculate_4d_metrics(df):
    """
    Calcule les vecteurs 4D pour chaque colonne
    """
    print("\n" + "="*70)
    print("CALCUL DES VECTEURS 4D PROBABILISTES")
    print("="*70)

    columns = list(df.columns)
    stats = analyze_dataset(df, columns)
    vectors = compute_all_beta_vectors(df, columns, stats, 'standard')

    return vectors, stats


# =============================================================================
# COMPARAISON DAMA vs 4D
# =============================================================================

def compare_dama_vs_4d(df, dama_metrics, vectors_4d, anomalies_info):
    """
    Compare les résultats DAMA avec l'approche 4D
    """
    print("\n" + "="*70)
    print("COMPARAISON DAMA vs APPROCHE 4D")
    print("="*70)

    elicitor = AHPElicitor()
    scorer = RiskScorer()

    # Pondérations pour différents usages
    w_paie = elicitor.get_weights_preset('paie_reglementaire')
    w_dashboard = elicitor.get_weights_preset('dashboard_operationnel')
    w_audit = elicitor.get_weights_preset('audit_conformite')

    results = []

    for col in df.columns:
        dama = dama_metrics[col]
        vec = vectors_4d.get(col, {'P_DB': 0, 'P_DP': 0, 'P_BR': 0, 'P_UP': 0})

        # Scores contextuels (×100 pour pourcentage)
        score_paie = scorer.compute_risk_score(vec, w_paie) * 100
        score_dashboard = scorer.compute_risk_score(vec, w_dashboard) * 100
        score_audit = scorer.compute_risk_score(vec, w_audit) * 100

        # Score DAMA global
        dama_global = (
            dama['completeness'] * 0.25 +
            dama['uniqueness'] * 0.15 +
            dama['validity'] * 0.25 +
            dama['consistency'] * 0.15 +
            dama['timeliness'] * 0.10 +
            dama['accuracy'] * 0.10
        )

        results.append({
            'Colonne': col,
            'Anomalie_Type': anomalies_info.get(col, {}).get('type', '-'),
            # DAMA
            'DAMA_Complétude': dama['completeness'],
            'DAMA_Unicité': dama['uniqueness'],
            'DAMA_Validité': dama['validity'],
            'DAMA_Cohérence': dama['consistency'],
            'DAMA_Fraîcheur': dama['timeliness'],
            'DAMA_Exactitude': dama['accuracy'],
            'DAMA_Global': dama_global,
            # 4D
            'P_DB': vec['P_DB'],
            'P_DP': vec['P_DP'],
            'P_BR': vec['P_BR'],
            'P_UP': vec['P_UP'],
            # Scores contextuels
            'Score_Paie': score_paie,
            'Score_Dashboard': score_dashboard,
            'Score_Audit': score_audit,
        })

    return pd.DataFrame(results)


# =============================================================================
# AFFICHAGE DES RÉSULTATS
# =============================================================================

def display_results(comparison_df, anomalies_info):
    """
    Affiche les résultats de manière structurée
    """
    print("\n" + "="*70)
    print("RÉSULTATS DÉTAILLÉS PAR COLONNE")
    print("="*70)

    for _, row in comparison_df.iterrows():
        col = row['Colonne']
        print(f"\n{'─'*70}")
        print(f"📊 {col}")
        print(f"   Type d'anomalie: {row['Anomalie_Type']}")

        # Métriques DAMA
        print(f"\n   📈 MÉTRIQUES DAMA:")
        print(f"      Complétude:  {row['DAMA_Complétude']:.1%}")
        print(f"      Unicité:     {row['DAMA_Unicité']:.1%}")
        print(f"      Validité:    {row['DAMA_Validité']:.1%}")
        print(f"      Cohérence:   {row['DAMA_Cohérence']:.1%}")
        print(f"      Fraîcheur:   {row['DAMA_Fraîcheur']:.1%}")
        print(f"      Exactitude:  {row['DAMA_Exactitude']:.1%}")
        print(f"      → Global:    {row['DAMA_Global']:.1%}")

        # Vecteur 4D
        print(f"\n   🎯 VECTEUR 4D:")
        print(f"      P_DB (Structure):   {row['P_DB']:.1%}")
        print(f"      P_DP (Processing):  {row['P_DP']:.1%}")
        print(f"      P_BR (Business):    {row['P_BR']:.1%}")
        print(f"      P_UP (Usage-fit):   {row['P_UP']:.1%}")

        # Scores contextuels
        print(f"\n   🏢 SCORES PAR USAGE:")
        print(f"      Paie:       {row['Score_Paie']:.0f}% risque")
        print(f"      Dashboard:  {row['Score_Dashboard']:.0f}% risque")
        print(f"      Audit:      {row['Score_Audit']:.0f}% risque")

        # Analyse
        anomaly = anomalies_info.get(col, {})
        expected = anomaly.get('expected_validity', anomaly.get('expected_completeness', anomaly.get('expected_uniqueness', None)))
        if expected:
            actual = row['DAMA_Validité'] if 'VALIDITÉ' in row['Anomalie_Type'] else \
                     row['DAMA_Complétude'] if 'COMPLÉTUDE' in row['Anomalie_Type'] else \
                     row['DAMA_Unicité'] if 'UNICITÉ' in row['Anomalie_Type'] else None
            if actual:
                diff = abs(actual - expected)
                status = "✅" if diff < 0.05 else "⚠️" if diff < 0.10 else "❌"
                print(f"\n   {status} Attendu: {expected:.1%}, Calculé: {actual:.1%} (Δ={diff:.1%})")


def display_summary(comparison_df):
    """
    Affiche un résumé comparatif
    """
    print("\n" + "="*70)
    print("RÉSUMÉ COMPARATIF DAMA vs 4D")
    print("="*70)

    print("\n📊 TABLEAU RÉCAPITULATIF:")
    print("-" * 100)
    print(f"{'Colonne':<20} {'DAMA Global':>12} {'P_DB':>8} {'P_DP':>8} {'P_BR':>8} {'P_UP':>8} {'Paie':>8} {'Dashboard':>10}")
    print("-" * 100)

    for _, row in comparison_df.iterrows():
        print(f"{row['Colonne']:<20} {row['DAMA_Global']:>11.1%} {row['P_DB']:>7.1%} {row['P_DP']:>7.1%} {row['P_BR']:>7.1%} {row['P_UP']:>7.1%} {row['Score_Paie']:>7.0f}% {row['Score_Dashboard']:>9.0f}%")

    print("-" * 100)

    # Analyse des avantages de l'approche 4D
    print("\n" + "="*70)
    print("AVANTAGES DE L'APPROCHE 4D DÉMONTRÉS")
    print("="*70)

    # Trouver les cas où les scores varient significativement par usage
    diff_scores = comparison_df['Score_Paie'] - comparison_df['Score_Dashboard']
    significant_diff = comparison_df[abs(diff_scores) > 5]

    print(f"\n✅ {len(significant_diff)} colonnes avec scores différents selon l'usage:")
    for _, row in significant_diff.iterrows():
        diff = row['Score_Paie'] - row['Score_Dashboard']
        print(f"   • {row['Colonne']}: Paie={row['Score_Paie']:.0f}%, Dashboard={row['Score_Dashboard']:.0f}% (Δ={diff:+.0f}%)")

    # Colonnes à risque élevé pour la Paie
    high_risk_paie = comparison_df[comparison_df['Score_Paie'] > 20]
    print(f"\n⚠️ {len(high_risk_paie)} colonnes à risque élevé pour la Paie:")
    for _, row in high_risk_paie.iterrows():
        print(f"   • {row['Colonne']}: {row['Score_Paie']:.0f}% (P_DB={row['P_DB']:.0%})")

    # Colonnes à risque élevé pour Dashboard
    high_risk_dash = comparison_df[comparison_df['Score_Dashboard'] > 20]
    print(f"\n📊 {len(high_risk_dash)} colonnes à risque élevé pour Dashboard:")
    for _, row in high_risk_dash.iterrows():
        print(f"   • {row['Colonne']}: {row['Score_Dashboard']:.0f}% (P_UP={row['P_UP']:.0%})")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*70)
    print("   TEST COMPLET: INDICATEURS DAMA vs APPROCHE 4D")
    print("="*70)
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # 1. Générer le dataset
    df, anomalies_info = generate_complete_test_dataset(n=500)

    # Sauvegarder le dataset
    output_path = os.path.join(os.path.dirname(__file__), 'test_dataset_dama_complete.xlsx')
    df.to_excel(output_path, index=False)
    print(f"\n💾 Dataset sauvegardé: {output_path}")

    # 2. Calculer métriques DAMA
    dama_metrics = calculate_dama_metrics(df, anomalies_info)

    # 3. Calculer vecteurs 4D
    vectors_4d, stats = calculate_4d_metrics(df)

    # 4. Comparer
    comparison_df = compare_dama_vs_4d(df, dama_metrics, vectors_4d, anomalies_info)

    # 5. Afficher résultats
    display_results(comparison_df, anomalies_info)
    display_summary(comparison_df)

    # Sauvegarder comparaison
    comparison_path = os.path.join(os.path.dirname(__file__), 'comparison_dama_4d.xlsx')
    comparison_df.to_excel(comparison_path, index=False)
    print(f"\n💾 Comparaison sauvegardée: {comparison_path}")

    print("\n" + "="*70)
    print("   TEST TERMINÉ")
    print("="*70 + "\n")

    return comparison_df


if __name__ == "__main__":
    results = main()
