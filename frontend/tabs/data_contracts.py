"""
Tab Data Contracts v2 - Contrats de qualité intégrant le référentiel complet.

Intègre :
- 15 anomalies core (DB#1-5, DP#1-3, BR#1-4, UP#1-3)
- 6 dimensions DAMA/ISO 8000
- 4 dimensions causales (P_DB, P_DP, P_BR, P_UP)
- 5 profils de risque AHP
"""

import re
import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime


# ============================================================================
# RÉFÉRENTIEL DES ANOMALIES CORE (15)
# ============================================================================

ANOMALY_CATALOG = {
    # ── DB: Structure ──────────────────────────────────────────────────────
    "DB#1": {
        "name": "NULL dans colonnes obligatoires",
        "dimension": "DB", "criticality": "CRITIQUE", "woodall": "SAST",
        "description": "Attributs (1,1) contenant NULL",
        "example": "employee_id NULL → Paie bloquée",
    },
    "DB#2": {
        "name": "Doublons clé primaire",
        "dimension": "DB", "criticality": "CRITIQUE", "woodall": "SAMT",
        "description": "Violations contrainte PK",
        "example": "Matricule en double → Masse salariale ×2",
    },
    "DB#3": {
        "name": "Formats email invalides",
        "dimension": "DB", "criticality": "MOYEN", "woodall": "SAST",
        "description": "Email sans @ ou domaine invalide",
        "example": "Email invalide → Notification échoue",
    },
    "DB#4": {
        "name": "Valeurs hors domaine",
        "dimension": "DB", "criticality": "ÉLEVÉ", "woodall": "SAST",
        "description": "Valeur ∉ ensemble autorisé",
        "example": "Statut='Actif' au lieu CDI/CDD/Stage",
    },
    "DB#5": {
        "name": "Valeurs négatives interdites",
        "dimension": "DB", "criticality": "MOYEN", "woodall": "SAST",
        "description": "< 0 sur champs positifs (age, salaire, ancienneté)",
        "example": "Age=-5 → Calcul primes faussé",
    },
    # ── DP: Traitements ───────────────────────────────────────────────────
    "DP#1": {
        "name": "Calculs dérivés incorrects",
        "dimension": "DP", "criticality": "ÉLEVÉ", "woodall": "MAST",
        "description": "Formule F(A,...) non respectée",
        "example": "Age=35 mais né en 1985 → Écart 4 ans",
    },
    "DP#2": {
        "name": "Divisions par zéro",
        "dimension": "DP", "criticality": "MOYEN", "woodall": "SAST",
        "description": "Dénominateur = 0 ou NULL",
        "example": "Marge=(prix-cout)/cout avec cout=0",
    },
    "DP#3": {
        "name": "Type données incorrect",
        "dimension": "DP", "criticality": "MOYEN", "woodall": "SAST",
        "description": "Type réel ≠ type attendu (ex: VARCHAR au lieu DECIMAL)",
        "example": "Prix stocké en texte au lieu de nombre",
    },
    # ── BR: Règles Métier ─────────────────────────────────────────────────
    "BR#1": {
        "name": "Incohérences temporelles",
        "dimension": "BR", "criticality": "ÉLEVÉ", "woodall": "MAST",
        "description": "date_début > date_fin",
        "example": "Date_sortie < date_entrée → Ancienneté négative",
    },
    "BR#2": {
        "name": "Valeurs hors bornes métier",
        "dimension": "BR", "criticality": "CRITIQUE", "woodall": "MAST",
        "description": "Hors [min_business, max_business]",
        "example": "Age=150 ans → Donnée aberrante",
    },
    "BR#3": {
        "name": "Combinaisons interdites",
        "dimension": "BR", "criticality": "ÉLEVÉ", "woodall": "MAST",
        "description": "États mutuellement exclusifs",
        "example": "Forfait_jour=OUI ET heures_sup≠NULL",
    },
    "BR#4": {
        "name": "Obligations métier (SI/ALORS)",
        "dimension": "BR", "criticality": "ÉLEVÉ", "woodall": "MAST",
        "description": "SI condition ALORS champ obligatoire",
        "example": "Ancienneté>0 MAIS prime_ancienneté=0",
    },
    # ── UP: Utilisabilité ─────────────────────────────────────────────────
    "UP#1": {
        "name": "Données obsolètes",
        "dimension": "UP", "criticality": "ÉLEVÉ", "woodall": "SAMT",
        "description": "Date MAJ trop ancienne",
        "example": "Prix catalogue 2019 en 2025",
    },
    "UP#2": {
        "name": "Granularité excessive",
        "dimension": "UP", "criticality": "FAIBLE", "woodall": "SAMT",
        "description": "Trop de valeurs uniques (ratio > seuil)",
        "example": "Reporting annuel avec données à la seconde",
    },
    "UP#3": {
        "name": "Granularité insuffisante",
        "dimension": "UP", "criticality": "MOYEN", "woodall": "SAMT",
        "description": "Pas assez de détail (< seuil valeurs uniques)",
        "example": "Analyse pays avec seulement 3 valeurs",
    },
}

DAMA_DIMENSIONS = ["Complétude", "Cohérence", "Exactitude", "Fraîcheur", "Validité", "Unicité"]

