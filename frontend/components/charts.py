"""
Constructeurs de graphiques Plotly pour le Framework DQ.

Tous les graphiques utilisent le theme sombre (plotly_dark) avec
fond transparent pour s'integrer au CSS de l'application.
"""

import plotly.graph_objects as go
from frontend.components.theme import get_risk_color


def create_vector_chart(v):
    """Cree un graphique en barres du vecteur 4D pour un attribut.

    Chaque barre represente une dimension (DB, DP, BR, UP) coloree
    selon le niveau de risque via get_risk_color().

    Args:
        v: Dict avec les cles P_DB, P_DP, P_BR, P_UP (valeurs 0-1).

    Returns:
        go.Figure: Graphique Plotly.
    """
    dims = ["DB", "DP", "BR", "UP"]
    dim_labels = ["Structure", "Traitements", "Regles Metier", "Utilisabilite"]
    vals = [v.get(f"P_{d}", 0) * 100 for d in dims]

    fig = go.Figure(data=[go.Bar(
        x=dim_labels,
        y=vals,
        marker=dict(
            color=[get_risk_color(x / 100) for x in vals],
            line=dict(width=0),
            opacity=0.9
        ),
        text=[f"{x:.1f}%" for x in vals],
        textposition="outside",
        textfont=dict(color="white", size=14, family="Inter"),
        hovertemplate="<b>%{x}</b><br>Probabilité: %{y:.1f}%<extra></extra>"
    )])

    fig.update_layout(
        title=dict(
            text="Vecteur de Risque 4D",
            font=dict(size=18, color="white", family="Inter")
        ),
        height=380,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=dict(text="Probabilité (%)", font=dict(color="rgba(255,255,255,0.7)"))
        ),
        hoverlabel=dict(
            bgcolor="rgba(26,26,46,0.95)",
            font_size=14,
            font_family="Inter"
        )
    )
    return fig


def create_heatmap(scores):
    """Cree une heatmap [Attribut x Usage] des scores de risque.

    Les cles de scores suivent le format "attribut_usage".
    La matrice est construite en parsant ces cles.

    Args:
        scores: Dict[str, float] - scores par couple attribut_usage.

    Returns:
        go.Figure: Heatmap Plotly.
    """
    # Parser les cles "attribut_usage" pour extraire les axes
    attrs, usages = set(), set()
    for k in scores.keys():
        p = k.rsplit("_", 1)
        if len(p) == 2:
            attrs.add(p[0])
            usages.add(p[1])

    attrs, usages = sorted(attrs), sorted(usages)
    matrix = [[float(scores.get(f"{a}_{u}", 0)) * 100 for u in usages] for a in attrs]

    # Palette alignee sur les seuils de risque (0%=vert -> 100%=rouge)
    custom_colorscale = [
        [0.0, "#38ef7d"],
        [0.25, "#F2C94C"],
        [0.5, "#F2994A"],
        [0.75, "#f45c43"],
        [1.0, "#eb3349"]
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=usages,
        y=attrs,
        colorscale=custom_colorscale,
        colorbar=dict(
            title=dict(text="Risque (%)", font=dict(color="white")),
            tickfont=dict(color="rgba(255,255,255,0.7)"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0
        ),
        text=[[f"{v:.1f}%" for v in r] for r in matrix],
        texttemplate="%{text}",
        textfont=dict(color="white", size=12, family="Inter"),
        hovertemplate="<b>%{y}</b> × %{x}<br>Risque: %{z:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="Matrice des Scores de Risque",
            font=dict(size=18, color="white", family="Inter")
        ),
        height=450,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=100, r=40, t=60, b=60),
        xaxis=dict(
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=dict(text="Profils d'Usage", font=dict(color="rgba(255,255,255,0.7)"))
        ),
        yaxis=dict(
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=dict(text="Attributs", font=dict(color="rgba(255,255,255,0.7)"))
        ),
        hoverlabel=dict(
            bgcolor="rgba(26,26,46,0.95)",
            font_size=14,
            font_family="Inter"
        )
    )
    return fig
