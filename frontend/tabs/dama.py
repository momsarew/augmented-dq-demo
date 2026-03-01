"""Tab DAMA - DAMA dimensions comparison."""

import streamlit as st
import plotly.graph_objects as go
from frontend.components.ai_explain import explain_with_ai


def _get_score_color(score):
    """Retourne la couleur associee a un score DAMA (0-1).

    Seuils : >=0.8 vert, >=0.6 jaune, >=0.4 orange, <0.4 rouge.
    None renvoie gris (dimension non calculable).
    """
    if score is None:
        return "#6b7280"     # Gris : dimension non calculable
    if score >= 0.8:
        return "#38ef7d"     # Vert : bon
    if score >= 0.6:
        return "#F2C94C"     # Jaune : acceptable
    if score >= 0.4:
        return "#F2994A"     # Orange : a surveiller
    return "#eb3349"         # Rouge : critique


DIM_INFO = {
    "completeness": {"label": "Complétude", "icon": ":material/pie_chart:", "desc": "Donnees presentes vs attendues"},
    "consistency": {"label": "Cohérence", "icon": ":material/link:", "desc": "Uniformite entre sources"},
    "accuracy": {"label": "Exactitude", "icon": ":material/target:", "desc": "Conformite a la realite"},
    "timeliness": {"label": "Fraîcheur", "icon": ":material/schedule:", "desc": "Actualite des donnees"},
    "validity": {"label": "Validité", "icon": ":material/verified:", "desc": "Respect des regles metier"},
    "uniqueness": {"label": "Unicité", "icon": ":material/fingerprint:", "desc": "Donnees sans doublons"}
}


def render_dama_tab(r, sanitize_column_name):
    """Render the DAMA comparison tab."""
    st.header("Comparaison DAMA", anchor=False)

    comp = r.get("comparaison", {})
    if not comp:
        st.info("Aucune comparaison disponible")
        return

    dama_scores = comp.get("dama_scores", {})

    for attr_name, attr_data in dama_scores.items():
        safe_attr_name = sanitize_column_name(attr_name)
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="color: white; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;">
                {safe_attr_name}
            </h3>
        </div>
        """, unsafe_allow_html=True)

        score_global = attr_data.get("score_global", 0)
        dims_calc = attr_data.get("dimensions_calculables", 0)
        dims_total = attr_data.get("dimensions_total", 6)

        col_score, col_info = st.columns([1, 2])

        with col_score:
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score_global * 100,
                number={"suffix": "%", "font": {"size": 36, "color": "white"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.3)"},
                    "bar": {"color": _get_score_color(score_global)},
                    "bgcolor": "rgba(255,255,255,0.1)",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 40], "color": "rgba(235,51,73,0.2)"},
                        {"range": [40, 60], "color": "rgba(242,153,74,0.2)"},
                        {"range": [60, 80], "color": "rgba(242,201,76,0.2)"},
                        {"range": [80, 100], "color": "rgba(56,239,125,0.2)"}
                    ]
                },
                title={"text": "Score Global", "font": {"size": 14, "color": "rgba(255,255,255,0.7)"}}
            ))
            fig_gauge.update_layout(
                height=200,
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{attr_name}")

        with col_info:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            ">
                <p style="color: rgba(255,255,255,0.6); margin: 0; font-size: 0.85rem;">Dimensions analysables</p>
                <p style="color: white; margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: 600;">
                    {dims_calc} <span style="color: rgba(255,255,255,0.5); font-size: 1rem;">/ {dims_total}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

            note = attr_data.get("note", "")
            if note:
                st.caption(f"{note}")

        st.markdown("<p style='color: rgba(255,255,255,0.7); margin: 1rem 0 0.5rem 0; font-weight: 500;'>Dimensions DAMA</p>", unsafe_allow_html=True)

        cols = st.columns(3)
        dims_list = ["completeness", "consistency", "accuracy", "timeliness", "validity", "uniqueness"]

        for i, dim_key in enumerate(dims_list):
            with cols[i % 3]:
                dim_value = attr_data.get(dim_key)
                info = DIM_INFO.get(dim_key, {"label": dim_key, "icon": "", "desc": ""})

                if dim_value is None:
                    display_value = "N/A"
                    color = "#6b7280"
                    bg_color = "rgba(107, 114, 128, 0.1)"
                else:
                    if dim_value < 0.05 and dim_value > 0:
                        display_value = f"{dim_value:.1%}"
                    else:
                        display_value = f"{dim_value:.0%}"
                    color = _get_score_color(dim_value)
                    bg_color = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)"

                st.markdown(f"""
                <div style="
                    background: {bg_color};
                    border: 1px solid {color}40;
                    border-radius: 12px;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    text-align: center;
                ">
                    <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{info['icon']}</div>
                    <div style="color: rgba(255,255,255,0.7); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">{info['label']}</div>
                    <div style="color: {color}; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">{display_value}</div>
                    <div style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">{info['desc']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

    # Comparative chart
    if len(dama_scores) > 1:
        st.subheader("Vue Comparative")

        attr_names = list(dama_scores.keys())
        global_scores = [dama_scores[a].get("score_global", 0) * 100 for a in attr_names]

        fig_comp = go.Figure(data=[go.Bar(
            x=attr_names,
            y=global_scores,
            marker=dict(color=[_get_score_color(s / 100) for s in global_scores], opacity=0.9),
            text=[f"{s:.1f}%" for s in global_scores],
            textposition="outside",
            textfont=dict(color="white", size=12),
            hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}%<extra></extra>"
        )])

        fig_comp.update_layout(
            title=dict(text="Scores Globaux DAMA par Attribut", font=dict(size=16, color="white")),
            height=350,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickfont=dict(color="rgba(255,255,255,0.7)")),
            yaxis=dict(tickfont=dict(color="rgba(255,255,255,0.7)"), gridcolor="rgba(255,255,255,0.1)", title=dict(text="Score (%)", font=dict(color="rgba(255,255,255,0.7)"))),
            hoverlabel=dict(bgcolor="rgba(26,26,46,0.95)", font_size=13)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(":material/chat: Synthetiser", key="dama"):
            exp = explain_with_ai("dama", {"dama": comp.get("dama_scores"), "masked": len(comp.get("problemes_masques", []))}, "dama", 500)
            st.session_state.dama_exp = exp
    with col2:
        if "dama_exp" in st.session_state:
            st.success(st.session_state.dama_exp)
