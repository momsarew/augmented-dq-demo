"""Tab Profil de Risque - Risk appetite adjustment."""

import json
import streamlit as st


PROFILS_RISQUE = {
    "tres_prudent": {
        "nom": "🛡️ Très Prudent",
        "description": "Zéro tolérance aux risques. Idéal pour contextes réglementaires stricts (Paie, Audit).",
        "multiplicateur": 1.3,
        "seuils": {"critique": 0.30, "eleve": 0.20, "modere": 0.10}
    },
    "prudent": {
        "nom": "🔒 Prudent",
        "description": "Préférence pour la sécurité. Alertes précoces recommandées.",
        "multiplicateur": 1.15,
        "seuils": {"critique": 0.35, "eleve": 0.22, "modere": 0.12}
    },
    "equilibre": {
        "nom": "⚖️ Équilibré",
        "description": "Balance risque/efficacité. Profil par défaut recommandé.",
        "multiplicateur": 1.0,
        "seuils": {"critique": 0.40, "eleve": 0.25, "modere": 0.15}
    },
    "tolerant": {
        "nom": "🎯 Tolérant",
        "description": "Accepte certains risques pour plus d'agilité. Pour environnements flexibles.",
        "multiplicateur": 0.85,
        "seuils": {"critique": 0.50, "eleve": 0.35, "modere": 0.20}
    },
    "tres_tolerant": {
        "nom": "🚀 Très Tolérant",
        "description": "Focus sur l'essentiel uniquement. Pour POC ou environnements de test.",
        "multiplicateur": 0.70,
        "seuils": {"critique": 0.60, "eleve": 0.45, "modere": 0.30}
    }
}