CRITICALITY_ORDER = {"CRITIQUE": 4, "ÉLEVÉ": 3, "MOYEN": 2, "FAIBLE": 1}
SEVERITY_COLORS = {"CRITIQUE": "#eb3349", "ÉLEVÉ": "#F2994A", "MOYEN": "#F2C94C", "FAIBLE": "#38ef7d"}
DIM_COLORS = {"DB": "#667eea", "DP": "#764ba2", "BR": "#f093fb", "UP": "#38ef7d"}


# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render_data_contracts_tab():
    """Rendu de l'onglet Data Contracts avec référentiel complet."""

    st.header("📜 Data Contracts")

    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">📜 Data Contracts v2 — Référentiel Complet</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            15 anomalies core (DB#1–5, DP#1–3, BR#1–4, UP#1–3) ·
            6 dimensions DAMA/ISO 8000 ·
            4 dimensions causales (P_DB, P_DP, P_BR, P_UP)
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "data_contracts" not in st.session_state:
        st.session_state.data_contracts = {}

    df = st.session_state.get("df")
    if df is None:
        st.info("📁 Chargez un dataset dans la sidebar pour générer les contrats.")
        return

    # =====================================================================
    # GÉNÉRATION
    # =====================================================================

    st.subheader("⚡ Génération automatique")

    if st.button("🔄 Générer les contrats (référentiel complet)", type="primary", use_container_width=True):
        contracts = _auto_generate_contracts(df)
        st.session_state.data_contracts = contracts
        total_rules = sum(len(c.get("rules", [])) for c in contracts.values())
        st.success(f"✅ {len(contracts)} contrats · {total_rules} règles générées depuis le référentiel")

    if not st.session_state.data_contracts:
        st.info("💡 Cliquez ci-dessus pour générer automatiquement les contrats depuis le référentiel complet.")
        return

    contracts = st.session_state.data_contracts

    # =====================================================================
    # VALIDATION
    # =====================================================================

    violations = _validate_contracts(df, contracts)
    dama_scores = _compute_dama_scores(df, contracts, violations)

    # =====================================================================
    # MÉTRIQUES GLOBALES
    # =====================================================================

    total_rules = sum(len(c.get("rules", [])) for c in contracts.values())
    total_violations = sum(len(v) for v in violations.values())
    passing = len([c for c in contracts if len(violations.get(c, [])) == 0])

    # Compter par dimension
    dim_counts = {"DB": 0, "DP": 0, "BR": 0, "UP": 0}
    dim_violations = {"DB": 0, "DP": 0, "BR": 0, "UP": 0}
    for contract in contracts.values():
        for rule in contract.get("rules", []):
            dim = rule.get("dimension", "")
            if dim in dim_counts:
                dim_counts[dim] += 1
    for col_viols in violations.values():
        for v in col_viols:
            dim = v.get("dimension", "")
            if dim in dim_violations:
                dim_violations[dim] += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 Attributs", len(contracts))
    c2.metric("📏 Règles", total_rules)
    c3.metric("✅ Conformes", f"{passing}/{len(contracts)}")
    c4.metric("⚠️ Violations", total_violations)

    # Métriques par dimension causale
    st.markdown("**Couverture par dimension causale :**")
    dc1, dc2, dc3, dc4 = st.columns(4)
    for col_ui, (dim, label) in zip(
        [dc1, dc2, dc3, dc4],
        [("DB", "Structure"), ("DP", "Traitements"), ("BR", "Règles Métier"), ("UP", "Utilisabilité")]
    ):
        nb = dim_counts[dim]
        nv = dim_violations[dim]
        color = DIM_COLORS[dim]
        col_ui.markdown(f"""
        <div style="background: {color}15; border-left: 3px solid {color}; padding: 0.5rem; border-radius: 0 8px 8px 0;">
            <strong style="color: {color};">[{dim}] {label}</strong><br/>
            <span style="color: rgba(255,255,255,0.7);">{nb} règles · {nv} violations</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =====================================================================
    # SCORES DAMA/ISO 8000
    # =====================================================================

    st.subheader("📊 Scores DAMA / ISO 8000")

    if dama_scores:
        dama_cols = st.columns(6)
        for i, dim_name in enumerate(DAMA_DIMENSIONS):
            vals = [s.get(dim_name) for s in dama_scores.values() if s.get(dim_name) is not None]
            if vals:
                avg = np.mean(vals) * 100
                color = "#38ef7d" if avg >= 90 else "#F2C94C" if avg >= 70 else "#F2994A" if avg >= 50 else "#eb3349"
                dama_cols[i].markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: {color}15; border-radius: 8px; border: 1px solid {color}40;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: {color};">{avg:.0f}%</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">{dim_name}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                dama_cols[i].markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 1.4rem; font-weight: 700; color: rgba(255,255,255,0.3);">N/A</div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4);">{dim_name}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # =====================================================================
    # VUE PAR ATTRIBUT
    # =====================================================================

    st.subheader("📋 Contrats par attribut")

    for col_name, contract in contracts.items():
        col_viols = violations.get(col_name, [])
        nb_rules = len(contract.get("rules", []))
        status_icon = "✅" if len(col_viols) == 0 else "❌" if any(v.get("criticality") == "CRITIQUE" for v in col_viols) else "⚠️"

        with st.expander(
            f"{status_icon} **{col_name}** — {nb_rules} règles, {len(col_viols)} violation(s)",
            expanded=len(col_viols) > 0
        ):
            # Métadonnées
            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f"**Type:** `{contract.get('expected_type', 'N/A')}`")
            m2.markdown(f"**Nullable:** {'Oui' if contract.get('nullable', True) else 'Non'}")
            m3.markdown(f"**Unique:** {'Oui' if contract.get('unique', False) else 'Non'}")
            dama_s = dama_scores.get(col_name, {})
            calc_dims = [f"{k}: {v:.0%}" for k, v in dama_s.items() if v is not None]
            m4.markdown(f"**DAMA:** {', '.join(calc_dims) if calc_dims else 'N/A'}")

            # Règles groupées par dimension
            violated_names = {v["rule"] for v in col_viols}
            rules_by_dim = {}
            for rule in contract.get("rules", []):
                dim = rule.get("dimension", "—")
                rules_by_dim.setdefault(dim, []).append(rule)

            for dim in ["DB", "DP", "BR", "UP", "DAMA", "—"]:
                dim_rules = rules_by_dim.get(dim, [])
                if not dim_rules:
                    continue
                color = DIM_COLORS.get(dim, "rgba(255,255,255,0.5)")
                st.markdown(f"<span style='color: {color}; font-weight: 600;'>[{dim}]</span>", unsafe_allow_html=True)
                for rule in dim_rules:
                    icon = "❌" if rule["name"] in violated_names else "✅"
                    anomaly_id = rule.get("anomaly_id", "")
                    tag = f" `{anomaly_id}`" if anomaly_id else ""
                    st.markdown(f"- {icon}{tag} **{rule['name']}**: {rule['description']}")

            # Violations détaillées
            if col_viols:
                st.markdown("**Violations détectées :**")
                for v in sorted(col_viols, key=lambda x: CRITICALITY_ORDER.get(x.get("criticality", ""), 0), reverse=True):
                    crit = v.get("criticality", "MOYEN")
                    sev_color = SEVERITY_COLORS.get(crit, "#F2994A")
                    anomaly_tag = f" [{v.get('anomaly_id', '')}]" if v.get("anomaly_id") else ""
                    st.markdown(f"""
                    <div style="background: {sev_color}15; border-left: 3px solid {sev_color}; padding: 0.5rem 1rem; margin-bottom: 0.4rem; border-radius: 0 8px 8px 0;">
                        <span style="color: {sev_color}; font-weight: 700;">{crit}{anomaly_tag}</span> —
                        <span style="color: rgba(255,255,255,0.9);">{v['rule']}</span>:
                        <span style="color: rgba(255,255,255,0.7);">{v['message']}</span>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # =====================================================================
    # EXPORT
    # =====================================================================

    st.subheader("📤 Export")

    e1, e2 = st.columns(2)

    with e1:
        export_data = {
            "version": "2.0",
            "referentiel": "15 anomalies core + 6 DAMA + 4 dimensions causales",
            "generated_at": datetime.now().isoformat(),
            "contracts": contracts,
            "dama_scores": {k: {dk: dv for dk, dv in v.items() if dv is not None} for k, v in dama_scores.items()},
        }
        st.download_button(
            label="📥 Contrats JSON",
            data=json.dumps(export_data, ensure_ascii=False, indent=2, default=str),
            file_name=f"data_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with e2:
        if total_violations > 0:
            lines = [f"# Rapport de violations — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
            lines.append(f"**Total : {total_violations} violations sur {len(contracts)} attributs**\n")
            for dim in ["DB", "DP", "BR", "UP"]:
                if dim_violations[dim] > 0:
                    lines.append(f"- [{dim}] : {dim_violations[dim]} violations")
            lines.append("")
            for col_name, col_viols in violations.items():
                if col_viols:
                    lines.append(f"\n## {col_name}")
                    for v in sorted(col_viols, key=lambda x: CRITICALITY_ORDER.get(x.get("criticality", ""), 0), reverse=True):
                        aid = f" [{v.get('anomaly_id', '')}]" if v.get("anomaly_id") else ""
                        lines.append(f"- **{v.get('criticality', 'MOYEN')}**{aid} {v['rule']}: {v['message']}")
            st.download_button(
                label="📥 Rapport violations (MD)",
                data="\n".join(lines),
                file_name=f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.success("Aucune violation — rien à exporter")


# ============================================================================
# GÉNÉRATION AUTOMATIQUE AVEC RÉFÉRENTIEL COMPLET
# ============================================================================

def _auto_generate_contracts(df: pd.DataFrame) -> dict:
    """Génère des contrats couvrant les 15 anomalies core + DAMA."""
    contracts = {}
    col_config = _auto_detect_columns(df)

    for col in df.columns:
        series = df[col]
        total = len(series)
        expected_type = _infer_type(series)
        null_pct = series.isnull().mean() * 100

        contract = {
            "expected_type": expected_type,
            "nullable": bool(series.isnull().any()),
            "unique": bool(series.nunique() == len(series.dropna())) if len(series.dropna()) > 0 else False,
            "rules": [],
        }
        rules = contract["rules"]

        # ==================================================================
        # DB#1 : NULL dans colonnes obligatoires
        # ==================================================================
        threshold = 0.0 if null_pct == 0 else 10.0
        rules.append({
            "name": "null_threshold",
            "anomaly_id": "DB#1",
            "dimension": "DB",
            "description": f"Taux nulls ≤ {threshold}% (actuel: {null_pct:.1f}%)",
            "type": "null_check",
            "threshold": threshold,
        })

        # ==================================================================
        # DB#2 : Doublons clé primaire
        # ==================================================================
        if col in col_config["pk_columns"]:
            dup_count = series.duplicated(keep="first").sum()
            rules.append({
                "name": "pk_no_duplicates",
                "anomaly_id": "DB#2",
                "dimension": "DB",
                "description": f"Pas de doublons sur clé primaire (actuel: {dup_count})",
                "type": "pk_unique",
            })

        # ==================================================================
        # DB#3 : Formats email invalides
        # ==================================================================
        if col in col_config["email_columns"]:
            rules.append({
                "name": "email_format",
                "anomaly_id": "DB#3",
                "dimension": "DB",
                "description": "Format email valide (xxx@domain.tld)",
                "type": "email_format",
            })

        # ==================================================================
        # DB#4 : Valeurs hors domaine
        # ==================================================================
        if expected_type == "string":
            clean = series.dropna()
            if len(clean) > 0:
                nunique = clean.nunique()
                if nunique <= 30:
                    values = sorted(clean.unique().tolist())
                    rules.append({
                        "name": "allowed_values",
                        "anomaly_id": "DB#4",
                        "dimension": "DB",
                        "description": f"Valeurs autorisées ({nunique}): {', '.join(str(v) for v in values[:10])}{'...' if len(values) > 10 else ''}",
                        "type": "enum",
                        "values": [str(v) for v in values],
                    })

        # ==================================================================
        # DB#5 : Valeurs négatives interdites
        # ==================================================================
        if col in col_config["positive_columns"] and pd.api.types.is_numeric_dtype(series):
            neg_count = (pd.to_numeric(series, errors="coerce") < 0).sum()
            rules.append({
                "name": "no_negative",
                "anomaly_id": "DB#5",
                "dimension": "DB",
                "description": f"Pas de valeurs négatives (actuel: {neg_count})",
                "type": "no_negative",
            })

        # ==================================================================
        # DP#2 : Division par zéro
        # ==================================================================
        if col in col_config["denominator_columns"] and pd.api.types.is_numeric_dtype(series):
            zero_count = (pd.to_numeric(series, errors="coerce") == 0).sum()
            rules.append({
                "name": "no_zero_denominator",
                "anomaly_id": "DP#2",
                "dimension": "DP",
                "description": f"Pas de zéros (dénominateur potentiel, actuel: {zero_count})",
                "type": "no_zero",
            })

        # ==================================================================
        # DP#3 : Type données incorrect (types mixtes)
        # ==================================================================
        if expected_type == "string":
            non_null = series.dropna()
            if len(non_null) > 0:
                numeric_converted = pd.to_numeric(non_null, errors="coerce")
                numeric_rate = numeric_converted.notna().sum() / len(non_null)
                if 0.1 < numeric_rate < 0.9:
                    rules.append({
                        "name": "type_consistency",
                        "anomaly_id": "DP#3",
                        "dimension": "DP",
                        "description": f"Types mixtes détectés ({numeric_rate:.0%} numériques dans colonne texte)",
                        "type": "type_mix",
                        "numeric_rate": float(numeric_rate),
                    })

        # ==================================================================
        # BR#1 : Incohérences temporelles (multi-colonnes)
        # ==================================================================
        if col in col_config["date_start_columns"]:
            for end_col in col_config["date_end_columns"]:
                if end_col != col and end_col in df.columns:
                    rules.append({
                        "name": f"temporal_consistency_{end_col}",
                        "anomaly_id": "BR#1",
                        "dimension": "BR",
                        "description": f"{col} doit être ≤ {end_col}",
                        "type": "temporal_order",
                        "start_col": col,
                        "end_col": end_col,
                    })

        # ==================================================================
        # BR#2 : Valeurs hors bornes métier
        # ==================================================================
        if pd.api.types.is_numeric_dtype(series):
            clean = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean) > 0:
                q01, q99 = float(clean.quantile(0.01)), float(clean.quantile(0.99))
                rules.append({
                    "name": "business_range",
                    "anomaly_id": "BR#2",
                    "dimension": "BR",
                    "description": f"Valeurs dans [{q01:.2f}, {q99:.2f}] (bornes métier 1–99%)",
                    "type": "range",
                    "min": q01,
                    "max": q99,
                })

        # ==================================================================
        # BR#3 : Combinaisons interdites (détection auto)
        # ==================================================================
        # Détecté au niveau validation si config manuelle fournie
        # On génère la structure pour chaque colonne catégorielle
        # L'utilisateur pourra enrichir via JSON

        # ==================================================================
        # BR#4 : Obligations métier SI/ALORS (détection auto)
        # ==================================================================
        if col in col_config["conditional_required_columns"]:
            cond_col, cond_val = col_config["conditional_required_columns"][col]
            if cond_col in df.columns:
                rules.append({
                    "name": f"mandatory_if_{cond_col}",
                    "anomaly_id": "BR#4",
                    "dimension": "BR",
                    "description": f"SI {cond_col}={cond_val} ALORS {col} NOT NULL",
                    "type": "conditional_required",
                    "condition_col": cond_col,
                    "condition_val": cond_val,
                })

        # ==================================================================
        # UP#1 : Données obsolètes
        # ==================================================================
        if col in col_config["date_columns"]:
            rules.append({
                "name": "freshness",
                "anomaly_id": "UP#1",
                "dimension": "UP",
                "description": "Données de moins de 365 jours",
                "type": "freshness",
                "max_age_days": 365,
            })

        # ==================================================================
        # UP#2 : Granularité excessive
        # ==================================================================
        if expected_type == "string" and total > 0:
            unique_ratio = series.nunique() / total
            if unique_ratio > 0.9:
                rules.append({
                    "name": "granularity_excessive",
                    "anomaly_id": "UP#2",
                    "dimension": "UP",
                    "description": f"Granularité excessive ({unique_ratio:.0%} valeurs uniques)",
                    "type": "granularity_max",
                    "max_unique_ratio": 0.9,
                })

        # ==================================================================
        # UP#3 : Granularité insuffisante
        # ==================================================================
        if expected_type == "string" and total > 0:
            unique_ratio = series.nunique() / total
            nunique = series.nunique()
            if nunique <= 2 and total > 50:
                rules.append({
                    "name": "granularity_insufficient",
                    "anomaly_id": "UP#3",
                    "dimension": "UP",
                    "description": f"Granularité insuffisante ({nunique} valeurs uniques pour {total} lignes)",
                    "type": "granularity_min",
                    "min_unique": 3,
                })

        # ==================================================================
        # Outliers IQR (complément P_UP)
        # ==================================================================
        if pd.api.types.is_numeric_dtype(series):
            clean = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean) > 10:
                q1 = float(clean.quantile(0.25))
                q3 = float(clean.quantile(0.75))
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_count = int(((clean < lower) | (clean > upper)).sum())
                    if outlier_count > 0:
                        rules.append({
                            "name": "outlier_iqr",
                            "anomaly_id": "",
                            "dimension": "UP",
                            "description": f"Outliers IQR : {outlier_count} valeurs hors [{lower:.2f}, {upper:.2f}]",
                            "type": "outlier_iqr",
                            "lower": lower,
                            "upper": upper,
                        })

        # ==================================================================
        # Longueur max (string)
        # ==================================================================
        if expected_type == "string":
            clean = series.dropna()
            if len(clean) > 0:
                max_len = int(clean.str.len().max())
                rules.append({
                    "name": "max_length",
                    "anomaly_id": "",
                    "dimension": "DB",
                    "description": f"Longueur max ≤ {max_len} caractères",
                    "type": "length",
                    "max_length": max_len,
                })

        # ==================================================================
        # Unicité (DAMA Uniqueness)
        # ==================================================================
        if contract["unique"]:
            rules.append({
                "name": "uniqueness",
                "anomaly_id": "",
                "dimension": "DAMA",
                "description": "Toutes les valeurs doivent être uniques",
                "type": "unique",
            })

        contracts[col] = contract

    # ==================================================================
    # DP#1 : Calculs dérivés (multi-colonnes)
    # ==================================================================
    for formula_info in col_config.get("derived_formulas", []):
        target = formula_info["target"]
        if target in contracts:
            contracts[target]["rules"].append({
                "name": f"derived_calc_{formula_info['formula']}",
                "anomaly_id": "DP#1",
                "dimension": "DP",
                "description": f"Formule: {formula_info['description']}",
                "type": "derived_calc",
                "sources": formula_info["sources"],
                "target": target,
                "formula": formula_info["formula"],
            })

    return contracts


# ============================================================================
# VALIDATION AVEC RÉFÉRENTIEL COMPLET
# ============================================================================

def _validate_contracts(df: pd.DataFrame, contracts: dict) -> dict:
    """Valide le DataFrame contre les contrats enrichis."""
    violations = {}

    for col_name, contract in contracts.items():
        col_viols = []

        if col_name not in df.columns:
            col_viols.append({
                "rule": "column_exists", "anomaly_id": "DB#1",
                "dimension": "DB", "criticality": "CRITIQUE",
                "message": f"Colonne '{col_name}' absente du dataset",
            })
            violations[col_name] = col_viols
            continue

        series = df[col_name]
        total = len(series)

        for rule in contract.get("rules", []):
            rt = rule.get("type")
            aid = rule.get("anomaly_id", "")
            dim = rule.get("dimension", "")

            # ── DB#1: null_check ──────────────────────────────────────
            if rt == "null_check":
                null_pct = series.isnull().mean() * 100
                threshold = rule.get("threshold", 10.0)
                if null_pct > threshold:
                    col_viols.append({
                        "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                        "criticality": "CRITIQUE" if null_pct > 50 else "ÉLEVÉ" if null_pct > 20 else "MOYEN",
                        "message": f"Taux nulls {null_pct:.1f}% > seuil {threshold}%",
                        "affected_rows": int(series.isnull().sum()),
                    })

            # ── DB#2: pk_unique ───────────────────────────────────────
            elif rt == "pk_unique":
                dup_count = int(series.duplicated(keep="first").sum())
                if dup_count > 0:
                    dups = series[series.duplicated(keep=False)].value_counts().head(5)
                    col_viols.append({
                        "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                        "criticality": "CRITIQUE",
                        "message": f"{dup_count} doublons PK (top: {', '.join(str(v) for v in dups.index[:3])})",
                        "affected_rows": dup_count,
                    })

            # ── DB#3: email_format ────────────────────────────────────
            elif rt == "email_format":
                pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                non_null = series.dropna()
                if len(non_null) > 0:
                    invalid = non_null[~non_null.astype(str).str.match(pattern, na=False)]
                    if len(invalid) > 0:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "MOYEN",
                            "message": f"{len(invalid)} emails invalides (ex: {', '.join(str(v) for v in invalid.head(3).tolist())})",
                            "affected_rows": len(invalid),
                        })

            # ── DB#4: enum ────────────────────────────────────────────
            elif rt == "enum":
                clean = series.dropna()
                if len(clean) > 0:
                    allowed = set(rule.get("values", []))
                    invalid = clean[~clean.astype(str).isin(allowed)]
                    if len(invalid) > 0:
                        examples = invalid.unique()[:5]
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "ÉLEVÉ",
                            "message": f"{len(invalid)} hors domaine (ex: {', '.join(str(v) for v in examples)})",
                            "affected_rows": len(invalid),
                        })

            # ── DB#5: no_negative ─────────────────────────────────────
            elif rt == "no_negative":
                vals = pd.to_numeric(series, errors="coerce")
                neg_count = int((vals < 0).sum())
                if neg_count > 0:
                    col_viols.append({
                        "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                        "criticality": "MOYEN",
                        "message": f"{neg_count} valeurs négatives (min: {vals.min():.2f})",
                        "affected_rows": neg_count,
                    })

            # ── DP#2: no_zero ─────────────────────────────────────────
            elif rt == "no_zero":
                vals = pd.to_numeric(series, errors="coerce")
                zero_count = int((vals == 0).sum())
                if zero_count > 0:
                    col_viols.append({
                        "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                        "criticality": "MOYEN",
                        "message": f"{zero_count} zéros (division par zéro potentielle)",
                        "affected_rows": zero_count,
                    })

            # ── DP#3: type_mix ────────────────────────────────────────
            elif rt == "type_mix":
                non_null = series.dropna()
                if len(non_null) > 0:
                    numeric_converted = pd.to_numeric(non_null, errors="coerce")
                    numeric_rate = numeric_converted.notna().sum() / len(non_null)
                    if 0.1 < numeric_rate < 0.9:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "MOYEN",
                            "message": f"Types mixtes: {numeric_rate:.0%} numériques dans colonne texte",
                            "affected_rows": int(numeric_converted.isna().sum()),
                        })

            # ── BR#1: temporal_order ──────────────────────────────────
            elif rt == "temporal_order":
                end_col = rule.get("end_col", "")
                if end_col in df.columns:
                    try:
                        starts = pd.to_datetime(series, errors="coerce")
                        ends = pd.to_datetime(df[end_col], errors="coerce")
                        bad = ((starts > ends) & starts.notna() & ends.notna()).sum()
                        if bad > 0:
                            col_viols.append({
                                "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                                "criticality": "ÉLEVÉ",
                                "message": f"{int(bad)} lignes où {col_name} > {end_col}",
                                "affected_rows": int(bad),
                            })
                    except Exception:
                        pass

            # ── BR#2: range ───────────────────────────────────────────
            elif rt == "range":
                clean = pd.to_numeric(series, errors="coerce").dropna()
                if len(clean) > 0:
                    min_val = rule.get("min", float("-inf"))
                    max_val = rule.get("max", float("inf"))
                    out = int(((clean < min_val) | (clean > max_val)).sum())
                    if out > 0:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "CRITIQUE" if out > total * 0.1 else "ÉLEVÉ",
                            "message": f"{out} valeurs hors [{min_val:.2f}, {max_val:.2f}]",
                            "affected_rows": out,
                        })

            # ── BR#4: conditional_required ────────────────────────────
            elif rt == "conditional_required":
                cond_col = rule.get("condition_col", "")
                cond_val = rule.get("condition_val", "")
                if cond_col in df.columns:
                    violations_br4 = df[(df[cond_col] == cond_val) & series.isnull()]
                    if len(violations_br4) > 0:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "ÉLEVÉ",
                            "message": f"{len(violations_br4)} lignes: {cond_col}={cond_val} mais {col_name} est NULL",
                            "affected_rows": len(violations_br4),
                        })

            # ── UP#1: freshness ───────────────────────────────────────
            elif rt == "freshness":
                try:
                    dates = pd.to_datetime(series, errors="coerce")
                    max_age = rule.get("max_age_days", 365)
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=max_age)
                    obsolete = int((dates < cutoff).sum())
                    if obsolete > 0:
                        oldest = dates.min()
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "ÉLEVÉ" if obsolete > total * 0.5 else "MOYEN",
                            "message": f"{obsolete} données obsolètes (> {max_age}j, plus ancienne: {oldest.strftime('%Y-%m-%d') if pd.notna(oldest) else 'N/A'})",
                            "affected_rows": obsolete,
                        })
                except Exception:
                    pass

            # ── UP#2: granularity_max ─────────────────────────────────
            elif rt == "granularity_max":
                if total > 0:
                    ratio = series.nunique() / total
                    threshold = rule.get("max_unique_ratio", 0.9)
                    if ratio > threshold:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "FAIBLE",
                            "message": f"Granularité excessive: {ratio:.0%} uniques (seuil: {threshold:.0%})",
                            "affected_rows": 0,
                        })

            # ── UP#3: granularity_min ─────────────────────────────────
            elif rt == "granularity_min":
                nunique = series.nunique()
                min_unique = rule.get("min_unique", 3)
                if nunique < min_unique:
                    col_viols.append({
                        "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                        "criticality": "MOYEN",
                        "message": f"Granularité insuffisante: {nunique} uniques (min attendu: {min_unique})",
                        "affected_rows": 0,
                    })

            # ── Outlier IQR ───────────────────────────────────────────
            elif rt == "outlier_iqr":
                clean = pd.to_numeric(series, errors="coerce").dropna()
                if len(clean) > 10:
                    lower = rule.get("lower", 0)
                    upper = rule.get("upper", 0)
                    out = int(((clean < lower) | (clean > upper)).sum())
                    if out > 0:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "MOYEN" if out < total * 0.05 else "ÉLEVÉ",
                            "message": f"{out} outliers IQR hors [{lower:.2f}, {upper:.2f}]",
                            "affected_rows": out,
                        })

            # ── Length ────────────────────────────────────────────────
            elif rt == "length":
                clean = series.dropna()
                if len(clean) > 0:
                    max_length = rule.get("max_length", 255)
                    too_long = int((clean.str.len() > max_length).sum())
                    if too_long > 0:
                        col_viols.append({
                            "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                            "criticality": "MOYEN",
                            "message": f"{too_long} valeurs > {max_length} caractères",
                            "affected_rows": too_long,
                        })

            # ── Unique ────────────────────────────────────────────────
            elif rt == "unique":
                dup_count = int(series.duplicated(keep="first").sum())
                if dup_count > 0:
                    col_viols.append({
                        "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                        "criticality": "ÉLEVÉ",
                        "message": f"{dup_count} doublons (unicité attendue)",
                        "affected_rows": dup_count,
                    })

            # ── Derived calc (DP#1) ───────────────────────────────────
            elif rt == "derived_calc":
                formula = rule.get("formula", "")
                sources = rule.get("sources", [])
                target = rule.get("target", col_name)
                if all(c in df.columns for c in sources) and target in df.columns:
                    try:
                        errors = _check_derived_formula(df, sources, target, formula)
                        if errors > 0:
                            col_viols.append({
                                "rule": rule["name"], "anomaly_id": aid, "dimension": dim,
                                "criticality": "ÉLEVÉ",
                                "message": f"{errors} lignes: formule '{formula}' non respectée",
                                "affected_rows": errors,
                            })
                    except Exception:
                        pass

        violations[col_name] = col_viols

    return violations


