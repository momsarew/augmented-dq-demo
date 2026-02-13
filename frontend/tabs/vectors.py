"""Tab Vecteurs - 4D vector detail per attribute."""

import streamlit as st
from frontend.components.charts import create_vector_chart
from frontend.components.ai_explain import explain_with_ai


def render_vectors_tab(r):
    """Render the vectors tab."""
    st.header("🎯 Vecteurs 4D")

    for attr, vec in r["vecteurs_4d"].items():
        st.subheader(f"📌 {attr}")
        st.plotly_chart(create_vector_chart(vec), use_container_width=True, key=f"vec_{attr}")

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💬 Expliquer", key=f"v_{attr}"):
                exp = explain_with_ai("vector", {f"P_{d}": vec[f"P_{d}"] for d in ["DB", "DP", "BR", "UP"]}, f"v_{attr}", 400)
                st.session_state[f"v_{attr}_exp"] = exp
        with col2:
            if f"v_{attr}_exp" in st.session_state:
                st.info(st.session_state[f"v_{attr}_exp"])

        with st.expander("🔬 Détails Beta"):
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**DB**: Beta({vec['alpha_DB']:.1f}, {vec['beta_DB']:.1f})\nP={vec['P_DB']:.3f}")
            c2.markdown(f"**DP**: Beta({vec['alpha_DP']:.1f}, {vec['beta_DP']:.1f})\nP={vec['P_DP']:.3f}")
            c3.markdown(f"**BR**: Beta({vec['alpha_BR']:.1f}, {vec['beta_BR']:.1f})\nP={vec['P_BR']:.3f}")
            c4.markdown(f"**UP**: Beta({vec['alpha_UP']:.1f}, {vec['beta_UP']:.1f})\nP={vec['P_UP']:.3f}")

        st.markdown("---")
