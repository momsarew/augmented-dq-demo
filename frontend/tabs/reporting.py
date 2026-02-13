"""Tab Reporting - Contextual AI-generated reports."""

import json
from datetime import datetime

import streamlit as st


PROFILS = {
    "cfo": "💰 CFO (Chief Financial Officer)",
    "data_engineer": "🔧 Data Engineer / Développeur",
    "drh": "👥 DRH (Directeur Ressources Humaines)",
    "auditeur": "🔍 Auditeur / Compliance Officer",
    "gouvernance": "📊 Responsable Gouvernance Données",
    "manager_ops": "⚡ Manager Opérationnel",
    "custom": "✏️ Profil personnalisé..."
}


def render_reporting_tab(r, escape_html, sanitize_user_input):
    """Render the reporting tab."""
    st.header("📋 Restitution Adaptative")
    st.info("🎯 Rapport personnalisé selon TON profil métier")

    profils = dict(PROFILS)

    col1, col2 = st.columns(2)

    with col1:
        profil_select = st.selectbox("👤 Ton profil", options=list(profils.keys()), format_func=lambda x: profils[x], index=4)
        st.session_state.selected_profile = profil_select

        if profil_select == "custom":
            st.markdown("---")
            st.markdown("**📝 Définir ton profil personnalisé**")

            custom_titre_raw = st.text_input("Intitulé du poste", placeholder="Ex: Chief Data Officer, Analyste BI...", key="custom_profile_title", max_chars=100)
            custom_titre = sanitize_user_input(custom_titre_raw, max_length=100)

            custom_description_raw = st.text_area("Description du rôle", placeholder="Ex: Responsable de la stratégie data...", height=100, key="custom_profile_desc", max_chars=500)
            custom_description = sanitize_user_input(custom_description_raw, max_length=500, allow_newlines=True)

            custom_focus_raw = st.text_input("Focus principal", placeholder="Ex: ROI des projets data, conformité RGPD...", key="custom_profile_focus", max_chars=200)
            custom_focus = sanitize_user_input(custom_focus_raw, max_length=200)

            if custom_titre:
                profils["custom"] = f"✏️ {escape_html(custom_titre)}"

    with col2:
        attributs = list(r.get("vecteurs_4d", {}).keys())
        if attributs:
            attributs_focus = st.multiselect("📌 Attribut(s) à analyser", options=attributs, default=[attributs[0]] if attributs else [], help="Sélectionne un ou plusieurs attributs pour le rapport")
        else:
            st.warning("Aucun attribut analysé")
            attributs_focus = []

    usages_list = list(r.get("weights", {}).keys())
    if usages_list and attributs_focus:
        usage_focus = st.selectbox("🎯 Usage métier", options=usages_list)

        st.markdown("---")

        can_generate = True
        if profil_select == "custom":
            if not st.session_state.get("custom_profile_title"):
                st.warning("⚠️ Renseigne l'intitulé de ton profil personnalisé")
                can_generate = False

        st.info(f"📊 **{len(attributs_focus)} attribut(s) sélectionné(s)** pour le rapport")

        if st.button("📄 Générer Rapport Personnalisé", type="primary", use_container_width=True) and can_generate:
            with st.spinner("🤖 Claude génère ton rapport..."):
                try:
                    weights_data = r.get("weights", {}).get(usage_focus, {})
                    lineage_data = r.get("lineage", {})

                    if profil_select == "custom":
                        custom_titre = st.session_state.get("custom_profile_title", "Profil personnalisé")
                        custom_desc = st.session_state.get("custom_profile_desc", "")
                        custom_focus_input = st.session_state.get("custom_profile_focus", "")
                        profil_pour_prompt = f"✏️ {custom_titre}"
                        if custom_desc:
                            profil_pour_prompt += f"\nDescription : {custom_desc}"
                        if custom_focus_input:
                            profil_pour_prompt += f"\nFocus principal : {custom_focus_input}"
                    else:
                        profil_pour_prompt = profils[profil_select]

                    attributs_data = []
                    for attr in attributs_focus:
                        vecteur = r["vecteurs_4d"].get(attr, {})
                        score = r["scores"].get(f"{attr}_{usage_focus}", 0)

                        dama_data = {}
                        if r.get("comparaison") and r["comparaison"].get("dama_scores"):
                            dama_data = r["comparaison"]["dama_scores"].get(attr, {})

                        priorities_for_attr = [p for p in r.get("top_priorities", []) if p.get("attribut") == attr]

                        dims_values = [
                            ("DB (Structure données)", vecteur.get("P_DB", 0)),
                            ("DP (Traitements)", vecteur.get("P_DP", 0)),
                            ("BR (Règles métier)", vecteur.get("P_BR", 0)),
                            ("UP (Utilisabilité)", vecteur.get("P_UP", 0))
                        ]
                        dimension_critique = max(dims_values, key=lambda x: x[1])

                        attributs_data.append({
                            "attribut": attr,
                            "score_risque": round(float(score), 4),
                            "vecteur_4d": {
                                "P_DB_structure": round(vecteur.get("P_DB", 0), 4),
                                "P_DP_traitements": round(vecteur.get("P_DP", 0), 4),
                                "P_BR_regles_metier": round(vecteur.get("P_BR", 0), 4),
                                "P_UP_utilisabilite": round(vecteur.get("P_UP", 0), 4)
                            },
                            "dimension_critique": {"nom": dimension_critique[0], "valeur": round(dimension_critique[1], 4)},
                            "scores_dama": {
                                "completude": dama_data.get("completeness"),
                                "unicite": dama_data.get("uniqueness"),
                                "score_global_dama": dama_data.get("score_global")
                            },
                            "priorites": priorities_for_attr[:3] if priorities_for_attr else []
                        })

                    attributs_data.sort(key=lambda x: x["score_risque"], reverse=True)

                    scores_list = [a["score_risque"] for a in attributs_data]
                    attribut_plus_risque = attributs_data[0] if attributs_data else None

                    rapport_data = {
                        "profil": profil_pour_prompt,
                        "usage": usage_focus,
                        "nombre_attributs": len(attributs_focus),
                        "attributs_analyses": attributs_focus,
                        "resume_global": {
                            "score_moyen": round(sum(scores_list) / len(scores_list), 4) if scores_list else 0,
                            "score_max": round(max(scores_list), 4) if scores_list else 0,
                            "score_min": round(min(scores_list), 4) if scores_list else 0,
                            "attribut_plus_critique": attribut_plus_risque["attribut"] if attribut_plus_risque else None,
                            "nb_alertes_critiques": len([s for s in scores_list if s > 0.4])
                        },
                        "ponderations_usage": {
                            "w_DB": round(weights_data.get("w_DB", 0.25), 4),
                            "w_DP": round(weights_data.get("w_DP", 0.25), 4),
                            "w_BR": round(weights_data.get("w_BR", 0.25), 4),
                            "w_UP": round(weights_data.get("w_UP", 0.25), 4)
                        },
                        "detail_par_attribut": attributs_data,
                        "lineage": {
                            "risque_source": lineage_data.get("risk_source"),
                            "risque_final": lineage_data.get("risk_final")
                        } if lineage_data else None
                    }

                    import anthropic
                    client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)

                    nb_attrs = len(attributs_focus)
                    system_prompt = f"""Tu es expert Data Quality générant un rapport personnalisé.

RÈGLE ABSOLUE : Utilise UNIQUEMENT les données fournies ci-dessous. NE JAMAIS inventer, simuler ou extrapoler des chiffres. Si une donnée est NULL ou absente, indique "Non disponible".

Profil destinataire : {profil_pour_prompt}
Nombre d'attributs analysés : {nb_attrs}

Génère un rapport structuré en 3 parties en utilisant EXCLUSIVEMENT les données réelles fournies :

**PARTIE 1 : SYNTHÈSE EXÉCUTIVE (2 min lecture)**
- 🚨 Vue d'ensemble : {nb_attrs} attribut(s) analysé(s) pour l'usage "{usage_focus}"
- 📊 Tableau récapitulatif des scores de risque par attribut (du plus critique au moins critique)
- 💡 L'essentiel en 3-5 points (basé sur les données réelles)
- 🔴 Focus sur l'attribut le plus critique et pourquoi
- ✅ Top 3 actions prioritaires (basées sur les dimensions critiques réelles)

**PARTIE 2 : DÉTAILS PAR ATTRIBUT (5-10 min lecture)**
Pour chaque attribut analysé, affiche un bloc avec :
- Nom de l'attribut et son score de risque
- Tableau des 4 dimensions (P_DB, P_DP, P_BR, P_UP)
- Dimension la plus critique identifiée
- Scores DAMA (complétude, unicité si disponibles)
- Actions recommandées spécifiques

**PARTIE 3 : SYNTHÈSE & RECOMMANDATIONS PROFIL (3 min lecture)**
- 📊 KPIs globaux : score moyen, min, max, nb alertes critiques
- ⚖️ Pondérations utilisées pour l'usage "{usage_focus}"
- 💼 Impact business global basé sur les scores de risque réels
- 📈 Plan de monitoring et prochaines étapes
- 🎯 Recommandations spécifiques pour le profil {profil_pour_prompt}

Format : Markdown avec tableaux. Utilise UNIQUEMENT les chiffres fournis dans les données JSON."""

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2500,
                        system=system_prompt,
                        messages=[{"role": "user", "content": f"Voici les données RÉELLES de l'analyse. Utilise UNIQUEMENT ces valeurs dans ton rapport :\n\n{json.dumps(rapport_data, ensure_ascii=False, indent=2)}"}],
                    )

                    st.session_state.ai_tokens_used += response.usage.input_tokens + response.usage.output_tokens
                    rapport = response.content[0].text
                    st.session_state.rapport_genere = rapport

                    st.success("✅ Rapport généré !")

                except Exception as e:
                    st.error(f"❌ Erreur génération rapport : {e}")

        # Display generated report
        if "rapport_genere" in st.session_state:
            st.markdown("---")

            if profil_select == "custom":
                profil_affiche = st.session_state.get("custom_profile_title", "Profil personnalisé")
                profil_filename = "custom_" + profil_affiche.replace(" ", "_")[:20]
            else:
                profil_affiche = profils[profil_select]
                profil_filename = profil_select

            nb_attrs_rapport = len(attributs_focus)
            attrs_str = ", ".join(attributs_focus[:3]) + ("..." if nb_attrs_rapport > 3 else "")
            st.success(f"✅ Rapport généré pour : **{profil_affiche}** | {nb_attrs_rapport} attribut(s) : {attrs_str}")

            try:
                from backend.audit_trail import get_audit_trail
                audit = get_audit_trail()
                audit.log_report_generation(report_type=f"rapport_{profil_select}", format="markdown", columns_included=nb_attrs_rapport)
            except Exception:
                pass

            with st.expander("📄 Ton Rapport Personnalisé", expanded=True):
                st.markdown(st.session_state.rapport_genere)

            st.markdown("---")
            st.subheader("📥 Télécharger")

            col1, col2 = st.columns(2)
            with col1:
                rapport_bytes = st.session_state.rapport_genere.encode('utf-8')
                st.download_button("📝 Markdown (.md)", data=rapport_bytes, file_name=f"rapport_{profil_filename}_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")
            with col2:
                st.download_button("📄 Texte (.txt)", data=rapport_bytes, file_name=f"rapport_{profil_filename}_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain")

    else:
        st.warning("⚠️ Sélectionne au moins un usage ET un attribut pour générer un rapport")
