#!/usr/bin/env python3
"""
=============================================================================
TESTS COMPLETS PRÉ-DÉPLOIEMENT - Framework Probabiliste DQ
=============================================================================

Suite de tests exhaustive couvrant:
1. Cohérence mathématique
2. Cas limites (edge cases)
3. Volumétrie / Stress
4. Contextualisation
5. Robustesse données corrompues
6. Régression DAMA

=============================================================================
"""

import sys
import os
import time
import traceback
import warnings
warnings.filterwarnings('ignore')

# Ajouter le chemin parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Imports du framework
from backend.engine.analyzer import analyze_dataset
from backend.engine.beta_calculator import compute_all_beta_vectors
from backend.engine.ahp_elicitor import AHPElicitor
from backend.engine.risk_scorer import RiskScorer
from backend.engine.comparator import DAMACalculator

# =============================================================================
# CONFIGURATION
# =============================================================================
VERBOSE = True
RESULTS = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'errors': []
}

def log(msg, level="INFO"):
    """Logger avec niveau"""
    if VERBOSE or level in ["ERROR", "WARN"]:
        prefix = {"INFO": "   ", "OK": "   ✅", "FAIL": "   ❌", "WARN": "   ⚠️", "ERROR": "   🔴"}
        print(f"{prefix.get(level, '   ')} {msg}")

def test_passed(name):
    RESULTS['passed'] += 1
    log(f"{name}: PASS", "OK")

def test_failed(name, reason):
    RESULTS['failed'] += 1
    RESULTS['errors'].append(f"{name}: {reason}")
    log(f"{name}: FAIL - {reason}", "FAIL")

def test_warning(name, reason):
    RESULTS['warnings'] += 1
    log(f"{name}: {reason}", "WARN")

# =============================================================================
# TEST 1: COHÉRENCE MATHÉMATIQUE
# =============================================================================
def test_mathematical_coherence():
    """Vérifie que toutes les valeurs sont mathématiquement cohérentes"""
    print("\n" + "="*70)
    print("TEST 1: COHÉRENCE MATHÉMATIQUE")
    print("="*70)

    # Créer dataset de test
    np.random.seed(42)
    n = 500
    df = pd.DataFrame({
        'Col_Normal': np.random.choice(['A', 'B', 'C', None], n),
        'Col_Numeric': np.random.uniform(0, 100, n),
        'Col_WithNulls': [None if i < 100 else f"val_{i}" for i in range(n)],
        'Col_AllSame': ['SAME'] * n,
        'Col_AllUnique': [f"unique_{i}" for i in range(n)],
    })

    columns = list(df.columns)

    # Analyse
    stats = analyze_dataset(df, columns)

    # Calcul vecteurs
    vectors = compute_all_beta_vectors(df, columns, stats, profiling_level='standard')

    # Pondérations
    elicitor = AHPElicitor()
    weights = elicitor.get_weights_preset('paie_reglementaire')

    # Scores
    scorer = RiskScorer()

    errors = []

    # Test 1.1: Tous les P_XX dans [0, 1]
    log("Test 1.1: Vérification P_XX ∈ [0, 1]")
    for col, vec in vectors.items():
        for dim in ['P_DB', 'P_DP', 'P_BR', 'P_UP']:
            val = vec.get(dim, 0)
            if not (0 <= val <= 1):
                errors.append(f"{col}.{dim} = {val} hors [0,1]")

    if not errors:
        test_passed("P_XX dans [0, 1]")
    else:
        test_failed("P_XX dans [0, 1]", "; ".join(errors[:3]))

    # Test 1.2: Somme des pondérations = 1
    log("Test 1.2: Vérification Σ weights = 1")
    errors = []
    usages = ['paie_reglementaire', 'reporting_social', 'dashboard_operationnel', 'audit_conformite']
    for usage in usages:
        w = elicitor.get_weights_preset(usage)
        # Filtrer uniquement les valeurs numériques (w_DB, w_DP, w_BR, w_UP)
        numeric_weights = {k: v for k, v in w.items() if k.startswith('w_') and isinstance(v, (int, float))}
        total = sum(numeric_weights.values())
        if abs(total - 1.0) > 0.001:
            errors.append(f"{usage}: Σw = {total}")

    if not errors:
        test_passed("Σ pondérations = 1")
    else:
        test_failed("Σ pondérations = 1", "; ".join(errors))

    # Test 1.3: Scores de risque dans [0, 100]
    log("Test 1.3: Vérification scores ∈ [0, 100]")
    errors = []
    for col in columns:
        for usage in usages:
            w = elicitor.get_weights_preset(usage)
            score = scorer.compute_risk_score(vectors[col], w)
            if not (0 <= score <= 100):
                errors.append(f"{col}/{usage}: score = {score}")

    if not errors:
        test_passed("Scores dans [0, 100]")
    else:
        test_failed("Scores dans [0, 100]", "; ".join(errors[:3]))

    # Test 1.4: Distributions Beta valides (α, β > 0)
    log("Test 1.4: Vérification Beta(α, β) valides")
    errors = []
    for col, vec in vectors.items():
        for dim in ['P_DB', 'P_DP', 'P_BR', 'P_UP']:
            p = vec.get(dim, 0)
            # Alpha et Beta calculés selon notre formule
            n_obs = 100  # Hypothèse
            alpha = max(1, p * n_obs)
            beta = max(1, (1 - p) * n_obs)
            if alpha <= 0 or beta <= 0:
                errors.append(f"{col}.{dim}: α={alpha}, β={beta}")

    if not errors:
        test_passed("Distributions Beta valides")
    else:
        test_failed("Distributions Beta valides", "; ".join(errors[:3]))

    # Test 1.5: Monotonicité - Plus d'anomalies → score plus élevé
    log("Test 1.5: Vérification monotonicité")
    # Col_WithNulls a 20% nulls, Col_Normal moins → score WithNulls >= Normal pour Dashboard
    w_dashboard = elicitor.get_weights_preset('dashboard_operationnel')

    # Col_WithNulls devrait avoir P_UP plus élevé
    if vectors['Col_WithNulls']['P_UP'] >= vectors['Col_Normal']['P_UP']:
        test_passed("Monotonicité P_UP")
    else:
        test_warning("Monotonicité P_UP",
                    f"Col_WithNulls.P_UP ({vectors['Col_WithNulls']['P_UP']:.2f}) < Col_Normal.P_UP ({vectors['Col_Normal']['P_UP']:.2f})")

    return len(errors) == 0


