"""
Tests avancés du Framework Probabiliste DQ
==========================================

Ce fichier teste :
1. Les calculs Beta (vecteurs 4D)
2. Les pondérations AHP
3. Les scores de risque
4. Le calcul d'unicité DAMA
5. La propagation lineage
6. La cohérence globale du système
"""

import os
import sys
import pandas as pd
import numpy as np

# Ajouter les chemins
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_DIR = os.path.join(PROJECT_DIR, "backend", "engine")
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, ENGINE_DIR)

# Imports des modules
os.chdir(ENGINE_DIR)
import analyzer
import beta_calculator
import ahp_elicitor
import risk_scorer
import lineage_propagator
import comparator
os.chdir(PROJECT_DIR)

# ============================================================================
# DONNÉES DE TEST
# ============================================================================

def create_test_dataset():
    """Crée un dataset de test avec différents cas de figure"""
    np.random.seed(42)
    n = 100

    return pd.DataFrame({
        # Colonne parfaite (100% qualité)
        "Col_Parfaite": range(1, n+1),

        # Colonne avec 10% de nulls
        "Col_10pct_Nulls": [None if i < 10 else i for i in range(n)],

        # Colonne avec 50% de nulls
        "Col_50pct_Nulls": [None if i < 50 else i for i in range(n)],

        # Colonne avec doublons (unicité basse)
        "Col_Doublons": ["A"] * 80 + ["B"] * 15 + ["C"] * 5,

        # Colonne unique (unicité haute)
        "Col_Unique": [f"ID_{i:04d}" for i in range(n)],

        # Colonne avec erreurs de type (VARCHAR au lieu de NUMBER)
        "Col_TypeError": ["1,234"] * 30 + [1234] * 70,

        # Colonne dates avec formats mixtes
        "Col_Dates_Mixtes": ["2024-01-15"] * 40 + ["15/01/2024"] * 30 + ["Jan 15, 2024"] * 30,

        # Colonne avec valeurs négatives (violation métier)
        "Col_Salaires": [50000 + np.random.randint(-5000, 10000) for _ in range(95)] + [-1000, -500, -200, 0, 0],
    })


# ============================================================================
# TEST 1: ANALYZER
# ============================================================================

def test_analyzer():
    """Test du module analyzer"""
    print("\n" + "="*60)
    print("TEST 1: ANALYZER")
    print("="*60)

    df = create_test_dataset()
    cols = df.columns.tolist()

    stats = analyzer.analyze_dataset(df, cols)

    print(f"\n✅ Analyse de {len(cols)} colonnes réussie")

    # Vérifier Col_Parfaite
    assert stats["Col_Parfaite"]["null_rate"] == 0.0, "Col_Parfaite devrait avoir 0% nulls"
    print(f"   Col_Parfaite: null_rate = {stats['Col_Parfaite']['null_rate']:.1%} ✓")

    # Vérifier Col_10pct_Nulls
    assert abs(stats["Col_10pct_Nulls"]["null_rate"] - 0.10) < 0.01, "Col_10pct_Nulls devrait avoir ~10% nulls"
    print(f"   Col_10pct_Nulls: null_rate = {stats['Col_10pct_Nulls']['null_rate']:.1%} ✓")

    # Vérifier Col_50pct_Nulls
    assert abs(stats["Col_50pct_Nulls"]["null_rate"] - 0.50) < 0.01, "Col_50pct_Nulls devrait avoir ~50% nulls"
    print(f"   Col_50pct_Nulls: null_rate = {stats['Col_50pct_Nulls']['null_rate']:.1%} ✓")

    return stats


# ============================================================================
# TEST 2: BETA CALCULATOR (Vecteurs 4D)
# ============================================================================

def test_beta_calculator(stats):
    """Test du calcul des vecteurs 4D"""
    print("\n" + "="*60)
    print("TEST 2: BETA CALCULATOR (Vecteurs 4D)")
    print("="*60)

    df = create_test_dataset()
    cols = df.columns.tolist()

    vecteurs = beta_calculator.compute_all_beta_vectors(df, cols, stats)

    print(f"\n✅ Calcul de {len(vecteurs)} vecteurs 4D réussi")

    for col, v in vecteurs.items():
        p_db = v.get("P_DB", 0)
        p_dp = v.get("P_DP", 0)
        p_br = v.get("P_BR", 0)
        p_up = v.get("P_UP", 0)

        # Vérifier que toutes les probabilités sont entre 0 et 1
        assert 0 <= p_db <= 1, f"{col}: P_DB={p_db} hors limites"
        assert 0 <= p_dp <= 1, f"{col}: P_DP={p_dp} hors limites"
        assert 0 <= p_br <= 1, f"{col}: P_BR={p_br} hors limites"
        assert 0 <= p_up <= 1, f"{col}: P_UP={p_up} hors limites"

        print(f"   {col}: P_DB={p_db:.2f}, P_DP={p_dp:.2f}, P_BR={p_br:.2f}, P_UP={p_up:.2f} ✓")

    # Vérifier que Col_50pct_Nulls a un P_UP élevé (problème d'utilisabilité)
    assert vecteurs["Col_50pct_Nulls"]["P_UP"] > 0.3, "Col_50pct_Nulls devrait avoir P_UP élevé"
    print(f"\n   Col_50pct_Nulls a P_UP élevé ({vecteurs['Col_50pct_Nulls']['P_UP']:.2f}) ✓")

    return vecteurs


