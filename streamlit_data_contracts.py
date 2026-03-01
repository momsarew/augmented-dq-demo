"""
Onglet Data Contracts pour l'application Streamlit
Interface de création, import, validation et versioning des Data Contracts
"""

import streamlit as st
import pandas as pd
import yaml
import json
from datetime import datetime
from typing import Optional, Dict, List
import io

# Import du module Data Contracts
try:
    from backend.data_contracts import (
        DataContract, ContractValidator, ContractRepository,
        create_template_contract, get_template_yaml, get_referentiel_yaml
    )
    CONTRACTS_OK = True
except ImportError as e:
    CONTRACTS_OK = False
    print(f"Module data_contracts non disponible: {e}")


def render_data_contracts_tab():
    """Rendu de l'onglet Data Contracts"""

    if not CONTRACTS_OK:
        st.error("Module Data Contracts non disponible")
        return

    # En-tête
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(142, 68, 173, 0.1) 0%, rgba(52, 168, 83, 0.1) 100%);
        border: 1px solid rgba(142, 68, 173, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">📜 Data Contracts</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            Définissez vos attentes qualité, validez vos datasets et versionnez vos contrats.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialiser le repository
    if "contract_repo" not in st.session_state:
        st.session_state.contract_repo = ContractRepository()

    repo = st.session_state.contract_repo

    # Tabs internes
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Importer/Créer",
        "✅ Valider",
        "📚 Mes Contracts",
        "📖 Documentation"
    ])

    # =========================================================================
    # TAB 1: IMPORTER / CRÉER
    # =========================================================================
    with tab1:
        st.subheader("📥 Importer ou Créer un Data Contract")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📄 Télécharger le template")
            st.markdown("""
            Le template est pré-rempli avec les **128 anomalies** du référentiel,
            organisées par dimension causale (DB, DP, BR, UP) et conformes au
            standard **ODCS v3.1.0**. Complétez le schéma avec vos colonnes,
            puis importez-le ci-dessous.
            """)

            template_yaml = get_template_yaml()

            st.download_button(
                label="📥 Télécharger template (avec référentiel)",
                data=template_yaml,
                file_name="data_contract_template.yaml",
                mime="text/yaml",
                use_container_width=True,
                type="primary",
                key="dl_template_yaml"
            )

            st.markdown("---")

            st.markdown("### 📚 Référentiel complet")
            st.markdown("""
            Téléchargez le **référentiel complet** des anomalies avec toutes les
            métadonnées : algorithmes, complexité, risques métier, classification
            Woodall, mapping ODCS.
            """)

            referentiel_yaml = get_referentiel_yaml()

            st.download_button(
                label="📥 Télécharger le référentiel complet (YAML)",
                data=referentiel_yaml,
                file_name="referentiel_augmented_dq.yaml",
                mime="text/yaml",
                use_container_width=True,
                key="dl_referentiel_yaml"
            )

            st.markdown("---")

            st.markdown("### 📤 Importer un contract")
            uploaded_contract = st.file_uploader(
                "Choisir un fichier YAML ou JSON",
                type=["yaml", "yml", "json"],
                key="contract_upload"
            )

            if uploaded_contract:
                try:
                    content = uploaded_contract.read().decode('utf-8')
                    if uploaded_contract.name.endswith('.json'):
                        contract = DataContract.from_json(content)
                    else:
                        contract = DataContract.from_yaml(content)

                    st.success(f"✅ Contract '{contract.name}' v{contract.version} chargé")

                    # Afficher résumé
                    with st.expander("📋 Résumé du contract", expanded=True):
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Colonnes", len(contract.schema))
                        col_b.metric("Règles qualité", len(contract.quality_rules))
                        col_c.metric("Règles métier", len(contract.business_rules))

                        if contract.schema:
                            st.markdown("**Colonnes définies:**")
                            cols_list = [f"• {c.get('name')} ({c.get('type', 'any')})" for c in contract.schema[:10]]
                            st.markdown("\n".join(cols_list))
                            if len(contract.schema) > 10:
                                st.caption(f"... et {len(contract.schema) - 10} autres")

                    # Sauvegarder
                    if st.button("💾 Sauvegarder dans le repository", type="primary", key="save_imported"):
                        contract_id = repo.save_contract(contract)
                        st.session_state.current_contract = contract
                        st.success(f"✅ Contract sauvegardé: {contract_id}")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Erreur de parsing: {e}")

        with col2:
            st.markdown("### ✏️ Créer un contract simple")
            st.markdown("Créez rapidement un contract basique via l'interface.")

            with st.form("create_contract_form"):
                contract_name = st.text_input("Nom du contract", value="Mon Dataset")
                contract_version = st.text_input("Version", value="1.0.0")
                contract_owner = st.text_input("Owner (email)", value="")
                contract_desc = st.text_area("Description", height=80)

                st.markdown("---")
                st.markdown("**Colonnes (schéma simplifié)**")

                # Si un DataFrame est chargé, proposer ses colonnes
                if st.session_state.get("df") is not None:
                    df = st.session_state.df
                    st.info(f"💡 Dataset chargé avec {len(df.columns)} colonnes")

                    selected_cols = st.multiselect(
                        "Sélectionner les colonnes à inclure",
                        options=list(df.columns),
                        default=list(df.columns)[:5]
                    )
                else:
                    selected_cols = []
                    st.warning("Chargez d'abord un dataset pour auto-détecter les colonnes")

                submitted = st.form_submit_button("📝 Générer le contract", type="primary")

                if submitted and contract_name:
                    # Créer le contract
                    schema = []
                    if selected_cols and st.session_state.get("df") is not None:
                        df = st.session_state.df
                        for col in selected_cols:
                            col_type = _infer_type(df[col])
                            schema.append({
                                "name": col,
                                "type": col_type,
                                "nullable": df[col].isna().any(),
                                "description": f"Colonne {col}",
                            })

                    new_contract = DataContract({
                        "name": contract_name,
                        "version": contract_version,
                        "owner": contract_owner,
                        "description": contract_desc,
                        "schema": schema,
                        "quality_rules": [],
                        "business_rules": [],
                    })

                    st.session_state.current_contract = new_contract
                    st.session_state.editing_contract = True
                    st.success("✅ Contract créé! Personnalisez-le ci-dessous.")

        # Éditeur de contract (si en cours d'édition)
        if st.session_state.get("editing_contract") and st.session_state.get("current_contract"):
            st.markdown("---")
            _render_contract_editor(st.session_state.current_contract, repo)

    # =========================================================================
    # TAB 2: VALIDER
    # =========================================================================
    with tab2:
        st.subheader("✅ Valider un Dataset contre un Contract")

        # Sélectionner le contract
        contracts_list = repo.list_contracts()

        col1, col2 = st.columns([2, 1])

        with col1:
            if contracts_list:
                contract_options = {f"{c['name']} (v{c['latest_version']})": c['id'] for c in contracts_list}
                selected_contract_name = st.selectbox(
                    "Sélectionner un contract",
                    options=list(contract_options.keys())
                )
                selected_contract_id = contract_options.get(selected_contract_name)
            else:
                st.warning("Aucun contract disponible. Importez ou créez-en un d'abord.")
                selected_contract_id = None

        with col2:
            # Ou utiliser le contract courant
            if st.session_state.get("current_contract"):
                if st.button("📋 Utiliser contract courant"):
                    selected_contract_id = "__current__"

        # Valider
        if selected_contract_id and st.session_state.get("df") is not None:
            df = st.session_state.df

            if st.button("🔍 Valider le dataset", type="primary", use_container_width=True):
                with st.spinner("Validation en cours..."):
                    # Charger le contract
                    if selected_contract_id == "__current__":
                        contract = st.session_state.current_contract
                    else:
                        contract = repo.get_contract(selected_contract_id)

                    if contract:
                        validator = ContractValidator(contract)
                        results = validator.validate(df)

                        # Stocker les résultats
                        st.session_state.contract_validation_results = results

            # Afficher les résultats
            if st.session_state.get("contract_validation_results"):
                _render_validation_results(st.session_state.contract_validation_results)

        elif st.session_state.get("df") is None:
            st.info("📁 Chargez d'abord un dataset dans l'onglet Accueil")

    # =========================================================================
    # TAB 3: MES CONTRACTS
    # =========================================================================
    with tab3:
        st.subheader("📚 Repository de Data Contracts")

        contracts_list = repo.list_contracts()

        if not contracts_list:
            st.info("Aucun contract enregistré. Importez ou créez-en un dans l'onglet 'Importer/Créer'.")
        else:
            for contract_info in contracts_list:
                with st.expander(f"📜 {contract_info['name']} (v{contract_info['latest_version']})", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown(f"**ID:** `{contract_info['id']}`")
                        st.markdown(f"**Versions:** {', '.join(contract_info['versions'])}")
                        if contract_info.get('updated_at'):
                            st.caption(f"Mis à jour: {contract_info['updated_at'][:10]}")

                    with col2:
                        # Sélectionner version
                        version = st.selectbox(
                            "Version",
                            options=contract_info['versions'],
                            index=contract_info['versions'].index(contract_info['latest_version']),
                            key=f"version_{contract_info['id']}"
                        )

                    with col3:
                        # Actions
                        if st.button("📖 Voir", key=f"view_{contract_info['id']}"):
                            contract = repo.get_contract(contract_info['id'], version)
                            st.session_state.current_contract = contract
                            st.session_state.viewing_contract = contract_info['id']

                        if st.button("📥 Export YAML", key=f"export_{contract_info['id']}"):
                            contract = repo.get_contract(contract_info['id'], version)
                            if contract:
                                st.download_button(
                                    "💾 Télécharger",
                                    data=contract.to_yaml(),
                                    file_name=f"{contract_info['id']}_v{version}.yaml",
                                    mime="text/yaml",
                                    key=f"dl_{contract_info['id']}"
                                )

                    # Afficher le contract si sélectionné
                    if st.session_state.get("viewing_contract") == contract_info['id']:
                        contract = repo.get_contract(contract_info['id'], version)
                        if contract:
                            st.markdown("---")
                            _render_contract_view(contract)

    # =========================================================================
    # TAB 4: DOCUMENTATION
    # =========================================================================
    with tab4:
        st.subheader("📖 Documentation Data Contracts")

        st.markdown("""
        ### Qu'est-ce qu'un Data Contract ?

        Un **Data Contract** est un accord formel entre un producteur de données et ses consommateurs.
        Il définit précisément:

        - 📋 **Le schéma** : colonnes, types, formats attendus
        - ✅ **Les règles de qualité** : complétude, unicité, validité
        - 📊 **Les règles métier** : logique spécifique à votre domaine
        - ⏱️ **Les SLA** : fraîcheur, disponibilité
        - 👥 **Les responsabilités** : qui produit, qui consomme

        ---

        ### Structure d'un Contract YAML

        ```yaml
        name: "Mon Dataset RH"
        version: "1.0.0"
        owner: "equipe-data@exemple.com"

        schema:
          - name: "Matricule"
            type: "string"
            nullable: false
            unique: true
            pattern: "^EMP[0-9]{6}$"

          - name: "Salaire"
            type: "decimal"
            range: [1500, 500000]

        quality_rules:
          - rule: "completeness"
            columns: ["Matricule", "Nom"]
            threshold: 0.99

        business_rules:
          - name: "salaire_coherent"
            type: "comparison"
            column1: "Salaire"
            column2: "Salaire_Min"
            operator: ">="
        ```

        ---

        ### Types supportés

        | Type | Description | Exemple |
        |------|-------------|---------|
        | `string` | Texte | "Jean Dupont" |
        | `integer` | Entier | 42 |
        | `decimal` / `float` | Nombre décimal | 3.14 |
        | `boolean` | Booléen | true/false |
        | `date` | Date | 2024-01-15 |
        | `datetime` | Date et heure | 2024-01-15T10:30:00 |
        | `email` | Adresse email | jean@exemple.com |

        ---

        ### Règles de qualité

        | Règle | Description |
        |-------|-------------|
        | `completeness` | Taux minimum de valeurs non nulles |
        | `uniqueness` | Unicité des valeurs |
        | `not_null` | Interdit les valeurs nulles |
        | `in_range` | Valeur dans une plage |
        | `matches_pattern` | Respect d'un pattern regex |
        | `in_list` / `enum` | Valeur parmi une liste |

        ---

        ### Règles métier

        | Type | Description |
        |------|-------------|
        | `comparison` | Compare deux colonnes (>, <, =, etc.) |
        | `conditional` | Si colonne A = X, alors colonne B doit... |
        | `expression` | Formule personnalisée |

        """)


def _render_contract_editor(contract: DataContract, repo: ContractRepository):
    """Éditeur interactif de contract"""
    st.markdown("### ✏️ Éditeur de Contract")

    with st.form("edit_contract"):
        col1, col2 = st.columns(2)

        with col1:
            contract.name = st.text_input("Nom", value=contract.name)
            contract.version = st.text_input("Version", value=contract.version)

        with col2:
            contract.owner = st.text_input("Owner", value=contract.owner)
            tags_str = st.text_input("Tags (séparés par virgule)", value=", ".join(contract.tags))
            contract.tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        contract.description = st.text_area("Description", value=contract.description)

        st.markdown("---")
        st.markdown("**📋 Schéma des colonnes**")

        # Éditer chaque colonne
        updated_schema = []
        for i, col_spec in enumerate(contract.schema):
            with st.expander(f"Colonne: {col_spec.get('name', f'Col {i}')}", expanded=False):
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    col_name = st.text_input("Nom", value=col_spec.get("name", ""), key=f"col_name_{i}")
                    col_type = st.selectbox(
                        "Type",
                        options=DataContract.SUPPORTED_TYPES,
                        index=DataContract.SUPPORTED_TYPES.index(col_spec.get("type", "string")) if col_spec.get("type") in DataContract.SUPPORTED_TYPES else 0,
                        key=f"col_type_{i}"
                    )

                with col_b:
                    col_nullable = st.checkbox("Nullable", value=col_spec.get("nullable", True), key=f"col_null_{i}")
                    col_unique = st.checkbox("Unique", value=col_spec.get("unique", False), key=f"col_uniq_{i}")

                with col_c:
                    col_pattern = st.text_input("Pattern (regex)", value=col_spec.get("pattern", ""), key=f"col_pat_{i}")

                col_desc = st.text_input("Description", value=col_spec.get("description", ""), key=f"col_desc_{i}")

                updated_schema.append({
                    "name": col_name,
                    "type": col_type,
                    "nullable": col_nullable,
                    "unique": col_unique,
                    "pattern": col_pattern if col_pattern else None,
                    "description": col_desc,
                })

        contract.schema = [s for s in updated_schema if s.get("name")]

        st.markdown("---")

        col_save, col_export = st.columns(2)

        with col_save:
            if st.form_submit_button("💾 Sauvegarder", type="primary"):
                contract_id = repo.save_contract(contract)
                st.session_state.current_contract = contract
                st.success(f"✅ Contract '{contract.name}' v{contract.version} sauvegardé!")

        with col_export:
            pass  # Export button outside form

    # Export YAML (outside form)
    if st.button("📥 Exporter YAML", key="btn_export_yaml_contract"):
        st.download_button(
            "💾 Télécharger",
            data=contract.to_yaml(),
            file_name=f"{contract.name.lower().replace(' ', '_')}_v{contract.version}.yaml",
            mime="text/yaml",
            key="dl_export_yaml_contract"
        )


def _render_contract_view(contract: DataContract):
    """Affiche un contract en lecture seule"""
    col1, col2, col3 = st.columns(3)
    col1.metric("Version", contract.version)
    col2.metric("Colonnes", len(contract.schema))
    col3.metric("Règles", len(contract.quality_rules) + len(contract.business_rules))

    if contract.owner:
        st.caption(f"👤 Owner: {contract.owner}")
    if contract.description:
        st.info(contract.description)

    # Schéma
    if contract.schema:
        st.markdown("**📋 Schéma:**")
        schema_df = pd.DataFrame([
            {
                "Colonne": c.get("name"),
                "Type": c.get("type", "any"),
                "Nullable": "✅" if c.get("nullable", True) else "❌",
                "Unique": "✅" if c.get("unique", False) else "—",
                "Pattern": c.get("pattern", "—"),
            }
            for c in contract.schema
        ])
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    # Règles
    if contract.quality_rules or contract.business_rules:
        st.markdown("**📏 Règles:**")
        for rule in contract.quality_rules:
            st.markdown(f"• **{rule.get('rule')}** sur `{rule.get('columns', [])}` (seuil: {rule.get('threshold', '—')})")
        for rule in contract.business_rules:
            st.markdown(f"• **{rule.get('name')}** ({rule.get('type', 'custom')}): {rule.get('description', '')}")


def _render_validation_results(results: Dict):
    """Affiche les résultats de validation"""
    st.markdown("---")
    st.markdown("### 📊 Résultats de Validation")

    # Score global
    score = results.get("conformity_percent", 0)
    if score >= 90:
        score_color = "#38ef7d"
        score_icon = "✅"
    elif score >= 70:
        score_color = "#FBBD23"
        score_icon = "⚠️"
    else:
        score_color = "#eb3349"
        score_icon = "❌"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="
            background: {score_color}20;
            border: 2px solid {score_color};
            border-radius: 16px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="font-size: 2.5rem;">{score_icon}</div>
            <div style="color: {score_color}; font-size: 1.8rem; font-weight: 700;">{score}%</div>
            <div style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Conformité</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("❌ Violations", results.get("total_violations", 0))

    with col3:
        st.metric("⚠️ Avertissements", results.get("total_warnings", 0))

    with col4:
        st.metric("📜 Contract", f"v{results.get('contract_version', '?')}")

    # Détails des violations
    violations = results.get("violations", [])
    if violations:
        st.markdown("---")
        st.markdown("### ❌ Violations")

        for v in violations:
            severity_colors = {
                "critical": "#eb3349",
                "high": "#eb3349",
                "medium": "#FBBD23",
                "low": "#38ef7d",
            }
            color = severity_colors.get(v.get("severity", "medium"), "#FBBD23")

            st.markdown(f"""
            <div style="
                background: {color}15;
                border-left: 4px solid {color};
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                border-radius: 0 8px 8px 0;
            ">
                <div style="display: flex; justify-content: space-between;">
                    <strong style="color: {color};">{v.get('rule', 'Unknown')}</strong>
                    <span style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">{v.get('column', '')}</span>
                </div>
                <div style="color: white; margin-top: 0.25rem;">{v.get('message', '')}</div>
                {f"<div style='color: rgba(255,255,255,0.5); font-size: 0.8rem; margin-top: 0.25rem;'>Lignes affectées: {v.get('affected_rows', '—')}</div>" if v.get('affected_rows') else ""}
            </div>
            """, unsafe_allow_html=True)

    # Warnings
    warnings = results.get("warnings", [])
    if warnings:
        with st.expander(f"⚠️ Avertissements ({len(warnings)})", expanded=False):
            for w in warnings:
                st.markdown(f"• **{w.get('column', '')}**: {w.get('message', '')}")

    # Scores par colonne
    column_scores = results.get("column_scores", {})
    if column_scores:
        st.markdown("---")
        st.markdown("### 📊 Score par Colonne")

        scores_df = pd.DataFrame([
            {"Colonne": col, "Score": f"{score*100:.0f}%", "Statut": "✅" if score >= 0.9 else "⚠️" if score >= 0.7 else "❌"}
            for col, score in column_scores.items()
        ])
        st.dataframe(scores_df, use_container_width=True, hide_index=True)


def _infer_type(series: pd.Series) -> str:
    """Infère le type d'une série pandas"""
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    elif pd.api.types.is_float_dtype(series):
        return "decimal"
    elif pd.api.types.is_bool_dtype(series):
        return "boolean"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    else:
        # Vérifier si c'est un email
        non_null = series.dropna().astype(str)
        if len(non_null) > 0:
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if non_null.str.match(email_pattern).mean() > 0.9:
                return "email"

            # Vérifier si c'est une date
            try:
                pd.to_datetime(non_null.head(100))
                return "date"
            except:
                pass

        return "string"