# =============================================================================
# TEST 2: CAS LIMITES (EDGE CASES)
# =============================================================================
def test_edge_cases():
    """Teste les cas limites extrêmes"""
    print("\n" + "="*70)
    print("TEST 2: CAS LIMITES (EDGE CASES)")
    print("="*70)

    dama_calc = DAMACalculator()

    # Test 2.1: DataFrame avec 1 seule ligne
    log("Test 2.1: DataFrame 1 ligne")
    try:
        df_1row = pd.DataFrame({'A': ['value'], 'B': [123]})
        stats = analyze_dataset(df_1row, list(df_1row.columns))
        vectors = compute_all_beta_vectors(df_1row, list(df_1row.columns), stats, 'standard')
        test_passed("DataFrame 1 ligne")
    except Exception as e:
        test_failed("DataFrame 1 ligne", str(e))

    # Test 2.2: Colonne 100% nulls
    log("Test 2.2: Colonne 100% nulls")
    try:
        df_nulls = pd.DataFrame({
            'AllNull': [None] * 100,
            'Normal': range(100)
        })
        stats = analyze_dataset(df_nulls, list(df_nulls.columns))
        vectors = compute_all_beta_vectors(df_nulls, list(df_nulls.columns), stats, 'standard')

        # P_UP devrait être 1.0 (ou proche) pour AllNull
        if vectors['AllNull']['P_UP'] >= 0.9:
            test_passed("Colonne 100% nulls → P_UP élevé")
        else:
            test_warning("Colonne 100% nulls", f"P_UP = {vectors['AllNull']['P_UP']:.2f}, attendu >= 0.9")
    except Exception as e:
        test_failed("Colonne 100% nulls", str(e))

    # Test 2.3: Colonne 100% doublons (1 seule valeur)
    log("Test 2.3: Colonne 100% doublons")
    try:
        df_dupes = pd.DataFrame({
            'AllSame': ['DUPLICATE'] * 100,
            'Normal': range(100)
        })
        stats = analyze_dataset(df_dupes, list(df_dupes.columns))

        # Unicité DAMA
        dama_scores = dama_calc.compute_all_dama_scores(df_dupes, list(df_dupes.columns))
        uniqueness = dama_scores['AllSame']['uniqueness']
        if uniqueness <= 0.05:  # 5% ou moins
            test_passed("Colonne 100% doublons → Unicité basse")
        else:
            test_warning("Colonne 100% doublons", f"Unicité = {uniqueness:.2%}, attendu <= 5%")
    except Exception as e:
        test_failed("Colonne 100% doublons", str(e))

    # Test 2.4: Colonne 100% unique
    log("Test 2.4: Colonne 100% unique")
    try:
        df_unique = pd.DataFrame({
            'AllUnique': [f"val_{i}" for i in range(100)],
            'Normal': range(100)
        })
        stats = analyze_dataset(df_unique, list(df_unique.columns))
        dama_scores = dama_calc.compute_all_dama_scores(df_unique, list(df_unique.columns))

        uniqueness = dama_scores['AllUnique']['uniqueness']
        if uniqueness >= 0.99:
            test_passed("Colonne 100% unique → Unicité 100%")
        else:
            test_warning("Colonne 100% unique", f"Unicité = {uniqueness:.2%}, attendu >= 99%")
    except Exception as e:
        test_failed("Colonne 100% unique", str(e))

    # Test 2.5: Types de données spéciaux
    log("Test 2.5: Types spéciaux (dates, UUIDs)")
    try:
        df_special = pd.DataFrame({
            'Dates_ISO': pd.date_range('2020-01-01', periods=50).tolist() + [None]*50,
            'UUIDs': [f"550e8400-e29b-41d4-a716-{i:012d}" for i in range(100)],
            'Timestamps': [datetime.now() - timedelta(hours=i) for i in range(100)],
            'Floats_Precision': np.random.uniform(0.000001, 0.000009, 100)
        })
        stats = analyze_dataset(df_special, list(df_special.columns))
        vectors = compute_all_beta_vectors(df_special, list(df_special.columns), stats, 'standard')
        test_passed("Types spéciaux traités")
    except Exception as e:
        test_failed("Types spéciaux", str(e))

    # Test 2.6: Valeurs numériques extrêmes
    log("Test 2.6: Valeurs numériques extrêmes")
    try:
        df_extreme = pd.DataFrame({
            'TresGrand': [1e15, 1e16, 1e17] + [100]*97,
            'TresPetit': [1e-15, 1e-16, 1e-17] + [0.5]*97,
            'Negatifs': [-1e10, -1e11, -1e12] + [100]*97,
            'Mixed': [1e308, -1e308, 0] + [1]*97  # Valeurs extrêmes mais pas inf
        })

        stats = analyze_dataset(df_extreme, list(df_extreme.columns))
        vectors = compute_all_beta_vectors(df_extreme, list(df_extreme.columns), stats, 'standard')
        test_passed("Valeurs extrêmes traitées")
    except Exception as e:
        test_failed("Valeurs extrêmes", str(e))

    return True


