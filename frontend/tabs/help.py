"""Tab Aide - User guide."""

import streamlit as st


def render_help_tab(full=True):
    """Render the help/guide tab.

    Args:
        full: If True, render the full help (post-analysis). If False, render compact help.
    """
    st.header("❓ Guide Utilisateur")

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">🎯 En 30 secondes : C'est quoi ?</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 1.1rem;">
            Un outil qui mesure la qualité de vos données <strong>ET leur impact selon l'usage</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # DAMA vs Probabiliste comparison
    st.subheader("📊 DAMA classique vs Notre approche")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: rgba(235,51,73,0.1); border: 1px solid rgba(235,51,73,0.3); border-radius: 12px; padding: 1rem;">
            <h4 style="color: #eb3349; margin: 0 0 0.5rem 0;">❌ Approche DAMA classique</h4>
            <p style="color: rgba(255,255,255,0.7); margin: 0;">Score unique : "82% de qualité"</p>
            <p style="color: rgba(255,255,255,0.5); margin: 0.5rem 0 0 0; font-size: 0.9rem;">→ Même donnée = même note partout</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: rgba(56,239,125,0.1); border: 1px solid rgba(56,239,125,0.3); border-radius: 12px; padding: 1rem;">
            <h4 style="color: #38ef7d; margin: 0 0 0.5rem 0;">✅ Notre approche probabiliste</h4>
            <p style="color: rgba(255,255,255,0.7); margin: 0;">Score contextualisé : "46% Paie, 12% Dashboard"</p>
            <p style="color: rgba(255,255,255,0.5); margin: 0.5rem 0 0 0; font-size: 0.9rem;">→ Même donnée = risques différents selon l'usage</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 4 dimensions
    st.subheader("🧠 Les 4 dimensions du risque")

    if full:
        st.markdown("""
        <p style="color: rgba(255,255,255,0.7); margin-bottom: 1rem;">
            Chaque attribut est analysé sur <strong>4 dimensions causales</strong> :
        </p>
        """, unsafe_allow_html=True)

    dims_help = [
        {"code": "DB", "nom": "Structure", "icon": "🗄️", "question": "Le format/type est-il correct ?" if full else "Format/type correct ?", "exemple": "VARCHAR au lieu de NUMBER", "color": "#667eea"},
        {"code": "DP", "nom": "Traitements", "icon": "⚙️", "question": "Les ETL ont-ils dégradé la donnée ?" if full else "ETL ont dégradé ?", "exemple": "Troncature, encodage cassé", "color": "#764ba2"},
        {"code": "BR", "nom": "Règles métier", "icon": "📋", "question": "La valeur respecte-t-elle les règles ?" if full else "Respecte les règles ?", "exemple": "Salaire négatif, date future", "color": "#f093fb"},
        {"code": "UP", "nom": "Utilisabilité", "icon": "👁️", "question": "La donnée est-elle exploitable ?" if full else "Exploitable ?", "exemple": "Trop de valeurs manquantes", "color": "#38ef7d"},
    ]

    cols = st.columns(4)
    for i, dim in enumerate(dims_help):
        with cols[i]:
            if full:
                st.markdown(f"""
                <div style="
                    background: rgba(255,255,255,0.03);
                    border: 1px solid {dim['color']}40;
                    border-radius: 12px;
                    padding: 1rem;
                    text-align: center;
                    height: 200px;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{dim['icon']}</div>
                    <div style="color: {dim['color']}; font-weight: 600; font-size: 1.1rem;">{dim['code']} - {dim['nom']}</div>
                    <p style="color: rgba(255,255,255,0.7); font-size: 0.85rem; margin: 0.5rem 0;">{dim['question']}</p>
                    <p style="color: rgba(255,255,255,0.5); font-size: 0.75rem; font-style: italic;">Ex: {dim['exemple']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border: 1px solid {dim['color']}40; border-radius: 12px; padding: 0.75rem; text-align: center;">
                    <div style="font-size: 1.5rem;">{dim['icon']}</div>
                    <div style="color: {dim['color']}; font-weight: 600;">{dim['code']} - {dim['nom']}</div>
                    <p style="color: rgba(255,255,255,0.6); font-size: 0.8rem; margin: 0.25rem 0 0 0;">{dim['question']}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    if full:
        # Weight explanation
        st.subheader("⚖️ Pourquoi les pondérations changent tout")
        st.markdown("""
        <p style="color: rgba(255,255,255,0.7);">
            Le <strong>même attribut</strong> a des risques différents selon l'usage car les pondérations varient :
        </p>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Usage | DB (Structure) | DP (Traitements) | BR (Règles) | UP (Utilisabilité) | Logique |
        |-------|----------------|------------------|-------------|--------------------| --------|
        | **Paie** | 40% | 30% | 20% | 10% | Structure critique (calculs légaux) |
        | **Dashboard** | 10% | 20% | 20% | 50% | Utilisabilité prime (affichage) |
        | **Audit** | 20% | 20% | 40% | 20% | Règles métier critiques (conformité) |
        """)

        st.info("💡 **Résultat** : Un attribut avec P_DB=80% aura un score de 40% pour la Paie mais seulement 19% pour un Dashboard !")
        st.markdown("---")

        # Tab overview
        st.subheader("📑 Les onglets en un coup d'œil")
        onglets_help = [
            {"icon": "🔍", "nom": "Scan", "desc": "Détecter les anomalies automatiquement", "quand": "Premier diagnostic"},
            {"icon": "📊", "nom": "Dashboard", "desc": "Vue globale, heatmap des risques", "quand": "Présentation COMEX"},
            {"icon": "🎯", "nom": "Vecteurs", "desc": "Détail des 4 dimensions par attribut", "quand": "Diagnostic technique"},
            {"icon": "⚠️", "nom": "Priorités", "desc": "Top 5 des urgences à traiter", "quand": "Plan d'action"},
            {"icon": "🎚️", "nom": "Élicitation", "desc": "Ajuster les pondérations par usage", "quand": "Personnalisation métier"},
            {"icon": "🔄", "nom": "Lineage", "desc": "Impact des transformations ETL", "quand": "Debug pipeline"},
            {"icon": "📈", "nom": "DAMA", "desc": "Comparaison avec approche classique", "quand": "Justification méthode"},
            {"icon": "📋", "nom": "Reporting", "desc": "Rapport personnalisé par profil", "quand": "Communication"},
        ]

        for i in range(0, len(onglets_help), 4):
            cols = st.columns(4)
            for j, col in enumerate(cols):
                if i + j < len(onglets_help):
                    o = onglets_help[i + j]
                    with col:
                        st.markdown(f"""
                        <div style="
                            background: rgba(255,255,255,0.03);
                            border: 1px solid rgba(255,255,255,0.1);
                            border-radius: 10px;
                            padding: 0.75rem;
                            margin-bottom: 0.5rem;
                        ">
                            <div style="font-size: 1.25rem;">{o['icon']} <strong>{o['nom']}</strong></div>
                            <p style="color: rgba(255,255,255,0.7); font-size: 0.8rem; margin: 0.25rem 0;">{o['desc']}</p>
                            <p style="color: rgba(255,255,255,0.5); font-size: 0.75rem; margin: 0;">→ {o['quand']}</p>
                        </div>
                        """, unsafe_allow_html=True)

        st.markdown("---")

        # 3 key insights
        st.subheader("🔑 Les 3 insights clés à retenir")
        cols = st.columns(3)
        insights = [
            {"num": "1", "titre": "UNE DONNÉE ≠ UN SCORE", "desc": "Le risque dépend de l'usage métier"},
            {"num": "2", "titre": "4 DIMENSIONS = DIAGNOSTIC", "desc": "Pas juste 'mauvaise qualité' mais 'pourquoi'"},
            {"num": "3", "titre": "PONDÉRATIONS = PRIORISATION", "desc": "Focus sur ce qui compte pour VOTRE usage"},
        ]

        for i, insight in enumerate(insights):
            with cols[i]:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                    border: 1px solid rgba(102, 126, 234, 0.3);
                    border-radius: 12px;
                    padding: 1.25rem;
                    text-align: center;
                ">
                    <div style="
                        background: linear-gradient(135deg, #667eea, #764ba2);
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 0.75rem auto;
                        font-size: 1.25rem;
                        font-weight: 700;
                        color: white;
                    ">{insight['num']}</div>
                    <div style="color: white; font-weight: 600; font-size: 0.95rem;">{insight['titre']}</div>
                    <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">{insight['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

    # Color code (both full and compact)
    st.subheader("🎨 Code couleur des risques")
    cols = st.columns(4)
    colors_help = [
        {"color": "#38ef7d", "label": "< 15%", "status": "Faible", "action": "Monitoring"},
        {"color": "#F2C94C", "label": "15-25%", "status": "Modéré", "action": "Surveillance"},
        {"color": "#F2994A", "label": "25-40%", "status": "Élevé", "action": "Action planifiée"},
        {"color": "#eb3349", "label": "> 40%", "status": "Critique", "action": "Action immédiate"},
    ]

    for i, c in enumerate(colors_help):
        with cols[i]:
            if full:
                st.markdown(f"""
                <div style="
                    background: {c['color']}20;
                    border: 2px solid {c['color']};
                    border-radius: 12px;
                    padding: 1rem;
                    text-align: center;
                ">
                    <div style="color: {c['color']}; font-size: 1.5rem; font-weight: 700;">{c['label']}</div>
                    <div style="color: white; font-weight: 600;">{c['status']}</div>
                    <div style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">{c['action']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: {c['color']}20; border: 2px solid {c['color']}; border-radius: 12px; padding: 0.75rem; text-align: center;">
                    <div style="color: {c['color']}; font-size: 1.25rem; font-weight: 700;">{c['label']}</div>
                    <div style="color: white; font-weight: 600;">{c['status']}</div>
                </div>
                """, unsafe_allow_html=True)

    if not full:
        st.info("💡 **Pour commencer** : Upload ton fichier dans la sidebar et lance l'analyse !")
