"""Tab Lineage - ETL propagation simulation."""

import streamlit as st
from frontend.components.ai_explain import explain_with_ai


def render_lineage_tab(r):
    """Render the lineage tab."""
    st.header("Propagation Lineage", anchor=False)

    lineage = r.get("lineage")
    if lineage:
        c1, c2 = st.columns(2)
        c1.metric("Risque source", f"{lineage.get('risk_source', 0):.1%}")
        c2.metric("Risque final", f"{lineage.get('risk_final', 0):.1%}")

        st.markdown("---")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(":material/chat: Analyser Propagation", key="lineage"):
                exp = explain_with_ai("lineage", {"risk_source": lineage.get("risk_source"), "risk_final": lineage.get("risk_final")}, "lineage", 450)
                st.session_state.lineage_exp = exp
        with col2:
            if "lineage_exp" in st.session_state:
                st.info(st.session_state.lineage_exp)
    else:
        st.info("Aucune simulation disponible")
