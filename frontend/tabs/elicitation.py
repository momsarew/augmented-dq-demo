"""Tab Élicitation - AHP weight adjustment."""

import streamlit as st
import plotly.graph_objects as go
from frontend.components.ai_explain import explain_with_ai


def render_elicitation_tab(r):
    """Render the elicitation tab."""
    st.header("🎚️ Élicitation Pondérations AHP")
    st.info("Configure les pondérations pour chaque usage. Utilise les presets ou définis tes propres valeurs.")

    for usage_nom, weights in r.get("weights", {}).items():
        st.subheader(f"📌 {usage_nom}")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Ajuster pondérations** :")

            w_db = st.slider("DB (Structure)", 0.0, 1.0, float(weights.get("w_DB", 0.25)), 0.05, key=f"w_db_{usage_nom}")
            w_dp = st.slider("DP (Traitements)", 0.0, 1.0, float(weights.get("w_DP", 0.25)), 0.05, key=f"w_dp_{usage_nom}")
            w_br = st.slider("BR (Règles Métier)", 0.0, 1.0, float(weights.get("w_BR", 0.25)), 0.05, key=f"w_br_{usage_nom}")
            w_up = st.slider("UP (Utilisabilité)", 0.0, 1.0, float(weights.get("w_UP", 0.25)), 0.05, key=f"w_up_{usage_nom}")

            total = w_db + w_dp + w_br + w_up
            if total > 0:
                w_db_norm, w_dp_norm, w_br_norm, w_up_norm = w_db / total, w_dp / total, w_br / total, w_up / total
            else:
                w_db_norm = w_dp_norm = w_br_norm = w_up_norm = 0.25

            st.markdown("**Pondérations normalisées** :")
            st.json({"w_DB": f"{w_db_norm:.2%}", "w_DP": f"{w_dp_norm:.2%}", "w_BR": f"{w_br_norm:.2%}", "w_UP": f"{w_up_norm:.2%}"})

            if st.button(f"💾 Sauvegarder pour {usage_nom}", key=f"save_{usage_nom}"):
                new_weights = {"w_DB": w_db_norm, "w_DP": w_dp_norm, "w_BR": w_br_norm, "w_UP": w_up_norm}
                if "custom_weights" not in st.session_state:
                    st.session_state.custom_weights = {}
                st.session_state.custom_weights[usage_nom] = new_weights
                st.success(f"✅ Pondérations sauvegardées pour {usage_nom}. Relance analyse pour appliquer.")
                try:
                    from backend.audit_trail import get_audit_trail
                    audit = get_audit_trail()
                    audit.log_ahp_weights(usage_nom, new_weights)
                except Exception:
                    pass

        with col2:
            dim_labels = ["Structure", "Traitements", "Règles", "Utilisabilité"]
            fig = go.Figure(data=[go.Bar(
                x=dim_labels,
                y=[w_db_norm * 100, w_dp_norm * 100, w_br_norm * 100, w_up_norm * 100],
                marker=dict(
                    color=["#667eea", "#764ba2", "#f093fb", "#38ef7d"],
                    line=dict(width=0),
                    opacity=0.9
                ),
                text=[f"{x:.1f}%" for x in [w_db_norm * 100, w_dp_norm * 100, w_br_norm * 100, w_up_norm * 100]],
                textposition="outside",
                textfont=dict(color="white", size=12, family="Inter"),
                hovertemplate="<b>%{x}</b><br>Pondération: %{y:.1f}%<extra></extra>"
            )])
            fig.update_layout(
                title=dict(text=f"Pondérations {usage_nom}", font=dict(size=16, color="white", family="Inter")),
                height=320,
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=30, r=30, t=50, b=30),
                xaxis=dict(showgrid=False, tickfont=dict(color="rgba(255,255,255,0.7)", size=11)),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color="rgba(255,255,255,0.7)", size=11)),
                hoverlabel=dict(bgcolor="rgba(26,26,46,0.95)", font_size=13, font_family="Inter")
            )
            st.plotly_chart(fig, use_container_width=True, key=f"fig_{usage_nom}")

        st.markdown("---")
        col_btn, col_exp = st.columns([1, 4])
        with col_btn:
            if st.button("💬 Justifier", key=f"elicit_{usage_nom}"):
                exp = explain_with_ai("elicitation", {"usage": usage_nom, "weights": {"w_DB": w_db_norm, "w_DP": w_dp_norm, "w_BR": w_br_norm, "w_UP": w_up_norm}}, f"elicit_{usage_nom}", 500)
                st.session_state[f"elicit_{usage_nom}_exp"] = exp
        with col_exp:
            if f"elicit_{usage_nom}_exp" in st.session_state:
                st.info(st.session_state[f"elicit_{usage_nom}_exp"])

        st.markdown("---")
