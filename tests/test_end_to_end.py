"""
TEST END-TO-END - Validation complète du Framework DQ
=====================================================

Ce test :
1. Génère un fichier Excel avec des données contrôlées et des anomalies connues
2. Calcule MANUELLEMENT les métriques attendues
3. Exécute l'outil sur ces données
4. Compare les résultats calculés vs attendus
5. Valide la cohérence globale

Auteur: Test automatique
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Paths
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(PROJECT_DIR, "backend", "engine")
TEST_DIR = os.path.join(PROJECT_DIR, "tests")
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, ENGINE_DIR)

# Imports
os.chdir(ENGINE_DIR)
import analyzer
import beta_calculator
import ahp_elicitor
import risk_scorer
import comparator
os.chdir(PROJECT_DIR)

# ============================================================================
# GÉNÉRATION DU DATASET DE TEST
# ============================================================================

def generate_controlled_dataset():
    """
    Génère un dataset RH réaliste avec des anomalies CONTRÔLÉES

    On sait exactement ce qu'on met, donc on peut calculer les métriques attendues.
    """
    np.random.seed(2024)
    n = 200  # 200 employés

    # ========================================================================
    # COLONNE 1: Matricule (parfait - aucune anomalie)
    # ========================================================================
    # Attendu: P_DB=0, P_DP=0, P_BR=0, P_UP=0, Unicité=100%, Complétude=100%
    matricules = [f"EMP{i:05d}" for i in range(1, n+1)]

    # ========================================================================
    # COLONNE 2: Ancienneté (problème de type - VARCHAR au lieu de NUMBER)
    # ========================================================================
    # 60% avec virgule européenne (ex: "7,5"), 40% correct
    # Attendu: P_DB élevé (~60%), P_DP=0, P_BR=0, P_UP faible
    anciennete = []
    for i in range(n):
        if i < 120:  # 60% avec virgule
            anciennete.append(f"{np.random.randint(1, 30)},{np.random.randint(0, 9)}")
        else:  # 40% correct (float)
            anciennete.append(round(np.random.uniform(0.5, 35), 1))

    # ========================================================================
    # COLONNE 3: Salaire (quelques valeurs négatives - violation métier)
    # ========================================================================
    # 5% de valeurs négatives (erreurs de saisie)
    # Attendu: P_DB=0, P_DP=0, P_BR~5%, P_UP faible (outliers)
    salaires = []
    for i in range(n):
        if i < 10:  # 5% négatifs (10/200)
            salaires.append(-abs(np.random.randint(100, 5000)))
        else:
            salaires.append(round(np.random.uniform(25000, 120000), 2))

    # ========================================================================
    # COLONNE 4: Date_Embauche (formats mixtes)
    # ========================================================================
    # 50% format YYYY-MM-DD, 30% format DD/MM/YYYY, 20% format MM-DD-YYYY
    # Attendu: P_DB élevé (formats mixtes), P_DP élevé
    dates_embauche = []
    base_date = datetime(2000, 1, 1)
    for i in range(n):
        date = base_date + timedelta(days=np.random.randint(0, 8000))
        if i < 100:  # 50% ISO
            dates_embauche.append(date.strftime("%Y-%m-%d"))
        elif i < 160:  # 30% FR
            dates_embauche.append(date.strftime("%d/%m/%Y"))
        else:  # 20% US
            dates_embauche.append(date.strftime("%m-%d-%Y"))

    # ========================================================================
    # COLONNE 5: Email (20% nulls - problème utilisabilité)
    # ========================================================================
    # Attendu: P_DB=0, P_DP=0, P_BR=0, P_UP~20%
    emails = []
    for i in range(n):
        if i < 40:  # 20% nulls
            emails.append(None)
        else:
            emails.append(f"employe{i}@entreprise.com")

    # ========================================================================
    # COLONNE 6: Département (beaucoup de doublons - unicité basse)
    # ========================================================================
    # Seulement 5 valeurs possibles pour 200 lignes → unicité ~2.5%
    # Attendu: Unicité DAMA très basse
    departements = np.random.choice(
        ["RH", "Finance", "IT", "Commercial", "Production"],
        size=n
    ).tolist()

    # ========================================================================
    # COLONNE 7: Note_Performance (outliers)
    # ========================================================================
    # Notes entre 1-5, mais 3% de valeurs aberrantes (0, 10, -1)
    # Attendu: P_BR modéré (valeurs hors domaine), P_UP avec outliers
    notes = []
    for i in range(n):
        if i < 6:  # 3% aberrant
            notes.append(np.random.choice([0, 10, -1, 100]))
        else:
            notes.append(round(np.random.uniform(1, 5), 1))

    # ========================================================================
    # COLONNE 8: Statut (parfait - valeurs catégorielles propres)
    # ========================================================================
    # Attendu: Tout à 0, unicité basse (normal pour catégoriel)
    statuts = np.random.choice(["CDI", "CDD", "Stage", "Alternance"], size=n).tolist()

    # Créer le DataFrame
    df = pd.DataFrame({
        "Matricule": matricules,
        "Anciennete": anciennete,
        "Salaire": salaires,
        "Date_Embauche": dates_embauche,
        "Email": emails,
        "Departement": departements,
        "Note_Performance": notes,
        "Statut": statuts
    })

    return df


def calculate_expected_metrics(df):
    """
    Calcule MANUELLEMENT les métriques attendues pour chaque colonne
    """
    n = len(df)
    expected = {}

    # ========================================================================
    # MATRICULE - Parfait
    # ========================================================================
    expected["Matricule"] = {
        "completude": 1.0,  # 0 nulls
        "unicite": 1.0,     # Tous uniques
        "P_DB": 0.0,        # Pas de problème de type
        "P_DP": 0.0,        # Pas d'erreur parsing
        "P_BR": 0.0,        # Pas de violation métier
        "P_UP": 0.0,        # Pas de null ni outlier
    }

    # ========================================================================
    # ANCIENNETE - 60% avec virgule (type error)
    # ========================================================================
    # Compter les valeurs avec virgule
    virgule_count = sum(1 for v in df["Anciennete"] if isinstance(v, str) and ',' in str(v))
    expected["Anciennete"] = {
        "completude": 1.0,
        "unicite": None,  # Dépend des valeurs
        "P_DB": virgule_count / n,  # ~60%
        "P_DP": 0.0,
        "P_BR": 0.0,
        "P_UP": 0.0,
    }

    # ========================================================================
    # SALAIRE - 5% négatifs
    # ========================================================================
    negative_count = sum(1 for v in df["Salaire"] if v < 0)
    expected["Salaire"] = {
        "completude": 1.0,
        "unicite": None,
        "P_DB": 0.0,
        "P_DP": 0.0,
        "P_BR": negative_count / n,  # ~5%
        "P_UP": 0.0,  # Les outliers seront calculés
    }

    # ========================================================================
    # DATE_EMBAUCHE - Formats mixtes
    # ========================================================================
    expected["Date_Embauche"] = {
        "completude": 1.0,
        "unicite": None,
        "P_DB": 1.0,  # 100% car formats mixtes = type incohérent
        "P_DP": 0.3,  # Formats mixtes = problème de traitement
        "P_BR": 0.0,
        "P_UP": 0.0,
    }

    # ========================================================================
    # EMAIL - 20% nulls
    # ========================================================================
    null_count = df["Email"].isnull().sum()
    expected["Email"] = {
        "completude": 1 - (null_count / n),  # ~80%
        "unicite": None,
        "P_DB": 0.0,
        "P_DP": 0.0,
        "P_BR": 0.0,
        "P_UP": null_count / n,  # ~20%
    }

    # ========================================================================
    # DEPARTEMENT - 5 valeurs uniques sur 200
    # ========================================================================
    unique_count = df["Departement"].nunique()
    duplicated_count = df["Departement"].duplicated(keep='first').sum()
    expected["Departement"] = {
        "completude": 1.0,
        "unicite": 1 - (duplicated_count / n),  # ~2.5%
        "P_DB": 0.0,
        "P_DP": 0.0,
        "P_BR": 0.0,
        "P_UP": 0.0,
    }

    # ========================================================================
    # NOTE_PERFORMANCE - 3% aberrant
    # ========================================================================
    # Valeurs hors [1, 5]
    hors_domaine = sum(1 for v in df["Note_Performance"] if v < 1 or v > 5)
    expected["Note_Performance"] = {
        "completude": 1.0,
        "unicite": None,
        "P_DB": 0.0,
        "P_DP": 0.0,
        "P_BR": hors_domaine / n,  # ~3%
        "P_UP": 0.0,  # Outliers à calculer
    }

    # ========================================================================
    # STATUT - Parfait catégoriel
    # ========================================================================
    unique_count = df["Statut"].nunique()
    duplicated_count = df["Statut"].duplicated(keep='first').sum()
    expected["Statut"] = {
        "completude": 1.0,
        "unicite": 1 - (duplicated_count / n),  # ~2%
        "P_DB": 0.0,
        "P_DP": 0.0,
        "P_BR": 0.0,
        "P_UP": 0.0,
    }

    return expected


# ============================================================================
# TEST PRINCIPAL
# ============================================================================

def run_end_to_end_test():
    """Exécute le test complet end-to-end"""

    print("\n" + "="*70)
    print("TEST END-TO-END - FRAMEWORK PROBABILISTE DQ")
    print("="*70)

    # ========================================================================
    # ÉTAPE 1: Générer le dataset
    # ========================================================================
    print("\n📊 ÉTAPE 1: Génération du dataset de test...")
    df = generate_controlled_dataset()

    # Sauvegarder en Excel
    excel_path = os.path.join(TEST_DIR, "test_dataset_controlled.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"   ✅ Dataset généré: {len(df)} lignes, {len(df.columns)} colonnes")
    print(f"   📁 Fichier: {excel_path}")

    # Afficher aperçu
    print("\n   Aperçu des données:")
    print(df.head(3).to_string())

    # ========================================================================
    # ÉTAPE 2: Calculer les métriques ATTENDUES
    # ========================================================================
    print("\n📐 ÉTAPE 2: Calcul des métriques ATTENDUES (manuelles)...")
    expected = calculate_expected_metrics(df)

    print("\n   Métriques attendues par colonne:")
    for col, metrics in expected.items():
        print(f"\n   {col}:")
        print(f"      Complétude attendue: {metrics['completude']:.1%}")
        if metrics['unicite'] is not None:
            print(f"      Unicité attendue: {metrics['unicite']:.1%}")
        print(f"      P_DB attendu: {metrics['P_DB']:.1%}")
        print(f"      P_UP attendu: {metrics['P_UP']:.1%}")
        print(f"      P_BR attendu: {metrics['P_BR']:.1%}")

    # ========================================================================
    # ÉTAPE 3: Exécuter l'outil
    # ========================================================================
    print("\n🔧 ÉTAPE 3: Exécution de l'outil...")

    columns = df.columns.tolist()

    # Analyzer
    print("   → Analyse exploratoire...")
    stats = analyzer.analyze_dataset(df, columns)

    # Beta Calculator
    print("   → Calcul vecteurs 4D...")
    vecteurs = beta_calculator.compute_all_beta_vectors(df, columns, stats)

    # AHP Elicitor
    print("   → Élicitation pondérations...")
    ahp = ahp_elicitor.AHPElicitor()
    usages = [
        {"nom": "Paie", "type": "paie_reglementaire", "criticite": "HIGH"},
        {"nom": "Dashboard", "type": "dashboard_operationnel", "criticite": "MEDIUM"},
    ]
    weights = {u["nom"]: ahp.get_weights_preset(u["type"]) for u in usages}

    # Risk Scorer
    print("   → Calcul scores de risque...")
    scores = risk_scorer.compute_risk_scores(vecteurs, weights, usages)

    # DAMA Comparator
    print("   → Calcul scores DAMA...")
    dama_calc = comparator.DAMACalculator()
    dama_scores = {}
    for col in columns:
        dama_scores[col] = dama_calc.compute_dama_score(df, col)

    print("   ✅ Exécution terminée")

    # ========================================================================
    # ÉTAPE 4: Comparaison ATTENDU vs CALCULÉ
    # ========================================================================
    print("\n📊 ÉTAPE 4: Comparaison ATTENDU vs CALCULÉ...")

    errors = []
    warnings = []

    print("\n   " + "-"*65)
    print(f"   {'Colonne':<20} {'Métrique':<15} {'Attendu':<12} {'Calculé':<12} {'Status'}")
    print("   " + "-"*65)

    for col in columns:
        exp = expected.get(col, {})
        vec = vecteurs.get(col, {})
        dama = dama_scores.get(col, {})

        # Comparer Complétude DAMA
        exp_comp = exp.get('completude', 1.0)
        calc_comp = dama.get('completeness', 0)
        diff_comp = abs(exp_comp - calc_comp)
        status_comp = "✅" if diff_comp < 0.05 else "⚠️" if diff_comp < 0.15 else "❌"
        print(f"   {col:<20} {'Complétude':<15} {exp_comp:.1%}        {calc_comp:.1%}        {status_comp}")
        if status_comp == "❌":
            errors.append(f"{col}: Complétude {exp_comp:.1%} vs {calc_comp:.1%}")

        # Comparer Unicité DAMA
        if exp.get('unicite') is not None:
            exp_uni = exp['unicite']
            calc_uni = dama.get('uniqueness', 0)
            diff_uni = abs(exp_uni - calc_uni)
            status_uni = "✅" if diff_uni < 0.05 else "⚠️" if diff_uni < 0.15 else "❌"
            print(f"   {'':<20} {'Unicité':<15} {exp_uni:.1%}        {calc_uni:.1%}        {status_uni}")
            if status_uni == "❌":
                errors.append(f"{col}: Unicité {exp_uni:.1%} vs {calc_uni:.1%}")

        # Comparer P_DB
        exp_db = exp.get('P_DB', 0)
        calc_db = vec.get('P_DB', 0)
        diff_db = abs(exp_db - calc_db)
        # Tolérance plus large pour P_DB car la détection peut varier
        status_db = "✅" if diff_db < 0.20 else "⚠️" if diff_db < 0.40 else "❌"
        print(f"   {'':<20} {'P_DB':<15} {exp_db:.1%}        {calc_db:.1%}        {status_db}")
        if status_db == "❌":
            errors.append(f"{col}: P_DB {exp_db:.1%} vs {calc_db:.1%}")
        elif status_db == "⚠️":
            warnings.append(f"{col}: P_DB {exp_db:.1%} vs {calc_db:.1%}")

        # Comparer P_UP
        exp_up = exp.get('P_UP', 0)
        calc_up = vec.get('P_UP', 0)
        diff_up = abs(exp_up - calc_up)
        status_up = "✅" if diff_up < 0.10 else "⚠️" if diff_up < 0.25 else "❌"
        print(f"   {'':<20} {'P_UP':<15} {exp_up:.1%}        {calc_up:.1%}        {status_up}")
        if status_up == "❌":
            errors.append(f"{col}: P_UP {exp_up:.1%} vs {calc_up:.1%}")
        elif status_up == "⚠️":
            warnings.append(f"{col}: P_UP {exp_up:.1%} vs {calc_up:.1%}")

        # Comparer P_BR
        exp_br = exp.get('P_BR', 0)
        calc_br = vec.get('P_BR', 0)
        diff_br = abs(exp_br - calc_br)
        status_br = "✅" if diff_br < 0.05 else "⚠️" if diff_br < 0.15 else "❌"
        print(f"   {'':<20} {'P_BR':<15} {exp_br:.1%}        {calc_br:.1%}        {status_br}")
        if status_br == "❌":
            errors.append(f"{col}: P_BR {exp_br:.1%} vs {calc_br:.1%}")

        print("   " + "-"*65)

    # ========================================================================
    # ÉTAPE 5: Validation des scores de risque contextualisés
    # ========================================================================
    print("\n📈 ÉTAPE 5: Validation des scores contextualisés...")

    print("\n   Principe: Même colonne → scores différents selon usage")
    print("   " + "-"*65)

    for col in ["Anciennete", "Email", "Date_Embauche"]:
        score_paie = scores.get(f"{col}_Paie", 0)
        score_dash = scores.get(f"{col}_Dashboard", 0)
        diff = abs(score_paie - score_dash)

        print(f"   {col}:")
        print(f"      Score Paie:      {score_paie:.1%}")
        print(f"      Score Dashboard: {score_dash:.1%}")
        print(f"      Différence:      {diff:.1%}")

        # Vérifier logique métier
        vec = vecteurs.get(col, {})
        p_db = vec.get('P_DB', 0)
        p_up = vec.get('P_UP', 0)

        # Si P_DB élevé, Paie devrait être plus impacté (car w_DB=0.40 pour Paie)
        if p_db > 0.3:
            if score_paie > score_dash:
                print(f"      ✅ Logique OK: P_DB élevé ({p_db:.1%}) → Paie plus impacté")
            else:
                warnings.append(f"{col}: P_DB élevé mais Paie moins impacté que Dashboard")

        # Si P_UP élevé, Dashboard devrait être plus impacté (car w_UP=0.60 pour Dashboard)
        if p_up > 0.1:
            if score_dash > score_paie:
                print(f"      ✅ Logique OK: P_UP élevé ({p_up:.1%}) → Dashboard plus impacté")
            else:
                warnings.append(f"{col}: P_UP élevé mais Dashboard moins impacté que Paie")

        print()

    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    print("\n" + "="*70)
    print("RÉSUMÉ DU TEST END-TO-END")
    print("="*70)

    print(f"\n   📊 Dataset: {len(df)} lignes × {len(columns)} colonnes")
    print(f"   🎯 Colonnes testées: {', '.join(columns)}")
    print(f"   ⚖️ Usages testés: Paie, Dashboard")

    print(f"\n   ❌ Erreurs critiques: {len(errors)}")
    for e in errors:
        print(f"      - {e}")

    print(f"\n   ⚠️ Avertissements: {len(warnings)}")
    for w in warnings:
        print(f"      - {w}")

    if len(errors) == 0:
        print("\n   🎉 TEST END-TO-END RÉUSSI !")
        print("   → Les calculs de l'outil correspondent aux valeurs attendues")
        print("   → La contextualisation par usage fonctionne correctement")
    else:
        print(f"\n   ⚠️ TEST AVEC {len(errors)} ERREUR(S)")

    return {
        "errors": errors,
        "warnings": warnings,
        "df": df,
        "stats": stats,
        "vecteurs": vecteurs,
        "scores": scores,
        "dama_scores": dama_scores,
        "expected": expected
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    results = run_end_to_end_test()
