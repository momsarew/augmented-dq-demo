"""Theme constants and color utilities."""


def get_risk_color(s):
    """Couleurs modernes pour les niveaux de risque."""
    if s >= 0.40:
        return "#eb3349"   # Rouge
    if s >= 0.25:
        return "#F2994A"   # Orange
    if s >= 0.15:
        return "#F2C94C"   # Jaune
    return "#38ef7d"       # Vert