# ============================================================================
# SCORES DAMA / ISO 8000
# ============================================================================

def _compute_dama_scores(df: pd.DataFrame, contracts: dict, violations: dict) -> dict:
    """Calcule les 6 dimensions DAMA pour chaque colonne."""
    scores = {}

    for col_name in contracts:
        if col_name not in df.columns:
            continue

        series = df[col_name]
        total = len(series)
        if total == 0:
            continue

        # Complétude : 1 - taux nulls
        completude = 1 - (series.isnull().sum() / total)

        # Unicité : 1 - taux doublons
        dup_count = series.duplicated(keep="first").sum()
        unicite = 1 - (dup_count / total)

        # Validité : basée sur les violations DB#4 (enum) et DB#3 (email)
        validity_violations = sum(
            v.get("affected_rows", 0) for v in violations.get(col_name, [])
            if v.get("anomaly_id") in ("DB#4", "DB#3", "DB#5")
        )
        validite = 1 - (validity_violations / total) if total > 0 else None

        # Cohérence : basée sur violations BR (règles métier)
        br_violations = sum(
            v.get("affected_rows", 0) for v in violations.get(col_name, [])
            if v.get("dimension") == "BR"
        )
        coherence = 1 - (br_violations / total) if br_violations > 0 else None

        # Fraîcheur : basée sur UP#1
        freshness_violations = [
            v for v in violations.get(col_name, [])
            if v.get("anomaly_id") == "UP#1"
        ]
        if freshness_violations:
            obsolete = freshness_violations[0].get("affected_rows", 0)
            fraicheur = 1 - (obsolete / total)
        else:
            fraicheur = None

        # Exactitude : basée sur DP#1 + DP#3
        dp_violations = sum(
            v.get("affected_rows", 0) for v in violations.get(col_name, [])
            if v.get("dimension") == "DP"
        )
        exactitude = 1 - (dp_violations / total) if dp_violations > 0 else None

        scores[col_name] = {
            "Complétude": round(completude, 4),
            "Cohérence": round(coherence, 4) if coherence is not None else None,
            "Exactitude": round(exactitude, 4) if exactitude is not None else None,
            "Fraîcheur": round(fraicheur, 4) if fraicheur is not None else None,
            "Validité": round(validite, 4) if validite is not None and validity_violations > 0 else None,
            "Unicité": round(unicite, 4),
        }

    return scores