def render_risk_profile_tab(r):
    """Render the risk profile tab."""
    st.header("🎭 Profil de Risque")

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">🎯 Qu'est-ce que c'est ?</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 1rem;">
            Ton <strong>profil de risque</strong> détermine comment les scores sont ajustés selon ton appétence au risque.
            Un profil <strong>prudent</strong> amplifiera les alertes, tandis qu'un profil <strong>tolérant</strong> les atténuera.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("1️⃣ Choisis ton profil")

    if "profil_risque" not in st.session_state:
        st.session_state.profil_risque = "equilibre"

    cols_profil = st.columns(5)
    for i, (key, profil) in enumerate(PROFILS_RISQUE.items()):
        with cols_profil[i]:
            is_selected = st.session_state.profil_risque == key
            border_color = "#667eea" if is_selected else "rgba(255,255,255,0.1)"
            bg_color = "rgba(102, 126, 234, 0.2)" if is_selected else "rgba(255,255,255,0.03)"

            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                min-height: 120px;
            ">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{profil['nom'].split()[0]}</div>
                <div style="color: white; font-weight: 600; font-size: 0.85rem;">{profil['nom'].split(maxsplit=1)[1]}</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 0.7rem; margin-top: 0.25rem;">×{profil['multiplicateur']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Sélectionner", key=f"profil_{key}", use_container_width=True):
                st.session_state.profil_risque = key
                try:
                    from backend.audit_trail import get_audit_trail
                    audit = get_audit_trail()
                    audit.log_profile_selection(
                        profile_name=profil['nom'],
                        profile_type=key,
                        weights={"multiplicateur": profil['multiplicateur']}
                    )
                except Exception:
                    pass
                st.rerun()

    profil_actuel = PROFILS_RISQUE[st.session_state.profil_risque]
    st.markdown("---")

    st.subheader(f"2️⃣ Ton profil : {profil_actuel['nom']}")
    st.info(f"📋 {profil_actuel['description']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔢 Multiplicateur de risque**")
        mult = profil_actuel['multiplicateur']
        if mult > 1:
            st.warning(f"Les scores sont **amplifiés** de {(mult - 1) * 100:.0f}%")
        elif mult < 1:
            st.success(f"Les scores sont **atténués** de {(1 - mult) * 100:.0f}%")
        else:
            st.info("Scores **non modifiés** (profil neutre)")

    with col2:
        st.markdown("**🚨 Seuils d'alerte ajustés**")
        seuils = profil_actuel['seuils']
        st.markdown(f"""
        | Niveau | Seuil |
        |--------|-------|
        | 🔴 Critique | ≥ {seuils['critique']:.0%} |
        | 🟠 Élevé | ≥ {seuils['eleve']:.0%} |
        | 🟡 Modéré | ≥ {seuils['modere']:.0%} |
        | 🟢 Faible | < {seuils['modere']:.0%} |
        """)

    st.markdown("---")

    st.subheader("3️⃣ Impact sur tes scores actuels")

    scores = r.get("scores", {})
    if scores:
        mult = profil_actuel['multiplicateur']
        seuils = profil_actuel['seuils']

        scores_ajustes = []
        for key, score in scores.items():
            score_ajuste = min(1.0, score * mult)
            parts = key.rsplit("_", 1)
            attr = parts[0] if len(parts) == 2 else key
            usage = parts[1] if len(parts) == 2 else "N/A"

            if score_ajuste >= seuils['critique']:
                niveau = "🔴 Critique"
            elif score_ajuste >= seuils['eleve']:
                niveau = "🟠 Élevé"
            elif score_ajuste >= seuils['modere']:
                niveau = "🟡 Modéré"
            else:
                niveau = "🟢 Faible"

            scores_ajustes.append({
                "attribut": attr,
                "usage": usage,
                "score_original": score,
                "score_ajuste": score_ajuste,
                "niveau": niveau,
            })

        scores_ajustes.sort(key=lambda x: x["score_ajuste"], reverse=True)

        st.markdown("| Attribut | Usage | Score Original | Score Ajusté | Niveau |")
        st.markdown("|----------|-------|----------------|--------------|--------|")
        for s in scores_ajustes[:10]:
            st.markdown(f"| {s['attribut']} | {s['usage']} | {s['score_original']:.1%} | **{s['score_ajuste']:.1%}** | {s['niveau']} |")

        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        nb_critique = len([s for s in scores_ajustes if "Critique" in s['niveau']])
        nb_eleve = len([s for s in scores_ajustes if "Élevé" in s['niveau']])
        nb_modere = len([s for s in scores_ajustes if "Modéré" in s['niveau']])
        nb_faible = len([s for s in scores_ajustes if "Faible" in s['niveau']])

        col1.metric("🔴 Critiques", nb_critique)
        col2.metric("🟠 Élevés", nb_eleve)
        col3.metric("🟡 Modérés", nb_modere)
        col4.metric("🟢 Faibles", nb_faible)

        st.session_state.scores_ajustes = {f"{s['attribut']}_{s['usage']}": s['score_ajuste'] for s in scores_ajustes}
        st.session_state.seuils_profil = seuils

    else:
        st.warning("Aucun score disponible")

    # AI recommendations
    st.markdown("---")
    if st.button("🤖 Obtenir recommandations IA selon mon profil", type="primary"):
        if st.session_state.get("anthropic_api_key"):
            with st.spinner("🤖 Analyse en cours..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)

                    prompt_data = {
                        "profil_risque": profil_actuel['nom'],
                        "multiplicateur": mult,
                        "seuils": seuils,
                        "nb_critiques": nb_critique,
                        "nb_eleves": nb_eleve,
                        "top_3_risques": scores_ajustes[:3]
                    }

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=800,
                        system=f"""Tu es expert en gestion des risques data. L'utilisateur a un profil {profil_actuel['nom']}.

Donne des recommandations personnalisées en 4 parties :
1. **Cohérence profil** : Ce profil est-il adapté à leur situation ? (2 phrases)
2. **Actions prioritaires** : 3 actions concrètes selon leur profil de risque
3. **Ajustements suggérés** : Devraient-ils modifier leur appétence au risque ?
4. **KPIs à surveiller** : 3 indicateurs clés pour ce profil

Utilise les données JSON fournies. Sois concis et actionnable.""",
                        messages=[{"role": "user", "content": f"Données : {json.dumps(prompt_data, ensure_ascii=False)}"}]
                    )

                    st.session_state.ai_tokens_used += response.usage.input_tokens + response.usage.output_tokens
                    st.session_state.profil_risque_reco = response.content[0].text
                except Exception as e:
                    st.error(f"❌ Erreur IA : {e}")
        else:
            st.warning("⚠️ Configure ta clé API dans l'onglet ⚙️ Paramètres")

    if "profil_risque_reco" in st.session_state:
        with st.expander("💡 Recommandations IA personnalisées", expanded=True):
            st.markdown(st.session_state.profil_risque_reco)