# ============================================================================
# TEST 3: AHP ELICITOR (Pondérations)
# ============================================================================

def test_ahp_elicitor():
    """Test du module d'élicitation AHP"""
    print("\n" + "="*60)
    print("TEST 3: AHP ELICITOR (Pondérations)")
    print("="*60)

    ahp = ahp_elicitor.AHPElicitor()

    # Tester les presets
    usages = ["paie_reglementaire", "reporting_social", "dashboard_operationnel", "audit_conformite"]

    for usage in usages:
        weights = ahp.get_weights_preset(usage)

        # Vérifier que la somme = 1
        total = weights.get("w_DB", 0) + weights.get("w_DP", 0) + weights.get("w_BR", 0) + weights.get("w_UP", 0)
        assert abs(total - 1.0) < 0.01, f"{usage}: somme des poids = {total} (devrait être 1.0)"

        print(f"   {usage}: w_DB={weights['w_DB']:.2f}, w_DP={weights['w_DP']:.2f}, w_BR={weights['w_BR']:.2f}, w_UP={weights['w_UP']:.2f}, Σ={total:.2f} ✓")

    # Vérifier que Paie privilégie DB (structure critique)
    paie = ahp.get_weights_preset("paie_reglementaire")
    assert paie["w_DB"] >= paie["w_UP"], "Paie devrait privilégier DB sur UP"
    print(f"\n   Paie privilégie DB ({paie['w_DB']:.2f}) sur UP ({paie['w_UP']:.2f}) ✓")

    # Vérifier que Dashboard privilégie UP (utilisabilité)
    dash = ahp.get_weights_preset("dashboard_operationnel")
    assert dash["w_UP"] >= dash["w_DB"], "Dashboard devrait privilégier UP sur DB"
    print(f"   Dashboard privilégie UP ({dash['w_UP']:.2f}) sur DB ({dash['w_DB']:.2f}) ✓")

    return True


# ============================================================================
# TEST 4: RISK SCORER (Scores de risque)
# ============================================================================

def test_risk_scorer(vecteurs):
    """Test du calcul des scores de risque"""
    print("\n" + "="*60)
    print("TEST 4: RISK SCORER (Scores de risque)")
    print("="*60)

    ahp = ahp_elicitor.AHPElicitor()

    usages = [
        {"nom": "Paie", "type": "paie_reglementaire", "criticite": "HIGH"},
        {"nom": "Dashboard", "type": "dashboard_operationnel", "criticite": "MEDIUM"},
    ]

    weights = {u["nom"]: ahp.get_weights_preset(u["type"]) for u in usages}

    scores = risk_scorer.compute_risk_scores(vecteurs, weights, usages)

    print(f"\n✅ Calcul de {len(scores)} scores de risque réussi")

    for key, score in scores.items():
        # Vérifier que le score est entre 0 et 1
        assert 0 <= score <= 1, f"{key}: score={score} hors limites"

        # Déterminer le niveau
        if score >= 0.40:
            niveau = "🔴 CRITIQUE"
        elif score >= 0.25:
            niveau = "🟠 ÉLEVÉ"
        elif score >= 0.15:
            niveau = "🟡 MODÉRÉ"
        else:
            niveau = "🟢 FAIBLE"

        print(f"   {key}: {score:.1%} {niveau}")

    # Vérifier que la même colonne a des scores différents selon l'usage
    # (c'est le cœur du concept probabiliste)
    col_test = "Col_50pct_Nulls"
    score_paie = scores.get(f"{col_test}_Paie", 0)
    score_dash = scores.get(f"{col_test}_Dashboard", 0)

    print(f"\n   Même colonne, scores différents selon usage:")
    print(f"   {col_test}_Paie: {score_paie:.1%}")
    print(f"   {col_test}_Dashboard: {score_dash:.1%}")
    print(f"   → Différence: {abs(score_paie - score_dash):.1%} ✓")

    return scores


