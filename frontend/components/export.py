"""Utilitaires d'export Excel pour les resultats d'analyse.

Genere un fichier .xlsx horodate avec 3 feuilles :
Vecteurs (probabilites 4D), Scores (risque par attribut/usage),
et Priorites (top anomalies triees par score decroissant).
"""

from datetime import datetime

import pandas as pd


def export_excel(results):
    """Exporte les resultats d'analyse en fichier Excel multi-feuilles.

    Args:
        results: Dict contenant les cles vecteurs_4d, scores, top_priorities.

    Returns:
        str: Chemin du fichier Excel genere (resultats_YYYYMMDD_HHMMSS.xlsx).
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"resultats_{ts}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        # Feuille 1 : Vecteurs 4D (P_DB, P_DP, P_BR, P_UP par attribut)
        pd.DataFrame([
            {**{"Attribut": k}, **{f"P_{d}": v.get(f"P_{d}", 0) for d in ["DB", "DP", "BR", "UP"]}}
            for k, v in results.get("vecteurs_4d", {}).items()
        ]).to_excel(w, sheet_name="Vecteurs", index=False)

        # Feuille 2 : Scores de risque par couple (attribut, usage)
        pd.DataFrame([
            {
                "Attribut": k.rsplit("_", 1)[0] if "_" in k else k,
                "Usage": k.rsplit("_", 1)[1] if "_" in k else "N/A",
                "Score": float(v),
            }
            for k, v in results.get("scores", {}).items()
        ]).to_excel(w, sheet_name="Scores", index=False)

        # Feuille 3 : Top priorites triees par criticite
        pd.DataFrame(results.get("top_priorities", [])).to_excel(w, sheet_name="Priorites", index=False)
    return out
