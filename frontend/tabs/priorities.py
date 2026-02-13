"""Tab Priorités - Top risk priorities."""

import streamlit as st
from frontend.components.ai_explain import explain_with_ai


def render_priorities_tab(r):
    """Render the priorities tab."""
    st.header("⚠️ Top Priorités")

    for i, p in enumerate(r["top_priorities"], 1):
        emoji = "🚨" if p.get("severite") == "CRITIQUE" else "⚠️"
        st.markdown(f"### {emoji} #{i} - {p.get('attribut')} × {p.get('usage')}")
        st.markdown(f"**Risque** : {p.get('score', 0):.1%}")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💬 Analyser", key=f"p{i}"):
                exp = explain_with_ai("priority", {"score": p.get("score"), "sev": p.get("severite")}, f"p{i}", 500)
                st.session_state[f"p{i}_exp"] = exp
        with col2:
            if f"p{i}_exp" in st.session_state:
                st.warning(st.session_state[f"p{i}_exp"])

        st.markdown("---")