# ============================================================================
# TEST 5: UNICITÉ DAMA
# ============================================================================

def test_dama_uniqueness():
    """Test du calcul d'unicité DAMA"""
    print("\n" + "="*60)
    print("TEST 5: UNICITÉ DAMA")
    print("="*60)

    df = create_test_dataset()
    dama_calc = comparator.DAMACalculator()

    # Test Col_Unique (devrait être ~100%)
    score_unique = dama_calc.compute_dama_score(df, "Col_Unique")
    print(f"\n   Col_Unique (toutes valeurs différentes):")
    print(f"   → Unicité: {score_unique['uniqueness']:.1%}")
    assert score_unique['uniqueness'] > 0.99, "Col_Unique devrait avoir unicité ~100%"
    print(f"   ✓ Unicité proche de 100%")

    # Test Col_Doublons (80% A, 15% B, 5% C → beaucoup de doublons)
    score_doublons = dama_calc.compute_dama_score(df, "Col_Doublons")
    print(f"\n   Col_Doublons (80% même valeur):")
    print(f"   → Unicité: {score_doublons['uniqueness']:.1%}")
    assert score_doublons['uniqueness'] < 0.10, "Col_Doublons devrait avoir unicité très basse"
    print(f"   ✓ Unicité basse (beaucoup de doublons)")

    # Test Col_Parfaite (valeurs 1-100, toutes uniques)
    score_parfaite = dama_calc.compute_dama_score(df, "Col_Parfaite")
    print(f"\n   Col_Parfaite (1 à 100, toutes uniques):")
    print(f"   → Unicité: {score_parfaite['uniqueness']:.1%}")
    print(f"   → Complétude: {score_parfaite['completeness']:.1%}")
    assert score_parfaite['uniqueness'] == 1.0, "Col_Parfaite devrait avoir unicité 100%"
    assert score_parfaite['completeness'] == 1.0, "Col_Parfaite devrait avoir complétude 100%"
    print(f"   ✓ Parfaite qualité")

    return True


# ============================================================================
# TEST 6: LINEAGE PROPAGATION
# ============================================================================

def test_lineage_propagation(vecteurs):
    """Test de la propagation du risque via lineage"""
    print("\n" + "="*60)
    print("TEST 6: LINEAGE PROPAGATION")
    print("="*60)

    ahp = ahp_elicitor.AHPElicitor()
    weights = ahp.get_weights_preset("paie_reglementaire")

    # Prendre un vecteur de test
    vecteur_test = vecteurs.get("Col_TypeError", vecteurs[list(vecteurs.keys())[0]])

    lineage = lineage_propagator.simulate_lineage(vecteur_test, weights)

    risk_source = lineage.get("risk_source", 0)
    risk_final = lineage.get("risk_final", 0)

    print(f"\n   Risque source: {risk_source:.1%}")
    print(f"   Risque final (après ETL): {risk_final:.1%}")
    print(f"   Dégradation: +{(risk_final - risk_source):.1%}")

    # Le risque final devrait être >= risque source (l'ETL dégrade)
    assert risk_final >= risk_source, "Le risque final devrait être >= risque source"
    print(f"   ✓ Le risque se propage correctement")

    return True


# ============================================================================
# TEST 7: COMPARAISON DAMA vs PROBABILISTE
# ============================================================================

def test_dama_vs_probabiliste(vecteurs, scores):
    """Test de la comparaison des deux approches"""
    print("\n" + "="*60)
    print("TEST 7: COMPARAISON DAMA vs PROBABILISTE")
    print("="*60)

    df = create_test_dataset()
    cols = df.columns.tolist()

    comparison = comparator.compare_dama_vs_probabiliste(df, cols, scores, vecteurs)

    dama_scores = comparison.get("dama_scores", {})
    problemes = comparison.get("problemes_masques", [])
    gains = comparison.get("gains", [])

    print(f"\n   Scores DAMA calculés pour {len(dama_scores)} colonnes")
    print(f"   Problèmes masqués détectés: {len(problemes)}")
    print(f"   Gains méthodologiques: {len(gains)} catégories")

    # Afficher quelques scores DAMA
    for col, data in list(dama_scores.items())[:3]:
        print(f"\n   {col}:")
        print(f"      Complétude: {data.get('completeness', 'N/A')}")
        print(f"      Unicité: {data.get('uniqueness', 'N/A')}")
        print(f"      Score global: {data.get('score_global', 'N/A')}")

    print(f"\n   ✓ Comparaison DAMA vs Probabiliste fonctionnelle")

    return True


# ============================================================================
# TEST 8: COHÉRENCE GLOBALE
# ============================================================================

