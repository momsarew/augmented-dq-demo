"""
Theme constants and color utilities.

Centralise les couleurs, seuils et constantes visuelles
pour eviter les duplications dans le code.
"""

# ---------------------------------------------------------------------------
# Couleurs de risque
# ---------------------------------------------------------------------------
RISK_COLORS = {
    "CRITIQUE": "#eb3349",
    "ELEVE": "#F2994A",
    "MOYEN": "#F2C94C",
    "FAIBLE": "#38ef7d",
}

# ---------------------------------------------------------------------------
# Couleurs des dimensions 4D
# ---------------------------------------------------------------------------
DIM_COLORS = {
    "DB": "#667eea",
    "DP": "#764ba2",
    "BR": "#f093fb",
    "UP": "#38ef7d",
}

DIM_LABELS = {
    "DB": "Database Integrity",
    "DP": "Data Processing",
    "BR": "Business Rules",
    "UP": "Usage Appropriateness",
}

# ---------------------------------------------------------------------------
# Seuils de risque
# ---------------------------------------------------------------------------
RISK_THRESHOLDS = {
    "CRITIQUE": 0.40,
    "ELEVE": 0.25,
    "MOYEN": 0.15,
    "ACCEPTABLE": 0.10,
}


def get_risk_color(s):
    """Couleur selon le score de risque."""
    if s >= RISK_THRESHOLDS["CRITIQUE"]:
        return RISK_COLORS["CRITIQUE"]
    if s >= RISK_THRESHOLDS["ELEVE"]:
        return RISK_COLORS["ELEVE"]
    if s >= RISK_THRESHOLDS["MOYEN"]:
        return RISK_COLORS["MOYEN"]
    return RISK_COLORS["FAIBLE"]


def get_risk_level(s):
    """Niveau de risque selon le score."""
    if s >= RISK_THRESHOLDS["CRITIQUE"]:
        return "CRITIQUE"
    if s >= RISK_THRESHOLDS["ELEVE"]:
        return "ELEVE"
    if s >= RISK_THRESHOLDS["MOYEN"]:
        return "MOYEN"
    return "FAIBLE"
