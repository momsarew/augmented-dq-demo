"""Tab Paramètres - API configuration and preferences."""

import os
import streamlit as st


def render_settings_tab_full(validate_api_key, mask_api_key):
    """Render the full settings tab (post-analysis)."""
    st.header("Paramètres", anchor=False)

    def load_api_key_from_secrets():
        """Charge la cle API depuis les sources disponibles.

        Ordre de priorite : secrets.toml (nested ou flat) > variable d'env.
        """
        try:
            if hasattr(st, 'secrets'):
                if 'api' in st.secrets and 'ANTHROPIC_API_KEY' in st.secrets['api']:
                    key = st.secrets['api']['ANTHROPIC_API_KEY']
                    if key and key.strip():
                        return key.strip()
                if 'ANTHROPIC_API_KEY' in st.secrets:
                    key = st.secrets['ANTHROPIC_API_KEY']
                    if key and key.strip():
                        return key.strip()
        except Exception:
            pass
        try:
            key = os.getenv("ANTHROPIC_API_KEY", "")
            if key and key.strip():
                return key.strip()
        except Exception:
            pass
        return ""

    def check_admin_password():
        """Retourne le mot de passe admin depuis secrets ou 'admin' par defaut."""
        try:
            if hasattr(st, 'secrets') and 'admin' in st.secrets:
                return st.secrets['admin'].get('ADMIN_PASSWORD', '')
        except Exception:
            pass
        return "admin"

    if "anthropic_api_key" not in st.session_state or not st.session_state.anthropic_api_key:
        loaded_key = load_api_key_from_secrets()
        if loaded_key:
            is_valid, _ = validate_api_key(loaded_key)
            if is_valid:
                st.session_state.anthropic_api_key = loaded_key

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">Configuration de l'application</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            Statut de l'application et préférences utilisateur.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Statut API Claude")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        L'API Claude permet d'activer les fonctionnalités d'**assistance IA** :
        - Explications contextuelles des résultats
        - Génération de rapports personnalisés
        - Recommandations selon ton profil de risque
        - Synthèses intelligentes
        """)

        has_key = bool(st.session_state.get("anthropic_api_key"))

        if has_key:
            st.success("L'API Claude est configurée et prête à l'emploi")
            tokens = st.session_state.get("ai_tokens_used", 0)
            cost = (tokens / 1e6) * 9
            st.metric("Tokens utilisés (session)", f"{tokens:,}", delta=f"≈ ${cost:.4f}")
        else:
            st.warning("L'API Claude n'est pas configurée")
            st.info("Contactez l'administrateur pour activer les fonctionnalités IA")

    with col2:
        has_key = bool(st.session_state.get("anthropic_api_key"))
        status_color = "#38ef7d" if has_key else "#eb3349"
        status_text = "Active" if has_key else "Inactive"
        st.markdown(f"""
        <div style="
            background: {status_color}20;
            border: 2px solid {status_color};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="color: {status_color}; font-weight: 700; font-size: 1.2rem;">IA {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Admin section
    with st.expander(":material/admin_panel_settings: Administration (acces restreint)", expanded=False):
        st.warning("Cette section est réservée à l'administrateur")

        if not st.session_state.get("admin_authenticated", False):
            admin_pwd = st.text_input("Mot de passe administrateur", type="password", key="admin_password_input", placeholder="Entrer le mot de passe admin...")

            if st.button(":material/login: Se connecter", type="primary"):
                correct_pwd = check_admin_password()
                if admin_pwd == correct_pwd:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")

        else:
            st.success("Connecté en tant qu'administrateur")

            if st.button(":material/logout: Se déconnecter"):
                st.session_state.admin_authenticated = False
                st.rerun()

            st.markdown("---")
            st.subheader("Configuration API Claude")

            current_key = st.session_state.get("anthropic_api_key", "")
            if current_key:
                st.info(f"Clé actuelle: {mask_api_key(current_key)}")

            new_api_key = st.text_input("Nouvelle clé API Anthropic", type="password", placeholder="sk-ant-api03-...", help="Entrez une nouvelle clé pour remplacer l'existante", max_chars=200)

            if st.button(":material/save: Sauvegarder la clé", type="primary"):
                if new_api_key:
                    clean_key = new_api_key.strip()
                    is_valid, error_msg = validate_api_key(clean_key)

                    if is_valid:
                        st.session_state.anthropic_api_key = clean_key
                        st.success(f"Clé API mise à jour: {mask_api_key(clean_key)}")

                        st.info("""
                        **Pour rendre cette clé persistante:**

                        **En local:** Modifiez le fichier `.streamlit/secrets.toml`:
                        ```toml
                        [api]
                        ANTHROPIC_API_KEY = "votre-clé-ici"
                        ```

                        **Sur Streamlit Cloud:** Allez dans Settings > Secrets et ajoutez:
                        ```toml
                        [api]
                        ANTHROPIC_API_KEY = "votre-clé-ici"
                        ```
                        """)
                    else:
                        st.error(f"{error_msg}")
                else:
                    st.warning("Entrez une clé API")

            st.markdown("---")
            st.subheader("Sécurité")
            st.caption("Pour modifier le mot de passe admin, éditez `.streamlit/secrets.toml`")

    st.markdown("---")

    st.subheader("Préférences d'affichage")

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Langue des rapports IA", options=["Français", "English"], index=0, help="Langue utilisée pour la génération des rapports", disabled=True)
        st.caption("Bientôt disponible")
    with col2:
        st.selectbox("Niveau de detail par defaut", options=["Synthétique", "Standard", "Détaillé"], index=1, help="Niveau de détail pour les explications IA", disabled=True)
        st.caption("Bientôt disponible")

    st.markdown("---")

    st.subheader("Gestion des données")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(":material/restart_alt: Réinitialiser session", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ["anthropic_api_key"]:
                    del st.session_state[key]
            st.success("Session réinitialisée")
            st.rerun()
    with col2:
        if st.button(":material/delete_sweep: Vider cache IA", use_container_width=True):
            st.session_state.ai_explanations = {}
            if "profil_risque_reco" in st.session_state:
                del st.session_state.profil_risque_reco
            if "rapport_genere" in st.session_state:
                del st.session_state.rapport_genere
            st.success("Cache IA vidé")
    with col3:
        if st.button(":material/bug_report: Infos debug", use_container_width=True):
            with st.expander(":material/bug_report: Etat session", expanded=True):
                debug_info = {
                    "df_loaded": st.session_state.df is not None,
                    "analysis_done": st.session_state.get("analysis_done", False),
                    "api_configured": bool(st.session_state.get("anthropic_api_key")),
                    "tokens_used": st.session_state.get("ai_tokens_used", 0),
                    "profil_risque": st.session_state.get("profil_risque", "equilibre"),
                    "nb_explanations_cached": len(st.session_state.get("ai_explanations", {}))
                }
                st.json(debug_info)

    st.markdown("---")

    st.subheader("A propos")
    st.markdown("""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
    ">
        <h4 style="color: white; margin: 0 0 1rem 0;">Framework Probabiliste DQ</h4>
        <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;"><strong>Version :</strong> 2.0.0</p>
        <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;"><strong>Moteur IA :</strong> Claude Sonnet 4 (Anthropic)</p>
        <p style="color: rgba(255,255,255,0.7); margin: 0 0 1rem 0;"><strong>Framework :</strong> Streamlit + Plotly</p>
        <p style="color: rgba(255,255,255,0.5); margin: 0; font-size: 0.85rem;">
            Outil de démonstration pour l'analyse de qualité des données avec approche probabiliste basée sur les distributions Beta.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_settings_tab_init():
    """Render the initial settings tab (before analysis)."""
    st.header("Paramètres", anchor=False)

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">Configuration de l'application</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            Configure ici ta clé API et tes préférences pour l'assistance IA.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("API Claude (Anthropic)")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        L'API Claude permet d'activer les fonctionnalités d'**assistance IA** :
        - Explications contextuelles des résultats
        - Génération de rapports personnalisés
        - Recommandations selon ton profil de risque
        - Synthèses intelligentes
        """)

        api_key_input_init = st.text_input(
            "Clé API Anthropic",
            type="password",
            value=st.session_state.get("anthropic_api_key", "") or os.getenv("ANTHROPIC_API_KEY", ""),
            placeholder="sk-ant-api03-...",
            help="Ta clé reste locale et n'est jamais stockée sur un serveur",
            key="api_key_init"
        )

        if api_key_input_init:
            api_key_clean = api_key_input_init.strip()
            if api_key_clean.startswith("sk-ant-"):
                st.session_state.anthropic_api_key = api_key_clean
                st.success("Clé API valide et enregistrée")
            else:
                st.error("Format invalide (doit commencer par 'sk-ant-')")
                st.session_state.anthropic_api_key = ""
        else:
            st.session_state.anthropic_api_key = ""

        st.markdown("---")
        st.markdown("""
        **Comment obtenir une clé API ?**
        1. Crée un compte sur [console.anthropic.com](https://console.anthropic.com)
        2. Va dans **Settings** → **API Keys**
        3. Clique sur **Create Key**
        4. Copie la clé et colle-la ci-dessus
        """)

    with col2:
        has_key = bool(st.session_state.get("anthropic_api_key"))
        status_color = "#38ef7d" if has_key else "#eb3349"
        status_text = "Configurée" if has_key else "Non configurée"
        st.markdown(f"""
        <div style="
            background: {status_color}20;
            border: 2px solid {status_color};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <div style="color: {status_color}; font-weight: 700; font-size: 1.2rem;">API {status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("A propos")
    st.markdown("""
    <div style="
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1.5rem;
    ">
        <h4 style="color: white; margin: 0 0 1rem 0;">Framework Probabiliste DQ</h4>
        <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;"><strong>Version :</strong> 2.0.0</p>
        <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;"><strong>Moteur IA :</strong> Claude Sonnet 4 (Anthropic)</p>
        <p style="color: rgba(255,255,255,0.5); margin: 0; font-size: 0.85rem;">
            Outil de démonstration pour l'analyse de qualité des données avec approche probabiliste.
        </p>
    </div>
    """, unsafe_allow_html=True)
