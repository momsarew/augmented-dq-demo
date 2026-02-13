"""
Onglet Data Contracts pour l'application Streamlit
Permet de définir, visualiser et valider des contrats de qualité de données.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime


def render_data_contracts_tab():
    """Rendu de l'onglet Data Contracts"""

    st.header("📜 Data Contracts")

    # En-tête
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">📜 Data Contracts - Contrats Qualité</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            Définissez des règles de qualité attendues pour chaque attribut et validez vos données automatiquement.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialiser session state pour les contrats
    if "data_contracts" not in st.session_state:
        st.session_state.data_contracts = {}

    df = st.session_state.get("df")
    results = st.session_state.get("results")

    if df is None:
        st.info("📁 Chargez un dataset dans la sidebar pour commencer à définir des contrats.")
        return

    # =========================================================================
    # GÉNÉRATION AUTOMATIQUE DE CONTRATS
    # =========================================================================

    st.subheader("⚡ Génération automatique")

    if st.button("🔄 Générer les contrats depuis le dataset", type="primary", use_container_width=True):
        contracts = _auto_generate_contracts(df)
        st.session_state.data_contracts = contracts
        st.success(f"✅ {len(contracts)} contrats générés automatiquement")

    if not st.session_state.data_contracts:
        st.info("💡 Cliquez sur le bouton ci-dessus pour générer automatiquement les contrats depuis votre dataset.")
        return

    contracts = st.session_state.data_contracts

    # =========================================================================
    # STATISTIQUES GLOBALES
    # =========================================================================

    total_rules = sum(len(c.get("rules", [])) for c in contracts.values())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Attributs", len(contracts))
    col2.metric("📏 Règles totales", total_rules)

    # Calculer violations
    violations = _validate_contracts(df, contracts)
    total_violations = sum(len(v) for v in violations.values())
    passing = len([c for c, v in violations.items() if len(v) == 0])

    col3.metric("✅ Conformes", f"{passing}/{len(contracts)}")
    col4.metric("⚠️ Violations", total_violations)

    st.markdown("---")

    # =========================================================================
    # VUE PAR ATTRIBUT
    # =========================================================================

    st.subheader("📋 Contrats par attribut")

    for col_name, contract in contracts.items():
        col_violations = violations.get(col_name, [])
        status_icon = "✅" if len(col_violations) == 0 else "⚠️"
        nb_rules = len(contract.get("rules", []))

        with st.expander(f"{status_icon} **{col_name}** — {nb_rules} règles, {len(col_violations)} violation(s)", expanded=len(col_violations) > 0):
            # Infos type
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Type attendu:** `{contract.get('expected_type', 'N/A')}`")
            c2.markdown(f"**Nullable:** {'Oui' if contract.get('nullable', True) else 'Non'}")
            c3.markdown(f"**Unique:** {'Oui' if contract.get('unique', False) else 'Non'}")

            # Règles
            if contract.get("rules"):
                st.markdown("**Règles:**")
                for rule in contract["rules"]:
                    rule_icon = "✅" if rule["name"] not in [v["rule"] for v in col_violations] else "❌"
                    st.markdown(f"- {rule_icon} **{rule['name']}**: {rule['description']}")

            # Violations
            if col_violations:
                st.markdown("**Violations détectées:**")
                for v in col_violations:
                    severity_color = "#eb3349" if v.get("severity") == "ERROR" else "#F2994A"
                    st.markdown(f"""
                    <div style="
                        background: {severity_color}15;
                        border-left: 3px solid {severity_color};
                        padding: 0.5rem 1rem;
                        margin-bottom: 0.5rem;
                        border-radius: 0 8px 8px 0;
                    ">
                        <span style="color: {severity_color}; font-weight: 600;">{v['rule']}</span>:
                        <span style="color: rgba(255,255,255,0.8);">{v['message']}</span>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # EXPORT
    # =========================================================================

    st.subheader("📤 Export des contrats")

    col1, col2 = st.columns(2)

    with col1:
        contract_json = json.dumps({
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "contracts": contracts
        }, ensure_ascii=False, indent=2)

        st.download_button(
            label="📥 Télécharger JSON",
            data=contract_json,
            file_name=f"data_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        # Export rapport violations
        if total_violations > 0:
            report_lines = [f"# Rapport de violations - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
            for col_name, col_violations in violations.items():
                if col_violations:
                    report_lines.append(f"\n## {col_name}")
                    for v in col_violations:
                        report_lines.append(f"- **{v['rule']}**: {v['message']}")
            report_text = "\n".join(report_lines)

            st.download_button(
                label="📥 Rapport violations (MD)",
                data=report_text,
                file_name=f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.success("Aucune violation - rien à exporter")


def _auto_generate_contracts(df: pd.DataFrame) -> dict:
    """Génère automatiquement des contrats depuis un DataFrame"""
    contracts = {}

    for col in df.columns:
        series = df[col]
        contract = {
            "expected_type": _infer_type(series),
            "nullable": bool(series.isnull().any()),
            "unique": bool(series.nunique() == len(series.dropna())),
            "rules": []
        }

        null_pct = series.isnull().mean() * 100

        # Règle: taux de nulls
        if null_pct > 0:
            contract["rules"].append({
                "name": "null_threshold",
                "description": f"Taux de valeurs nulles <= 10% (actuel: {null_pct:.1f}%)",
                "type": "null_check",
                "threshold": 10.0
            })
        else:
            contract["rules"].append({
                "name": "not_nullable",
                "description": "Aucune valeur nulle attendue",
                "type": "null_check",
                "threshold": 0.0
            })

        # Règles par type
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                q1, q3 = clean.quantile(0.01), clean.quantile(0.99)
                contract["rules"].append({
                    "name": "range_check",
                    "description": f"Valeurs dans [{q1:.2f}, {q3:.2f}] (intervalle 1-99%)",
                    "type": "range",
                    "min": float(q1),
                    "max": float(q3)
                })

                if (clean < 0).any():
                    contract["rules"].append({
                        "name": "sign_check",
                        "description": "Des valeurs négatives sont présentes",
                        "type": "info",
                    })

        elif pd.api.types.is_string_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                nunique = clean.nunique()
                max_len = clean.str.len().max()

                contract["rules"].append({
                    "name": "max_length",
                    "description": f"Longueur max <= {int(max_len)} caractères",
                    "type": "length",
                    "max_length": int(max_len)
                })

                if nunique <= 20:
                    values = sorted(clean.unique().tolist())
                    contract["rules"].append({
                        "name": "allowed_values",
                        "description": f"Valeurs autorisées: {', '.join(str(v) for v in values[:10])}{'...' if len(values) > 10 else ''}",
                        "type": "enum",
                        "values": [str(v) for v in values]
                    })

        elif pd.api.types.is_datetime64_any_dtype(series):
            clean = series.dropna()
            if len(clean) > 0:
                contract["rules"].append({
                    "name": "date_range",
                    "description": f"Dates entre {clean.min().strftime('%Y-%m-%d')} et {clean.max().strftime('%Y-%m-%d')}",
                    "type": "date_range",
                    "min_date": clean.min().isoformat(),
                    "max_date": clean.max().isoformat()
                })

        contracts[col] = contract

    return contracts


def _infer_type(series: pd.Series) -> str:
    """Détermine le type logique d'une colonne"""
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    elif pd.api.types.is_float_dtype(series):
        return "float"
    elif pd.api.types.is_bool_dtype(series):
        return "boolean"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    elif pd.api.types.is_string_dtype(series):
        return "string"
    return "unknown"


def _validate_contracts(df: pd.DataFrame, contracts: dict) -> dict:
    """Valide le DataFrame contre les contrats et retourne les violations"""
    violations = {}

    for col_name, contract in contracts.items():
        col_violations = []

        if col_name not in df.columns:
            col_violations.append({
                "rule": "column_exists",
                "message": f"Colonne '{col_name}' absente du dataset",
                "severity": "ERROR"
            })
            violations[col_name] = col_violations
            continue

        series = df[col_name]

        for rule in contract.get("rules", []):
            rule_type = rule.get("type")

            if rule_type == "null_check":
                null_pct = series.isnull().mean() * 100
                threshold = rule.get("threshold", 10.0)
                if null_pct > threshold:
                    col_violations.append({
                        "rule": rule["name"],
                        "message": f"Taux de nulls {null_pct:.1f}% dépasse le seuil de {threshold}%",
                        "severity": "ERROR" if null_pct > 50 else "WARNING"
                    })

            elif rule_type == "range":
                clean = series.dropna()
                if len(clean) > 0:
                    min_val, max_val = rule.get("min", float("-inf")), rule.get("max", float("inf"))
                    outliers = ((clean < min_val) | (clean > max_val)).sum()
                    if outliers > 0:
                        col_violations.append({
                            "rule": rule["name"],
                            "message": f"{outliers} valeurs hors de l'intervalle [{min_val:.2f}, {max_val:.2f}]",
                            "severity": "WARNING"
                        })

            elif rule_type == "length":
                clean = series.dropna()
                if len(clean) > 0:
                    max_length = rule.get("max_length", 255)
                    too_long = (clean.str.len() > max_length).sum()
                    if too_long > 0:
                        col_violations.append({
                            "rule": rule["name"],
                            "message": f"{too_long} valeurs dépassent {max_length} caractères",
                            "severity": "WARNING"
                        })

            elif rule_type == "enum":
                clean = series.dropna()
                if len(clean) > 0:
                    allowed = set(rule.get("values", []))
                    invalid = clean[~clean.astype(str).isin(allowed)]
                    if len(invalid) > 0:
                        examples = invalid.head(3).tolist()
                        col_violations.append({
                            "rule": rule["name"],
                            "message": f"{len(invalid)} valeurs non autorisées (ex: {', '.join(str(v) for v in examples)})",
                            "severity": "WARNING"
                        })

        violations[col_name] = col_violations

    return violations