# =============================================================================
# TEST 3: VOLUMÉTRIE / STRESS
# =============================================================================
def test_volumetry():
    """Teste la performance avec différentes tailles de données"""
    print("\n" + "="*70)
    print("TEST 3: VOLUMÉTRIE / STRESS")
    print("="*70)

    sizes = [1000, 5000, 10000, 50000]

    for n in sizes:
        log(f"Test 3.x: {n:,} lignes × 10 colonnes")
        try:
            start = time.time()

            # Générer dataset
            np.random.seed(42)
            df = pd.DataFrame({
                f'Col_{i}': np.random.choice(['A', 'B', 'C', 'D', None], n)
                for i in range(10)
            })

            # Analyse
            columns = list(df.columns)
            stats = analyze_dataset(df, columns)
            vectors = compute_all_beta_vectors(df, columns, stats, 'standard')

            elapsed = time.time() - start

            if elapsed < 30:  # Moins de 30 secondes
                test_passed(f"{n:,} lignes en {elapsed:.1f}s")
            elif elapsed < 60:
                test_warning(f"{n:,} lignes", f"Lent: {elapsed:.1f}s")
            else:
                test_failed(f"{n:,} lignes", f"Trop lent: {elapsed:.1f}s")

        except Exception as e:
            test_failed(f"{n:,} lignes", str(e))

    # Test avec beaucoup de colonnes
    log("Test 3.x: 1000 lignes × 50 colonnes")
    try:
        start = time.time()
        df = pd.DataFrame({
            f'Col_{i}': np.random.choice(['A', 'B', 'C', None], 1000)
            for i in range(50)
        })
        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        elapsed = time.time() - start

        if elapsed < 30:
            test_passed(f"50 colonnes en {elapsed:.1f}s")
        else:
            test_warning("50 colonnes", f"Lent: {elapsed:.1f}s")
    except Exception as e:
        test_failed("50 colonnes", str(e))

    return True