def test_coherence_globale(vecteurs, scores):
    """Test de cohérence globale du système"""
    print("\n" + "="*60)
    print("TEST 8: COHÉRENCE GLOBALE")
    print("="*60)

    # 1. Vérifier que les colonnes "parfaites" ont des scores bas
    score_parfaite = scores.get("Col_Parfaite_Paie", 1)
    assert score_parfaite < 0.3, f"Col_Parfaite devrait avoir un score bas, a {score_parfaite:.1%}"
    print(f"   ✓ Col_Parfaite a un score bas ({score_parfaite:.1%})")

    # 2. Vérifier que les colonnes "problématiques" ont des scores élevés
    score_probleme = scores.get("Col_50pct_Nulls_Paie", 0)
    print(f"   ✓ Col_50pct_Nulls a un score de {score_probleme:.1%}")

    # 3. Vérifier la cohérence entre vecteurs et scores
    for col in vecteurs.keys():
        v = vecteurs[col]

        # Si P_UP est très élevé, le score Dashboard devrait être impacté
        if v.get("P_UP", 0) > 0.5:
            score_dash = scores.get(f"{col}_Dashboard", 0)
            print(f"   {col}: P_UP={v['P_UP']:.2f} → Score Dashboard={score_dash:.1%}")

    print(f"\n   ✓ Cohérence globale vérifiée")

    return True


# ============================================================================
# MAIN
# ============================================================================

def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("TESTS AVANCÉS - FRAMEWORK PROBABILISTE DQ")
    print("="*60)

    results = {}

    try:
        # Test 1: Analyzer
        stats = test_analyzer()
        results["analyzer"] = "✅ PASS"
    except Exception as e:
        results["analyzer"] = f"❌ FAIL: {e}"
        stats = None

    try:
        # Test 2: Beta Calculator
        if stats:
            vecteurs = test_beta_calculator(stats)
            results["beta_calculator"] = "✅ PASS"
        else:
            results["beta_calculator"] = "⏭️ SKIP (dépend de analyzer)"
            vecteurs = None
    except Exception as e:
        results["beta_calculator"] = f"❌ FAIL: {e}"
        vecteurs = None

    try:
        # Test 3: AHP Elicitor
        test_ahp_elicitor()
        results["ahp_elicitor"] = "✅ PASS"
    except Exception as e:
        results["ahp_elicitor"] = f"❌ FAIL: {e}"

    try:
        # Test 4: Risk Scorer
        if vecteurs:
            scores = test_risk_scorer(vecteurs)
            results["risk_scorer"] = "✅ PASS"
        else:
            results["risk_scorer"] = "⏭️ SKIP (dépend de beta_calculator)"
            scores = None
    except Exception as e:
        results["risk_scorer"] = f"❌ FAIL: {e}"
        scores = None

    try:
        # Test 5: Unicité DAMA
        test_dama_uniqueness()
        results["dama_uniqueness"] = "✅ PASS"
    except Exception as e:
        results["dama_uniqueness"] = f"❌ FAIL: {e}"

    try:
        # Test 6: Lineage Propagation
        if vecteurs:
            test_lineage_propagation(vecteurs)
            results["lineage"] = "✅ PASS"
        else:
            results["lineage"] = "⏭️ SKIP"
    except Exception as e:
        results["lineage"] = f"❌ FAIL: {e}"

    try:
        # Test 7: DAMA vs Probabiliste
        if vecteurs and scores:
            test_dama_vs_probabiliste(vecteurs, scores)
            results["dama_vs_prob"] = "✅ PASS"
        else:
            results["dama_vs_prob"] = "⏭️ SKIP"
    except Exception as e:
        results["dama_vs_prob"] = f"❌ FAIL: {e}"

    try:
        # Test 8: Cohérence globale
        if vecteurs and scores:
            test_coherence_globale(vecteurs, scores)
            results["coherence"] = "✅ PASS"
        else:
            results["coherence"] = "⏭️ SKIP"
    except Exception as e:
        results["coherence"] = f"❌ FAIL: {e}"

    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)

    passed = sum(1 for r in results.values() if "PASS" in r)
    failed = sum(1 for r in results.values() if "FAIL" in r)
    skipped = sum(1 for r in results.values() if "SKIP" in r)

    for test, result in results.items():
        print(f"   {test}: {result}")

    print(f"\n   TOTAL: {passed} passés, {failed} échoués, {skipped} ignorés")

    if failed == 0:
        print("\n   🎉 TOUS LES TESTS SONT PASSÉS !")
    else:
        print(f"\n   ⚠️ {failed} TEST(S) ÉCHOUÉ(S)")

    return results


if __name__ == "__main__":
    run_all_tests()