# ============================================================================
# HELPERS
# ============================================================================

def _infer_type(series: pd.Series) -> str:
    """Détermine le type logique d'une colonne."""
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


def _auto_detect_columns(df: pd.DataFrame) -> dict:
    """Détecte automatiquement les rôles des colonnes."""
    config = {
        "pk_columns": [],
        "email_columns": [],
        "date_columns": [],
        "date_start_columns": [],
        "date_end_columns": [],
        "positive_columns": [],
        "denominator_columns": [],
        "conditional_required_columns": {},
        "derived_formulas": [],
    }

    for col in df.columns:
        cl = col.lower()

        # Clés primaires
        if any(kw in cl for kw in ["id", "matricule", "code_unique", "pk", "identifiant"]):
            if df[col].nunique() == len(df[col].dropna()):
                config["pk_columns"].append(col)

        # Emails
        if any(kw in cl for kw in ["email", "mail", "courriel"]):
            config["email_columns"].append(col)

        # Dates
        if any(kw in cl for kw in ["date", "datetime", "timestamp", "jour", "dt_"]):
            config["date_columns"].append(col)
            if any(kw in cl for kw in ["debut", "start", "entree", "embauche", "creation", "ouverture"]):
                config["date_start_columns"].append(col)
            if any(kw in cl for kw in ["fin", "end", "sortie", "depart", "cloture", "fermeture"]):
                config["date_end_columns"].append(col)

        # Aussi détecter les datetimes par type pandas
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if col not in config["date_columns"]:
                config["date_columns"].append(col)

        # Champs positifs
        if any(kw in cl for kw in [
            "age", "anciennete", "salaire", "montant", "prix", "quantite",
            "nombre", "count", "nb_", "effectif", "taux", "prime", "indemnite",
        ]):
            config["positive_columns"].append(col)

        # Dénominateurs potentiels
        if any(kw in cl for kw in [
            "cout", "diviseur", "denominat", "base_", "total", "effectif",
        ]):
            config["denominator_columns"].append(col)

    # Détection formules dérivées (heuristiques)
    cols_lower = {c.lower(): c for c in df.columns}

    # age = f(date_naissance)
    for age_kw in ["age", "anciennete"]:
        for col in df.columns:
            if age_kw in col.lower() and pd.api.types.is_numeric_dtype(df[col]):
                for date_col in config["date_columns"]:
                    dcl = date_col.lower()
                    if any(kw in dcl for kw in ["naissance", "birth", "embauche", "entree"]):
                        config["derived_formulas"].append({
                            "target": col,
                            "sources": [date_col],
                            "formula": "age_from_birthdate",
                            "description": f"{col} = (now - {date_col}) / 365.25",
                        })

    # montant_ttc = montant_ht * (1 + tva)
    if "montant_ht" in cols_lower and "montant_ttc" in cols_lower:
        tva_col = cols_lower.get("taux_tva") or cols_lower.get("tva")
        if tva_col:
            config["derived_formulas"].append({
                "target": cols_lower["montant_ttc"],
                "sources": [cols_lower["montant_ht"], tva_col],
                "formula": "montant_ttc",
                "description": f"montant_ttc = montant_ht × (1 + tva)",
            })

    # Obligations conditionnelles (heuristiques)
    for col in df.columns:
        cl = col.lower()
        # SI statut='actif' ALORS date_sortie peut être null (pas de rule)
        # SI ancienneté > 0 ALORS prime_ancienneté NOT NULL
        if "prime" in cl:
            for other in df.columns:
                ol = other.lower()
                if "anciennete" in ol and pd.api.types.is_numeric_dtype(df[other]):
                    # Pas de condition automatique trop agressive
                    pass
        if "statut" in cl or "status" in cl:
            # SI statut est catégoriel, marquer les colonnes dépendantes
            for other in df.columns:
                ol = other.lower()
                if any(kw in ol for kw in ["date_sortie", "date_fin", "date_depart"]):
                    # SI statut='inactif' ALORS date_sortie NOT NULL
                    vals = df[col].dropna().unique()
                    for v in vals:
                        vl = str(v).lower()
                        if any(kw in vl for kw in ["inactif", "inactive", "sorti", "termine"]):
                            config["conditional_required_columns"][other] = (col, v)

    return config


def _check_derived_formula(df: pd.DataFrame, sources: list, target: str, formula: str) -> int:
    """Vérifie une formule dérivée et retourne le nombre d'erreurs."""
    if formula == "age_from_birthdate" and len(sources) >= 1:
        dates = pd.to_datetime(df[sources[0]], errors="coerce")
        expected = (pd.Timestamp.now() - dates).dt.days / 365.25
        actual = pd.to_numeric(df[target], errors="coerce")
        mask = expected.notna() & actual.notna()
        errors = (abs(expected[mask] - actual[mask]) > 1).sum()
        return int(errors)

    if formula == "montant_ttc" and len(sources) >= 2:
        ht = pd.to_numeric(df[sources[0]], errors="coerce")
        tva = pd.to_numeric(df[sources[1]], errors="coerce")
        expected = ht * (1 + tva)
        actual = pd.to_numeric(df[target], errors="coerce")
        mask = expected.notna() & actual.notna()
        errors = (~np.isclose(expected[mask], actual[mask], rtol=0.01, atol=0.01)).sum()
        return int(errors)

    return 0