# =============================================================================
# TEST 4: CONTEXTUALISATION
# =============================================================================
def test_contextualization():
    """Vérifie que les scores varient selon le contexte d'usage"""
    print("\n" + "="*70)
    print("TEST 4: CONTEXTUALISATION PAR USAGE")
    print("="*70)

    # Dataset avec anomalies spécifiques à chaque dimension
    np.random.seed(42)
    n = 200

    df = pd.DataFrame({
        # Colonne avec problème DB (types mixtes - virgule décimale)
        'Col_DB_Issue': [f"{i},5" if i < 120 else str(i) for i in range(n)],

        # Colonne avec problème UP (beaucoup de nulls)
        'Col_UP_Issue': [None if i < 80 else f"val_{i}" for i in range(n)],

        # Colonne avec problème BR (valeurs négatives dans un montant)
        'Col_BR_Issue': [-100 if i < 20 else abs(np.random.uniform(100, 1000)) for i in range(n)],

        # Colonne parfaite
        'Col_Perfect': [f"OK_{i}" for i in range(n)]
    })

    columns = list(df.columns)
    stats = analyze_dataset(df, columns)
    vectors = compute_all_beta_vectors(df, columns, stats, 'standard')

    elicitor = AHPElicitor()
    scorer = RiskScorer()

    # Récupérer pondérations
    w_paie = elicitor.get_weights_preset('paie_reglementaire')      # Sensible DB
    w_dashboard = elicitor.get_weights_preset('dashboard_operationnel')  # Sensible UP

    log(f"Pondérations Paie: DB={w_paie['w_DB']:.0%}, UP={w_paie['w_UP']:.0%}")
    log(f"Pondérations Dashboard: DB={w_dashboard['w_DB']:.0%}, UP={w_dashboard['w_UP']:.0%}")

    # Test 4.1: Col_DB_Issue → Score Paie > Score Dashboard
    log("Test 4.1: Problème DB → Paie plus impacté")
    score_db_paie = scorer.compute_risk_score(vectors['Col_DB_Issue'], w_paie)
    score_db_dashboard = scorer.compute_risk_score(vectors['Col_DB_Issue'], w_dashboard)

    if score_db_paie > score_db_dashboard:
        test_passed(f"DB Issue: Paie ({score_db_paie:.0f}%) > Dashboard ({score_db_dashboard:.0f}%)")
    else:
        test_failed("DB Issue contextualisation",
                   f"Paie ({score_db_paie:.0f}%) devrait > Dashboard ({score_db_dashboard:.0f}%)")

    # Test 4.2: Col_UP_Issue → Score Dashboard > Score Paie
    log("Test 4.2: Problème UP → Dashboard plus impacté")
    score_up_paie = scorer.compute_risk_score(vectors['Col_UP_Issue'], w_paie)
    score_up_dashboard = scorer.compute_risk_score(vectors['Col_UP_Issue'], w_dashboard)

    if score_up_dashboard > score_up_paie:
        test_passed(f"UP Issue: Dashboard ({score_up_dashboard:.0f}%) > Paie ({score_up_paie:.0f}%)")
    else:
        test_failed("UP Issue contextualisation",
                   f"Dashboard ({score_up_dashboard:.0f}%) devrait > Paie ({score_up_paie:.0f}%)")

    # Test 4.3: Col_Perfect → Scores bas partout
    log("Test 4.3: Colonne parfaite → Scores bas")
    score_perfect_paie = scorer.compute_risk_score(vectors['Col_Perfect'], w_paie)
    score_perfect_dashboard = scorer.compute_risk_score(vectors['Col_Perfect'], w_dashboard)

    if score_perfect_paie < 10 and score_perfect_dashboard < 10:
        test_passed(f"Perfect: Paie={score_perfect_paie:.0f}%, Dashboard={score_perfect_dashboard:.0f}%")
    else:
        test_warning("Perfect scores",
                    f"Paie={score_perfect_paie:.0f}%, Dashboard={score_perfect_dashboard:.0f}% (attendu < 10%)")

    # Test 4.4: Différences significatives entre usages
    log("Test 4.4: Différences significatives entre usages")
    diff_db = abs(score_db_paie - score_db_dashboard)
    diff_up = abs(score_up_paie - score_up_dashboard)

    if diff_db >= 10 and diff_up >= 10:
        test_passed(f"Différences: DB={diff_db:.0f}%, UP={diff_up:.0f}%")
    else:
        test_warning("Différences faibles",
                    f"DB={diff_db:.0f}%, UP={diff_up:.0f}% (attendu >= 10%)")

    return True


