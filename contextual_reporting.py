cat > contextual_reporting.py << 'EOF'
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Any, Callable, Tuple, List

import streamlit as st

from reporting_exports import export_report_pdf, export_report_excel, export_report_pptx


PROFILS = {
    "cfo": {"nom": "CFO (Chief Financial Officer)", "emoji": "💰", "focus": ["ROI", "Impact P&L", "Budget", "Risque financier"], "ton": "executif"},
    "data_engineer": {"nom": "Data Engineer / Développeur", "emoji": "🔧", "focus": ["Root cause", "Code", "Architecture", "Performance"], "ton": "technique"},
    "drh": {"nom": "DRH (Directeur Ressources Humaines)", "emoji": "👥", "focus": ["Conformité paie", "Impact social", "URSSAF", "CSE"], "ton": "business"},
    "auditeur": {"nom": "Auditeur / Compliance Officer", "emoji": "🔍", "focus": ["Traçabilité", "Conformité", "Preuves", "Contrôles"], "ton": "formel"},
    "gouvernance": {"nom": "Responsable Gouvernance Données", "emoji": "📊", "focus": ["KPIs", "Monitoring", "Processus", "Standards"], "ton": "professionnel"},
    "manager_ops": {"nom": "Manager Opérationnel", "emoji": "⚡", "focus": ["Actions rapides", "Impact métier", "Quick wins"], "ton": "pragmatique"},
}


def _risk_level(score: float) -> Tuple[str, str]:
    if score >= 0.60:
        return "⚫ BLOQUANT", "🔴"
    if score >= 0.40:
        return "🔴 CRITIQUE", "🔴"
    if score >= 0.25:
        return "🟡 SURVEILLÉ", "🟡"
    return "🟢 OK", "🟢"


def _get_interpretation_qualite(P: float) -> str:
    if P < 0.05:
        return "✅ EXCELLENT - Qualité optimale"
    if P < 0.10:
        return "✅ BON NIVEAU - Qualité satisfaisante"
    if P < 0.15:
        return "⚠️ À SURVEILLER - Attention requise"
    if P < 0.25:
        return "⚠️ PROBLÉMATIQUE - Action nécessaire"
    return "🚨 CRITIQUE - Intervention urgente"


def _dominant_dim(vecteur: Dict[str, Any]) -> str:
    P_DB = float(vecteur.get("P_DB", 0))
    P_DP = float(vecteur.get("P_DP", 0))
    P_BR = float(vecteur.get("P_BR", 0))
    P_UP = float(vecteur.get("P_UP", 0))
    return max([("DB", P_DB), ("DP", P_DP), ("BR", P_BR), ("UP", P_UP)], key=lambda x: x[1])[0]


def _safe_score(results: Dict[str, Any], attribut: str, usage: str) -> float:
    scores = results.get("scores", {}) or {}
    k = f"{attribut}_{usage}"
    if k in scores:
        return float(scores[k] or 0)
    best = 0.0
    for kk, vv in scores.items():
        if attribut in kk and usage in kk:
            best = max(best, float(vv or 0))
    return best


def generer_partie1_synthese_executive(results: Dict[str, Any], profil: str, attribut_focus: str, usage_focus: str) -> str:
    vecteur = results.get("vecteurs_4d", {}).get(attribut_focus, {}) or {}
    score = _safe_score(results, attribut_focus, usage_focus)

    P_DB = float(vecteur.get("P_DB", 0))
    P_DP = float(vecteur.get("P_DP", 0))
    P_BR = float(vecteur.get("P_BR", 0))
    P_UP = float(vecteur.get("P_UP", 0))

    dim_critique = _dominant_dim(vecteur)

    dim_labels = {"DB": "Structure (Base de données)", "DP": "Traitements (Transformations)", "BR": "Règles Métier (Cohérence)", "UP": "Utilisabilité (Exploitabilité)"}
    niveau_risque, _ = _risk_level(score)

    records_affected = 0
    for p in (results.get("top_priorities", []) or []):
        if p.get("attribut") == attribut_focus and p.get("usage") == usage_focus:
            try:
                records_affected = int(p.get("records_affected") or 0)
            except Exception:
                records_affected = 0
            break

    cout_mensuel = records_affected * 50
    cout_annuel = cout_mensuel * 12

    bar20 = "█" * int(score * 20) + "░" * (20 - int(score * 20))

    return f"""
╔═══════════════════════════════════════════════════════╗
║ RAPPORT QUALITÉ DONNÉES                              ║
╚═══════════════════════════════════════════════════════╝

**Incident** : {attribut_focus} - {score:.1%}
**Date** : {datetime.now().strftime("%Y-%m-%d")}
**Destinataire** : {PROFILS[profil]['nom']}

╔═══════════════════════════════════════════════════════╗
║ PARTIE 1 : SYNTHÈSE EXÉCUTIVE                        ║
║ Lecture : ~2 minutes                                  ║
╚═══════════════════════════════════════════════════════╝

## 🚨 SITUATION EN UN COUP D'ŒIL

**NIVEAU DE RISQUE**