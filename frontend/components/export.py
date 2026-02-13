"""Excel export utilities."""

from datetime import datetime

import pandas as pd


def export_excel(results):
    """Export analysis results to a multi-sheet Excel file."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"resultats_{ts}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        pd.DataFrame([
            {**{"Attribut": k}, **{f"P_{d}": v.get(f"P_{d}", 0) for d in ["DB", "DP", "BR", "UP"]}}
            for k, v in results.get("vecteurs_4d", {}).items()
        ]).to_excel(w, sheet_name="Vecteurs", index=False)

        pd.DataFrame([
            {"Attribut": k.rsplit("_", 1)[0], "Usage": k.rsplit("_", 1)[1] if "_" in k else "Usage", "Score": float(v)}
            for k, v in results.get("scores", {}).items()
        ]).to_excel(w, sheet_name="Scores", index=False)

        pd.DataFrame(results.get("top_priorities", [])).to_excel(w, sheet_name="Priorites", index=False)
    return out
