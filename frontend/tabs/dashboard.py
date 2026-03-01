"""Tab Dashboard - Global quality overview."""

import streamlit as st
from frontend.components.charts import create_heatmap
from frontend.components.export import export_excel
from frontend.components.ai_explain import explain_with_ai


def render_dashboard_tab(r):
    """Render the dashboard tab."""
    st.header("Dashboard Qualite", anchor=False)

    if st.button(":material/download: Export Excel", type="primary"):
        try:
            out = export_excel(r)
            with open(out, "rb") as f:
                st.download_button(":material/download: Telecharger", f, out, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.success(f"{out}")
            try:
                from backend.audit_trail import get_audit_trail
                audit = get_audit_trail()
                audit.log_export("results_excel", out, "xlsx", rows=len(r.get("vecteurs_4d", {})))
            except Exception:
                pass
        except Exception as e:
            st.error(f"{e}")

    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Attributs", len(r["vecteurs_4d"]))
    c2.metric("Usages", len(r["weights"]))
    c3.metric("Risque max", f"{max(r['scores'].values()):.1%}")
    c4.metric("Alertes", len([s for s in r["scores"].values() if s > 0.4]))

    st.markdown("---")

    if r.get("scores"):
        st.plotly_chart(create_heatmap(r["scores"]), use_container_width=True)

    st.markdown("---")
    st.subheader("Assistance IA")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(":material/smart_toy: Analyser", key="dash"):
            exp = explain_with_ai("global", {"nb": len(r["vecteurs_4d"]), "max": max(r["scores"].values())}, "dash", 500)
            st.session_state.dash_exp = exp
    with col2:
        if "dash_exp" in st.session_state:
            st.info(st.session_state.dash_exp)