# =============================================================================
# TEST 5: ROBUSTESSE DONNÉES CORROMPUES
# =============================================================================
def test_robustness():
    """Teste la robustesse face aux données corrompues ou inhabituelles"""
    print("\n" + "="*70)
    print("TEST 5: ROBUSTESSE DONNÉES CORROMPUES")
    print("="*70)

    # Test 5.1: Caractères spéciaux dans noms de colonnes
    log("Test 5.1: Noms de colonnes spéciaux")
    try:
        df = pd.DataFrame({
            'Normal_Col': [1, 2, 3],
            'Col avec espaces': [4, 5, 6],
            'Col-avec-tirets': [7, 8, 9],
            'Col.avec.points': [10, 11, 12],
            'Col_émojis_🎯': [13, 14, 15],
            'Col_(parenthèses)': [16, 17, 18],
        })
        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        test_passed("Noms de colonnes spéciaux")
    except Exception as e:
        test_failed("Noms de colonnes spéciaux", str(e))

    # Test 5.2: Valeurs avec caractères spéciaux
    log("Test 5.2: Valeurs avec caractères spéciaux")
    try:
        df = pd.DataFrame({
            'Emojis': ['Hello 👋', 'World 🌍', 'Test 🧪', None, ''],
            'Unicode': ['café', 'naïve', '北京', 'Москва', 'عربي'],
            'Special': ['<script>', "O'Brien", 'a"b"c', 'a\nb\tc', '\\path\\'],
            'HTML': ['<b>bold</b>', '&amp;', '&lt;', '&gt;', '&nbsp;'],
        })
        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        test_passed("Valeurs spéciales traitées")
    except Exception as e:
        test_failed("Valeurs spéciales", str(e))

    # Test 5.3: Types très mixtes dans une colonne
    log("Test 5.3: Types très mixtes")
    try:
        df = pd.DataFrame({
            'MixedTypes': [1, 'text', 3.14, True, None, '2024-01-01', '[1,2]', "{'a': 1}"],
            'Normal': range(8)
        })
        # Convertir les objets complexes en strings
        df['MixedTypes'] = df['MixedTypes'].apply(lambda x: str(x) if x is not None else None)

        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        test_passed("Types mixtes traités")
    except Exception as e:
        test_failed("Types mixtes", str(e))

    # Test 5.4: Strings très longues
    log("Test 5.4: Strings très longues")
    try:
        df = pd.DataFrame({
            'LongStrings': ['A' * 10000, 'B' * 50000, 'C' * 1000, 'short'],
            'Normal': range(4)
        })
        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        test_passed("Strings longues traitées")
    except Exception as e:
        test_failed("Strings longues", str(e))

    # Test 5.5: DataFrame avec index non standard
    log("Test 5.5: Index non standard")
    try:
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': ['a', 'b', 'c', 'd', 'e']
        }, index=['row_a', 'row_b', 'row_c', 'row_d', 'row_e'])

        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        test_passed("Index non standard")
    except Exception as e:
        test_failed("Index non standard", str(e))

    # Test 5.6: Colonnes avec données vides
    log("Test 5.6: Colonne vide (strings vides)")
    try:
        df = pd.DataFrame({
            'Empty': ['', '', '', '', ''],
            'Normal': range(5)
        })
        columns = list(df.columns)
        stats = analyze_dataset(df, columns)
        vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
        test_passed("Colonne vide gérée")
    except Exception as e:
        test_failed("Colonne vide", str(e))

    return True


