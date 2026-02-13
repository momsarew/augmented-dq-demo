"""Tab Accueil - Welcome page before analysis."""

import os
import streamlit as st


def render_home_tab():
    """Render the home/welcome tab."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        margin: 1.5rem 0;
    ">
        <div style="font-size: 3.5rem; margin-bottom: 0.75rem;">📊</div>
        <h2 style="color: white; margin-bottom: 0.75rem;">Bienvenue dans le Framework DQ</h2>
        <p style="color: rgba(255,255,255,0.7); font-size: 1.05rem; max-width: 600px; margin: 0 auto 1rem auto;">
            Analysez la qualité de vos données avec une approche probabiliste basée sur les distributions Beta.
        </p>
    <div style="
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin-top: 1.5rem;
    ">
        <div style="text-align: center;">
            <div style="font-size: 1.75rem;">1️⃣</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Upload dataset</p>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.75rem;">2️⃣</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Sélectionner colonnes</p>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.75rem;">3️⃣</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Lancer l'analyse</p>
        </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🚀 Ce que tu vas pouvoir faire")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background: rgba(102,126,234,0.1); border: 1px solid rgba(102,126,234,0.3); border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <div style="color: white; font-weight: 600;">Analyser</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">Scores de risque contextualisés par usage</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: rgba(118,75,162,0.1); border: 1px solid rgba(118,75,162,0.3); border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
            <div style="color: white; font-weight: 600;">Prioriser</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">Identifier les urgences à traiter</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background: rgba(56,239,125,0.1); border: 1px solid rgba(56,239,125,0.3); border-radius: 12px; padding: 1rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
            <div style="color: white; font-weight: 600;">Rapporter</div>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">Générer des rapports IA personnalisés</p>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **Consulte l'onglet ❓ Aide** pour comprendre la méthodologie en détail")

    st.markdown("---")
    if not st.session_state.get("anthropic_api_key"):
        st.warning("🔑 **Configure ta clé API** dans l'onglet ⚙️ Paramètres pour activer l'assistance IA")
    else:
        st.success("✅ **API configurée** - Toutes les fonctionnalités IA sont actives !")