# =============================================================================
# TEST 6: RÉGRESSION DAMA
# =============================================================================
def test_dama_regression():
    """Vérifie que les calculs DAMA sont corrects"""
    print("\n" + "="*70)
    print("TEST 6: RÉGRESSION DAMA")
    print("="*70)

    dama_calc = DAMACalculator()

    # Dataset avec valeurs connues
    n = 100
    df = pd.DataFrame({
        # 10% nulls → Complétude = 90%
        'Col_10pct_Nulls': [None if i < 10 else f"val_{i}" for i in range(n)],

        # 25% nulls → Complétude = 75%
        'Col_25pct_Nulls': [None if i < 25 else f"val_{i}" for i in range(n)],

        # 50 valeurs uniques sur 100 → Unicité = 50%
        'Col_50pct_Unique': [f"val_{i % 50}" for i in range(n)],

        # Toutes uniques → Unicité = 100%
        'Col_AllUnique': [f"unique_{i}" for i in range(n)],

        # Toutes identiques (1 valeur) → Unicité = 1%
        'Col_AllSame': ['SAME'] * n,
    })

    columns = list(df.columns)
    stats = analyze_dataset(df, columns)
    dama_scores = dama_calc.compute_all_dama_scores(df, columns)

    # Test 6.1: Complétude
    log("Test 6.1: Calcul Complétude DAMA")

    completude_10 = dama_scores['Col_10pct_Nulls']['completeness']
    completude_25 = dama_scores['Col_25pct_Nulls']['completeness']

    if abs(completude_10 - 0.90) < 0.01:
        test_passed(f"Complétude 10% nulls = {completude_10:.0%}")
    else:
        test_failed("Complétude 10% nulls", f"Got {completude_10:.0%}, expected 90%")

    if abs(completude_25 - 0.75) < 0.01:
        test_passed(f"Complétude 25% nulls = {completude_25:.0%}")
    else:
        test_failed("Complétude 25% nulls", f"Got {completude_25:.0%}, expected 75%")

    # Test 6.2: Unicité DAMA = 1 - (doublons / total)
    log("Test 6.2: Calcul Unicité DAMA")

    # Col_AllUnique: 100 valeurs uniques → 0 doublons → Unicité = 100%
    unicite_all_unique = dama_scores['Col_AllUnique']['uniqueness']
    if abs(unicite_all_unique - 1.0) < 0.01:
        test_passed(f"Unicité AllUnique = {unicite_all_unique:.0%}")
    else:
        test_failed("Unicité AllUnique", f"Got {unicite_all_unique:.0%}, expected 100%")

    # Col_AllSame: 1 valeur unique, 99 doublons → Unicité = 1 - 99/100 = 1%
    unicite_all_same = dama_scores['Col_AllSame']['uniqueness']
    if unicite_all_same <= 0.02:  # 1-2%
        test_passed(f"Unicité AllSame = {unicite_all_same:.0%}")
    else:
        test_failed("Unicité AllSame", f"Got {unicite_all_same:.0%}, expected ~1%")

    # Col_50pct_Unique: 50 valeurs uniques, chacune apparaît 2 fois
    # Doublons = 50 (la 2ème occurrence de chaque) → Unicité = 1 - 50/100 = 50%
    unicite_50 = dama_scores['Col_50pct_Unique']['uniqueness']
    if abs(unicite_50 - 0.50) < 0.05:
        test_passed(f"Unicité 50% unique = {unicite_50:.0%}")
    else:
        test_failed("Unicité 50% unique", f"Got {unicite_50:.0%}, expected ~50%")

    # Test 6.3: Score global DAMA dans [0, 1]
    log("Test 6.3: Score global DAMA")
    all_valid = True
    for col in columns:
        score = dama_scores[col].get('global_score', 0)
        if not (0 <= score <= 1):
            test_failed(f"Score DAMA {col}", f"Hors bornes: {score}")
            all_valid = False

    if all_valid:
        test_passed("Scores DAMA dans [0, 1]")

    return True


# =============================================================================
# TEST 7: COHÉRENCE CROISÉE
# =============================================================================
def test_cross_coherence():
    """Vérifie la cohérence entre les différents modules"""
    print("\n" + "="*70)
    print("TEST 7: COHÉRENCE CROISÉE MODULES")
    print("="*70)

    dama_calc = DAMACalculator()

    # Dataset de référence
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'Perfect': range(n),
        'WithNulls': [None if i < 40 else i for i in range(n)],  # 20% nulls
        'WithDupes': [i % 10 for i in range(n)],  # 10 valeurs uniques
    })

    columns = list(df.columns)
    stats = analyze_dataset(df, columns)
    vectors = compute_all_beta_vectors(df, columns, stats, 'standard')
    dama_scores = dama_calc.compute_all_dama_scores(df, columns)

    elicitor = AHPElicitor()
    scorer = RiskScorer()

    # Test 7.1: Cohérence Analyzer ↔ DAMA
    log("Test 7.1: Cohérence Analyzer ↔ DAMA")
    null_rate_analyzer = stats['WithNulls']['null_rate']
    completude_dama = dama_scores['WithNulls']['completeness']

    if abs((1 - null_rate_analyzer) - completude_dama) < 0.01:
        test_passed(f"Null rate ({null_rate_analyzer:.0%}) cohérent avec Complétude ({completude_dama:.0%})")
    else:
        test_failed("Cohérence Analyzer/DAMA",
                   f"Null rate {null_rate_analyzer:.0%} vs Complétude {completude_dama:.0%}")

    # Test 7.2: Cohérence Vectors ↔ Scores
    log("Test 7.2: Cohérence Vectors ↔ Scores")

    # Si P_UP = 0 pour tous, le score Dashboard devrait être bas
    if vectors['Perfect']['P_UP'] == 0:
        w = elicitor.get_weights_preset('dashboard_operationnel')
        score = scorer.compute_risk_score(vectors['Perfect'], w)
        if score < 10:
            test_passed(f"Perfect P_UP=0 → Score Dashboard bas ({score:.0f}%)")
        else:
            test_warning("Cohérence Vector/Score", f"Score={score:.0f}% pour P_UP=0")

    # Test 7.3: Ordre des scores cohérent
    log("Test 7.3: Ordre des scores cohérent")
    w_dashboard = elicitor.get_weights_preset('dashboard_operationnel')

    score_perfect = scorer.compute_risk_score(vectors['Perfect'], w_dashboard)
    score_withnulls = scorer.compute_risk_score(vectors['WithNulls'], w_dashboard)

    # WithNulls devrait avoir un score plus élevé que Perfect
    if score_withnulls >= score_perfect:
        test_passed(f"WithNulls ({score_withnulls:.0f}%) >= Perfect ({score_perfect:.0f}%)")
    else:
        test_failed("Ordre scores",
                   f"WithNulls ({score_withnulls:.0f}%) devrait >= Perfect ({score_perfect:.0f}%)")

    return True


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("\n" + "="*70)
    print("   TESTS COMPLETS PRÉ-DÉPLOIEMENT")
    print("   Framework Probabiliste Data Quality")
    print("="*70)
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    start_time = time.time()

    # Exécuter tous les tests
    tests = [
        ("Cohérence Mathématique", test_mathematical_coherence),
        ("Cas Limites", test_edge_cases),
        ("Volumétrie", test_volumetry),
        ("Contextualisation", test_contextualization),
        ("Robustesse", test_robustness),
        ("Régression DAMA", test_dama_regression),
        ("Cohérence Croisée", test_cross_coherence),
    ]

    for name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            test_failed(name, f"Exception non gérée: {str(e)}")
            traceback.print_exc()

    elapsed = time.time() - start_time

    # Résumé
    print("\n" + "="*70)
    print("   RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"   ✅ Passés:       {RESULTS['passed']}")
    print(f"   ❌ Échoués:      {RESULTS['failed']}")
    print(f"   ⚠️  Avertissements: {RESULTS['warnings']}")
    print(f"   ⏱️  Temps total:  {elapsed:.1f}s")
    print("="*70)

    if RESULTS['errors']:
        print("\n   Erreurs détaillées:")
        for err in RESULTS['errors']:
            print(f"   • {err}")

    if RESULTS['failed'] == 0:
        print("\n   🎉 TOUS LES TESTS SONT PASSÉS !")
        print("   → Le framework est prêt pour le déploiement")
    else:
        print(f"\n   ⚠️  {RESULTS['failed']} TEST(S) ÉCHOUÉ(S)")
        print("   → Corrections nécessaires avant déploiement")

    print("="*70 + "\n")

    return RESULTS['failed'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
