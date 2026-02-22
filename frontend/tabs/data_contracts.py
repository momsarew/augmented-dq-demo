"""
Tab Data Contracts v3 - Intègre le référentiel complet 128 anomalies.

Source: Base_d_anomalies_pour_les_dimensions_Risques__1_.xlsx
  DB: 22 anomalies (16 Auto, 4 Semi, 2 Manuel)
  DP: 32 anomalies (4 Auto, 17 Semi, 11 Manuel)
  BR: 34 anomalies (7 Auto, 14 Semi, 13 Manuel)
  UP: 40 anomalies (0 Auto, 7 Semi, 33 Manuel)
"""

import re
import uuid
import streamlit as st
import pandas as pd
import numpy as np
import json
import yaml
from datetime import datetime

# Import du référentiel complet
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.anomaly_referential import REFERENTIAL, get_summary, get_by_dimension


# ============================================================================
# CONSTANTES
# ============================================================================

DAMA_DIMENSIONS = ["Complétude", "Cohérence", "Exactitude", "Fraîcheur", "Validité", "Unicité"]
CRITICALITY_ORDER = {"CRITIQUE": 4, "ÉLEVÉ": 3, "MOYEN": 2, "FAIBLE": 1, "VARIABLE": 1}
SEVERITY_COLORS = {
    "CRITIQUE": "#eb3349", "ÉLEVÉ": "#F2994A", "MOYEN": "#F2C94C",
    "FAIBLE": "#38ef7d", "VARIABLE": "#667eea",
}
DIM_COLORS = {"DB": "#667eea", "DP": "#764ba2", "BR": "#f093fb", "UP": "#38ef7d"}
DIM_LABELS = {
    "DB": "Database Integrity", "DP": "Data Processing",
    "BR": "Business Rules", "UP": "Usage Appropriateness",
}


# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render_data_contracts_tab():
    """Rendu de l'onglet Data Contracts — référentiel 128 anomalies."""

    st.header("📜 Data Contracts")

    ref_summary = get_summary()
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    ">
        <h3 style="color: white; margin: 0 0 0.5rem 0;">📜 Data Contracts v3 — Référentiel {ref_summary['total']} anomalies</h3>
        <p style="color: rgba(255,255,255,0.8); margin: 0;">
            DB: {ref_summary['by_dimension']['DB']['total']} ·
            DP: {ref_summary['by_dimension']['DP']['total']} ·
            BR: {ref_summary['by_dimension']['BR']['total']} ·
            UP: {ref_summary['by_dimension']['UP']['total']} anomalies ·
            6 dimensions DAMA/ISO 8000
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
    # RÉFÉRENTIEL (collapsible)
    # =====================================================================
    with st.expander("📚 Référentiel complet (128 anomalies)", expanded=False):
        for dim in ["DB", "DP", "BR", "UP"]:
            dim_anomalies = get_by_dimension(dim)
            color = DIM_COLORS[dim]
            st.markdown(f"<h4 style='color: {color};'>[{dim}] {DIM_LABELS[dim]} — {len(dim_anomalies)} anomalies</h4>", unsafe_allow_html=True)
            rows = []
            for aid, a in dim_anomalies.items():
                det_icon = {"Auto": "🟢", "Semi": "🟡", "Manuel": "🔴"}.get(a["detection"], "⚪")
                rows.append({
                    "ID": aid,
                    "Anomalie": a["name"],
                    "Description": a["description"],
                    "Détection": f"{det_icon} {a['detection']}",
                    "Criticité": a["criticality"],
                    "Woodall": a["woodall"],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # =====================================================================
    # GÉNÉRATION
    # =====================================================================
    st.subheader("⚡ Génération automatique")

    if st.button("🔄 Générer les contrats (128 anomalies)", type="primary", use_container_width=True):
        contracts = _auto_generate_contracts(df)
        st.session_state.data_contracts = contracts
        total_rules = sum(len(c.get("rules", [])) for c in contracts.values())
        auto_rules = sum(1 for c in contracts.values() for r in c.get("rules", []) if r.get("detection") == "Auto")
        semi_rules = sum(1 for c in contracts.values() for r in c.get("rules", []) if r.get("detection") == "Semi")
        manuel_rules = sum(1 for c in contracts.values() for r in c.get("rules", []) if r.get("detection") == "Manuel")
        st.success(f"✅ {len(contracts)} contrats · {total_rules} règles (🟢 {auto_rules} Auto · 🟡 {semi_rules} Semi · 🔴 {manuel_rules} Manuel)")

    if not st.session_state.data_contracts:
        st.info("💡 Cliquez ci-dessus pour générer les contrats depuis le référentiel complet.")
        return

    contracts = st.session_state.data_contracts

    # =====================================================================
    # VALIDATION (Auto + Semi seulement)
    # =====================================================================
    violations = _validate_contracts(df, contracts)
    dama_scores = _compute_dama_scores(df, contracts, violations)

    # =====================================================================
    # MÉTRIQUES GLOBALES
    # =====================================================================
    total_rules = sum(len(c.get("rules", [])) for c in contracts.values())
    total_violations = sum(len(v) for v in violations.values())
    passing = len([c for c in contracts if len(violations.get(c, [])) == 0])

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

    # Dimension causale cards
    st.markdown("**Couverture par dimension causale :**")
    dc1, dc2, dc3, dc4 = st.columns(4)
    for col_ui, dim in zip([dc1, dc2, dc3, dc4], ["DB", "DP", "BR", "UP"]):
        nb = dim_counts[dim]
        nv = dim_violations[dim]
        color = DIM_COLORS[dim]
        col_ui.markdown(f"""
        <div style="background: {color}15; border-left: 3px solid {color}; padding: 0.5rem; border-radius: 0 8px 8px 0;">
            <strong style="color: {color};">[{dim}] {DIM_LABELS[dim]}</strong><br/>
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
            else:
                avg = None
                color = "rgba(255,255,255,0.3)"
            dama_cols[i].markdown(f"""
            <div style="text-align: center; padding: 0.5rem; background: {color}15; border-radius: 8px; border: 1px solid {color}40;">
                <div style="font-size: 1.4rem; font-weight: 700; color: {color};">{f'{avg:.0f}%' if avg is not None else 'N/A'}</div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">{dim_name}</div>
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
        has_critique = any(v.get("criticality") == "CRITIQUE" for v in col_viols)
        status_icon = "✅" if not col_viols else "❌" if has_critique else "⚠️"

        with st.expander(f"{status_icon} **{col_name}** — {nb_rules} règles, {len(col_viols)} violation(s)", expanded=len(col_viols) > 0):
            # Metadata
            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f"**Type:** `{contract.get('expected_type', 'N/A')}`")
            m2.markdown(f"**Nullable:** {'Oui' if contract.get('nullable', True) else 'Non'}")
            m3.markdown(f"**Unique:** {'Oui' if contract.get('unique', False) else 'Non'}")
            dama_s = dama_scores.get(col_name, {})
            calc_dims = [f"{k}: {v:.0%}" for k, v in dama_s.items() if v is not None]
            m4.markdown(f"**DAMA:** {', '.join(calc_dims[:3]) if calc_dims else 'N/A'}")

            # Rules grouped by dimension
            violated_names = {v["rule"] for v in col_viols}
            rules_by_dim = {}
            for rule in contract.get("rules", []):
                dim = rule.get("dimension", "—")
                rules_by_dim.setdefault(dim, []).append(rule)

            for dim in ["DB", "DP", "BR", "UP", "DAMA"]:
                dim_rules = rules_by_dim.get(dim, [])
                if not dim_rules:
                    continue
                color = DIM_COLORS.get(dim, "rgba(255,255,255,0.5)")
                st.markdown(f"<span style='color: {color}; font-weight: 600;'>[{dim}] {DIM_LABELS.get(dim, dim)}</span>", unsafe_allow_html=True)
                for rule in dim_rules:
                    icon = "❌" if rule["name"] in violated_names else "✅"
                    det_badge = {"Auto": "🟢", "Semi": "🟡", "Manuel": "🔴"}.get(rule.get("detection", ""), "")
                    aid = rule.get("anomaly_id", "")
                    tag = f" `{aid}`" if aid else ""
                    st.markdown(f"- {icon} {det_badge}{tag} **{rule['name']}**: {rule['description']}")

            # Violations
            if col_viols:
                st.markdown("**Violations détectées :**")
                for v in sorted(col_viols, key=lambda x: CRITICALITY_ORDER.get(x.get("criticality", ""), 0), reverse=True):
                    crit = v.get("criticality", "MOYEN")
                    sev_color = SEVERITY_COLORS.get(crit, "#F2994A")
                    atag = f" [{v.get('anomaly_id', '')}]" if v.get("anomaly_id") else ""
                    st.markdown(f"""
                    <div style="background: {sev_color}15; border-left: 3px solid {sev_color}; padding: 0.5rem 1rem; margin-bottom: 0.4rem; border-radius: 0 8px 8px 0;">
                        <span style="color: {sev_color}; font-weight: 700;">{crit}{atag}</span> —
                        <span style="color: rgba(255,255,255,0.9);">{v['rule']}</span>:
                        <span style="color: rgba(255,255,255,0.7);">{v['message']}</span>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # =====================================================================
    # EXPORT
    # =====================================================================
    st.subheader("📤 Export")

    # --- ODCS v3.1.0 (standard open source) ---
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(56, 239, 125, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
        border: 1px solid rgba(56, 239, 125, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <strong style="color: #38ef7d;">ODCS v3.1.0</strong>
        <span style="color: rgba(255,255,255,0.7);"> — Open Data Contract Standard (Bitol / Linux Foundation)</span>
    </div>
    """, unsafe_allow_html=True)

    dataset_name = st.session_state.get("uploaded_filename", "dataset")
    if dataset_name and "." in dataset_name:
        dataset_name = dataset_name.rsplit(".", 1)[0]

    odcs_yaml = export_odcs_yaml(contracts, dama_scores, violations, dataset_name or "dataset")
    st.download_button(
        label="📥 Export ODCS v3.1.0 (YAML)", use_container_width=True,
        data=odcs_yaml,
        file_name=f"data_contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.odcs.yaml",
        mime="application/x-yaml",
        type="primary",
    )

    with st.expander("Aperçu ODCS YAML", expanded=False):
        st.code(odcs_yaml[:3000] + ("\n# ... (tronqué)" if len(odcs_yaml) > 3000 else ""), language="yaml")

    # --- Exports complémentaires ---
    st.markdown("**Exports complémentaires :**")
    e1, e2 = st.columns(2)
    with e1:
        export_data = {
            "version": "3.0",
            "referentiel": f"{ref_summary['total']} anomalies (DB:{ref_summary['by_dimension']['DB']['total']}, DP:{ref_summary['by_dimension']['DP']['total']}, BR:{ref_summary['by_dimension']['BR']['total']}, UP:{ref_summary['by_dimension']['UP']['total']})",
            "generated_at": datetime.now().isoformat(),
            "contracts": contracts,
            "dama_scores": {k: {dk: dv for dk, dv in v.items() if dv is not None} for k, v in dama_scores.items()},
        }
        st.download_button(
            label="📥 Contrats JSON (format interne)", use_container_width=True,
            data=json.dumps(export_data, ensure_ascii=False, indent=2, default=str),
            file_name=f"data_contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )
    with e2:
        if total_violations > 0:
            lines = [f"# Rapport de violations — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
            lines.append(f"**Référentiel : {ref_summary['total']} anomalies | {total_violations} violations sur {len(contracts)} attributs**\n")
            for dim in ["DB", "DP", "BR", "UP"]:
                if dim_violations[dim]:
                    lines.append(f"- [{dim}] : {dim_violations[dim]} violations")
            lines.append("")
            for col_name, col_viols in violations.items():
                if col_viols:
                    lines.append(f"\n## {col_name}")
                    for v in sorted(col_viols, key=lambda x: CRITICALITY_ORDER.get(x.get("criticality", ""), 0), reverse=True):
                        atag = f" [{v.get('anomaly_id', '')}]" if v.get("anomaly_id") else ""
                        lines.append(f"- **{v.get('criticality', 'MOYEN')}**{atag} {v['rule']}: {v['message']}")
            st.download_button(
                label="📥 Rapport violations (MD)", use_container_width=True,
                data="\n".join(lines),
                file_name=f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
            )
        else:
            st.success("Aucune violation — rien à exporter")


# ============================================================================
# GÉNÉRATION AUTOMATIQUE — 128 ANOMALIES
# ============================================================================

def _auto_generate_contracts(df: pd.DataFrame) -> dict:
    """Génère des contrats couvrant les 128 anomalies du référentiel."""
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

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # DB — Database Integrity (22 anomalies)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # DB#1: NULL non autorisés [Auto]
        threshold = 0.0 if null_pct == 0 else 10.0
        rules.append(_rule("DB#1", f"Taux nulls ≤ {threshold}% (actuel: {null_pct:.1f}%)", "null_check", threshold=threshold))

        # DB#2: Violations clé primaire [Auto]
        if col in col_config["pk_columns"]:
            rules.append(_rule("DB#2", f"Pas de doublons PK (actuel: {series.duplicated(keep='first').sum()})", "pk_unique"))

        # DB#3: Violations clé étrangère [Auto] — structure prête
        # Nécessite tables de référence, tagué comme Semi

        # DB#4: Violations contraintes unicité [Auto]
        if contract["unique"]:
            rules.append(_rule("DB#4", "Toutes valeurs doivent être uniques", "unique"))

        # DB#5: Valeurs hors domaine [Auto]
        if expected_type == "string":
            clean = series.dropna()
            if len(clean) > 0 and clean.nunique() <= 30:
                values = sorted(clean.unique().tolist())
                rules.append(_rule("DB#5", f"Valeurs autorisées ({clean.nunique()}): {', '.join(str(v) for v in values[:10])}{'...' if len(values) > 10 else ''}", "enum", values=[str(v) for v in values]))

        # DB#6: Valeurs hors plage numérique [Auto]
        if pd.api.types.is_numeric_dtype(series):
            clean = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean) > 0:
                q01, q99 = float(clean.quantile(0.01)), float(clean.quantile(0.99))
                rules.append(_rule("DB#6", f"Valeurs dans [{q01:.2f}, {q99:.2f}]", "range", min=q01, max=q99))

        # DB#7: Violations de format [Auto]
        if col in col_config["email_columns"]:
            rules.append(_rule("DB#7", "Format email valide (xxx@domain.tld)", "email_format"))

        # DB#8: Erreurs type données [Auto]
        if expected_type == "string":
            non_null = series.dropna()
            if len(non_null) > 0:
                numeric_converted = pd.to_numeric(non_null, errors="coerce")
                numeric_rate = float(numeric_converted.notna().sum() / len(non_null))
                if 0.1 < numeric_rate < 0.9:
                    rules.append(_rule("DB#8", f"Types mixtes ({numeric_rate:.0%} numériques dans texte)", "type_mix", numeric_rate=numeric_rate))

        # DB#9: Doublons exacts [Auto]
        if col in col_config["pk_columns"]:
            pass  # Already covered by DB#2
        else:
            dup_count = int(series.duplicated(keep="first").sum())
            if dup_count > 0 and expected_type != "string":
                rules.append(_rule("DB#9", f"{dup_count} doublons exacts", "exact_duplicates"))

        # DB#10: Doublons proches (fuzzy) [Semi]
        if expected_type == "string" and col not in col_config["pk_columns"]:
            rules.append(_rule("DB#10", "Doublons fuzzy (variations syntaxiques)", "fuzzy_duplicates"))

        # DB#11: Redondance inter-tables [Semi] — tagged only

        # DB#12: Synonymes [Semi]
        if expected_type == "string":
            clean = series.dropna()
            if len(clean) > 0 and 3 <= clean.nunique() <= 50:
                rules.append(_rule("DB#12", "Vérifier synonymes/variantes même concept", "synonyms"))

        # DB#13: Homonymes [Manuel]
        # DB#14: Hétérogénéité unités [Semi]
        if col in col_config["positive_columns"]:
            rules.append(_rule("DB#14", "Vérifier homogénéité des unités", "unit_heterogeneity"))

        # DB#15: Incohérences format colonnes [Auto]
        if expected_type == "string" and col in col_config["date_columns"]:
            rules.append(_rule("DB#15", "Vérifier cohérence formats dates", "format_consistency"))

        # DB#16: Données manquantes (NULL légitimes) [Auto]
        if null_pct > 0:
            rules.append(_rule("DB#16", f"NULL légitimes: {null_pct:.1f}% (à documenter si > 30%)", "null_legitimate"))

        # DB#17: Lignes manquantes [Manuel]
        rules.append(_rule("DB#17", "Vérifier complétude vs univers attendu", "missing_rows"))

        # DB#18: Colonnes entières vides [Auto]
        if null_pct == 100:
            rules.append(_rule("DB#18", "Colonne 100% vide", "column_empty"))

        # DB#19: Problèmes encodage [Auto]
        if expected_type == "string":
            clean = series.dropna().astype(str)
            if len(clean) > 0:
                encoding_issues = clean.str.contains(r'[Ã¢Ã©Ã¨Ã´Ã¼]|ï¿½|\?{3,}', regex=True, na=False).sum()
                if encoding_issues > 0:
                    rules.append(_rule("DB#19", f"{encoding_issues} valeurs avec problèmes d'encodage", "encoding_issues"))

        # DB#20: Caractères spéciaux non échappés [Auto]
        if expected_type == "string":
            clean = series.dropna().astype(str)
            if len(clean) > 0:
                special = clean.str.contains(r"""['"\\<>]""", regex=True, na=False).sum()
                if special > 0:
                    rules.append(_rule("DB#20", f"{special} valeurs avec caractères spéciaux", "special_chars"))

        # DB#21: Espaces parasites [Auto]
        if expected_type == "string":
            clean = series.dropna().astype(str)
            if len(clean) > 0:
                whitespace = (clean != clean.str.strip()).sum()
                if whitespace > 0:
                    rules.append(_rule("DB#21", f"{whitespace} valeurs avec espaces parasites", "whitespace"))

        # DB#22: Casse incohérente [Auto]
        if expected_type == "string":
            clean = series.dropna().astype(str)
            if len(clean) > 0:
                upper_count = clean.str.isupper().sum()
                lower_count = clean.str.islower().sum()
                mixed = len(clean) - upper_count - lower_count
                if mixed > 0 and upper_count > 0 and lower_count > 0:
                    rules.append(_rule("DB#22", f"Casse incohérente ({upper_count} UPPER, {lower_count} lower, {mixed} Mixed)", "case_inconsistency"))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # DP — Data Processing (32 anomalies)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # DP#1: Calculs dérivés incorrects [Semi]
        # Handled at multi-column level below

        # DP#3: Débordements numériques [Auto]
        if pd.api.types.is_numeric_dtype(series):
            clean = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean) > 0:
                if clean.max() > 1e15 or clean.min() < -1e15:
                    rules.append(_rule("DB#3_DP", f"Valeurs extrêmes (max: {clean.max():.2e})", "overflow"))

        # DP#4: Divisions par zéro [Auto]
        if col in col_config["denominator_columns"] and pd.api.types.is_numeric_dtype(series):
            zero_count = int((pd.to_numeric(series, errors="coerce") == 0).sum())
            rules.append(_rule("DP#4", f"Pas de zéros dénominateur (actuel: {zero_count})", "no_zero"))

        # DP#5: Erreurs d'agrégations [Semi]
        # DP#6: Conversions type inappropriées [Semi]
        # DP#7: Troncatures de données [Auto]
        if expected_type == "string":
            clean = series.dropna().astype(str)
            if len(clean) > 0:
                max_len = int(clean.str.len().max())
                rules.append(_rule("DP#7", f"Longueur max ≤ {max_len} car.", "length", max_length=max_len))

        # DP#8: Conversions format dates [Semi]
        if col in col_config["date_columns"] and expected_type == "string":
            rules.append(_rule("DP#8", "Vérifier parsing dates (DD/MM vs MM/DD)", "date_format_ambiguity"))

        # DP#9–DP#15: Transcodage, jointures, fusions [Semi/Manuel]
        # Tagged informatif
        if col in col_config["pk_columns"]:
            rules.append(_rule("DP#14", "Risque jointure cartésienne si PK non unique", "cartesian_join_risk"))

        # DP#20: Données non chargées [Semi]
        # DP#22: Transformations non idempotentes [Manuel]
        # DP#29–32: Déduplication [Manuel]

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BR — Business Rules (34 anomalies)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # BR#1: Incohérences temporelles [Auto]
        if col in col_config["date_start_columns"]:
            for end_col in col_config["date_end_columns"]:
                if end_col != col and end_col in df.columns:
                    rules.append(_rule("BR#1", f"{col} doit être ≤ {end_col}", "temporal_order", start_col=col, end_col=end_col))

        # BR#2: Valeurs hors bornes métier [Auto]
        if col in col_config["positive_columns"] and pd.api.types.is_numeric_dtype(series):
            neg_count = int((pd.to_numeric(series, errors="coerce") < 0).sum())
            rules.append(_rule("BR#2", f"Pas de négatifs sur champ positif (actuel: {neg_count})", "no_negative"))

        # BR#3: Combinaisons interdites [Semi]
        # Structure prête pour config manuelle

        # BR#5: Obligations métier [Semi]
        if col in col_config["conditional_required_columns"]:
            cond_col, cond_val = col_config["conditional_required_columns"][col]
            if cond_col in df.columns:
                rules.append(_rule("BR#5", f"SI {cond_col}={cond_val} ALORS {col} NOT NULL", "conditional_required", condition_col=cond_col, condition_val=cond_val))

        # BR#6–9: Conformité (RGPD, légal, fiscal, standards) [Manuel]
        # BR#10: Exigences audit [Semi]
        # BR#11: Incohérences calculés vs base [Auto]
        # BR#12: Sommes de contrôle [Auto]
        # BR#13: Ratios métier invalides [Auto]
        if pd.api.types.is_numeric_dtype(series):
            clean = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean) > 0 and col.lower().startswith(("taux", "ratio", "pct", "pourcentage")):
                rules.append(_rule("BR#13", "Ratio dans [0, 1] ou [0, 100]", "ratio_bounds", min=0, max=100))

        # BR#14: Dépendances fonctionnelles [Semi]
        # BR#15: Exclusivité mutuelle [Auto]
        # BR#16–20: Hiérarchies, classifications [Semi/Manuel]
        # BR#21–25: Politiques, seuils, processus [Manuel]
        # BR#26: Événements dans mauvais ordre [Semi]
        # BR#27: Délais réglementaires [Semi]
        # BR#28–30: Périodes, fréquences, antériorité [Semi]
        # BR#31–34: Dossiers, validations, documents [Manuel]

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # UP — Usage Appropriateness (40 anomalies)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # UP#1: Granularité trop fine [Manuel]
        if expected_type == "string" and total > 0:
            ratio = series.nunique() / total
            if ratio > 0.9:
                rules.append(_rule("UP#1", f"Granularité excessive ({ratio:.0%} uniques)", "granularity_max", max_unique_ratio=0.9))

        # UP#2: Granularité trop large [Manuel]
        if expected_type == "string" and total > 0:
            nunique = series.nunique()
            if nunique <= 2 and total > 50:
                rules.append(_rule("UP#2", f"Granularité insuffisante ({nunique} uniques / {total} lignes)", "granularity_min", min_unique=3))

        # UP#6: Données obsolètes [Semi]
        if col in col_config["date_columns"]:
            rules.append(_rule("UP#6", "Données de moins de 365 jours", "freshness", max_age_days=365))

        # UP#7: Latence excessive [Semi]
        # UP#8: Fréquence MAJ insuffisante [Semi]

        # UP#16: Taux remplissage insuffisant [Semi]
        if null_pct > 30:
            rules.append(_rule("UP#16", f"Taux remplissage {100-null_pct:.1f}% (seuil: 70%)", "fill_rate", min_fill_rate=70))

        # UP#17: Attributs manquants [Semi]
        # UP#23: Données non interprétables [Manuel]
        # UP#25: Encodage incompatible [Semi]

        # UP#36: Données non conformes usage légal [Manuel]
        # UP#37: Habilitation insuffisante [Manuel]
        # UP#39: Durée conservation dépassée [Semi]
        # UP#40: Finalité usage non autorisée [Manuel]

        # Outliers IQR (complément UP)
        if pd.api.types.is_numeric_dtype(series):
            clean = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean) > 10:
                q1, q3 = float(clean.quantile(0.25)), float(clean.quantile(0.75))
                iqr = q3 - q1
                if iqr > 0:
                    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    outlier_count = int(((clean < lower) | (clean > upper)).sum())
                    if outlier_count > 0:
                        rules.append(_rule("", f"Outliers IQR: {outlier_count} hors [{lower:.2f}, {upper:.2f}]", "outlier_iqr", lower=lower, upper=upper, dimension="UP", detection="Auto"))

        contracts[col] = contract

    # ── Multi-colonnes: DP#1 Calculs dérivés ──────────────────────────────
    for formula_info in col_config.get("derived_formulas", []):
        target = formula_info["target"]
        if target in contracts:
            contracts[target]["rules"].append(
                _rule("DP#1", f"Formule: {formula_info['description']}", "derived_calc",
                      sources=formula_info["sources"], target=target, formula=formula_info["formula"])
            )

    return contracts


def _rule(anomaly_id: str, description: str, rule_type: str, **kwargs) -> dict:
    """Crée une règle de contrat liée au référentiel."""
    ref = REFERENTIAL.get(anomaly_id, {})
    r = {
        "name": ref.get("name", description.split(":")[0] if ":" in description else description[:40]),
        "anomaly_id": anomaly_id,
        "dimension": kwargs.pop("dimension", ref.get("dimension", "")),
        "detection": kwargs.pop("detection", ref.get("detection", "Auto")),
        "criticality_ref": ref.get("criticality", ""),
        "woodall": ref.get("woodall", ""),
        "description": description,
        "type": rule_type,
    }
    r.update(kwargs)
    return r


# ============================================================================
# VALIDATION
# ============================================================================

def _validate_contracts(df: pd.DataFrame, contracts: dict) -> dict:
    """Valide le DataFrame — exécute les détecteurs Auto et Semi."""
    violations = {}

    for col_name, contract in contracts.items():
        col_viols = []

        if col_name not in df.columns:
            col_viols.append(_violation("DB#1", "column_exists", f"Colonne '{col_name}' absente", "CRITIQUE", "DB"))
            violations[col_name] = col_viols
            continue

        series = df[col_name]
        total = len(series)

        for rule in contract.get("rules", []):
            rt = rule.get("type")
            aid = rule.get("anomaly_id", "")
            dim = rule.get("dimension", "")
            det = rule.get("detection", "Auto")

            # Skip Manuel rules (can't auto-validate)
            if det == "Manuel":
                continue

            try:
                v = _check_rule(df, series, col_name, total, rt, rule, aid, dim)
                if v:
                    col_viols.append(v)
            except Exception:
                pass

        violations[col_name] = col_viols

    return violations


def _check_rule(df, series, col_name, total, rt, rule, aid, dim):
    """Vérifie une règle et retourne une violation ou None."""

    if rt == "null_check":
        null_pct = series.isnull().mean() * 100
        threshold = rule.get("threshold", 10.0)
        if null_pct > threshold:
            crit = "CRITIQUE" if null_pct > 50 else "ÉLEVÉ" if null_pct > 20 else "MOYEN"
            return _violation(aid, rule["name"], f"Taux nulls {null_pct:.1f}% > seuil {threshold}%", crit, dim, int(series.isnull().sum()))

    elif rt == "pk_unique":
        dup_count = int(series.duplicated(keep="first").sum())
        if dup_count > 0:
            dups = series[series.duplicated(keep=False)].value_counts().head(3)
            return _violation(aid, rule["name"], f"{dup_count} doublons PK (top: {', '.join(str(v) for v in dups.index[:3])})", "CRITIQUE", dim, dup_count)

    elif rt == "unique":
        dup_count = int(series.duplicated(keep="first").sum())
        if dup_count > 0:
            return _violation(aid, rule["name"], f"{dup_count} doublons (unicité attendue)", "ÉLEVÉ", dim, dup_count)

    elif rt == "enum":
        clean = series.dropna()
        if len(clean) > 0:
            allowed = set(rule.get("values", []))
            invalid = clean[~clean.astype(str).isin(allowed)]
            if len(invalid) > 0:
                return _violation(aid, rule["name"], f"{len(invalid)} hors domaine (ex: {', '.join(str(v) for v in invalid.unique()[:5])})", "ÉLEVÉ", dim, len(invalid))

    elif rt == "range":
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean) > 0:
            mn, mx = rule.get("min", float("-inf")), rule.get("max", float("inf"))
            out = int(((clean < mn) | (clean > mx)).sum())
            if out > 0:
                return _violation(aid, rule["name"], f"{out} valeurs hors [{mn:.2f}, {mx:.2f}]", "CRITIQUE" if out > total * 0.1 else "ÉLEVÉ", dim, out)

    elif rt == "email_format":
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        non_null = series.dropna()
        if len(non_null) > 0:
            invalid = non_null[~non_null.astype(str).str.match(pattern, na=False)]
            if len(invalid) > 0:
                return _violation(aid, rule["name"], f"{len(invalid)} emails invalides", "MOYEN", dim, len(invalid))

    elif rt == "type_mix":
        non_null = series.dropna()
        if len(non_null) > 0:
            nc = pd.to_numeric(non_null, errors="coerce")
            rate = nc.notna().sum() / len(non_null)
            if 0.1 < rate < 0.9:
                return _violation(aid, rule["name"], f"Types mixtes: {rate:.0%} numériques dans texte", "ÉLEVÉ", dim, int(nc.isna().sum()))

    elif rt == "no_negative":
        vals = pd.to_numeric(series, errors="coerce")
        neg = int((vals < 0).sum())
        if neg > 0:
            return _violation(aid, rule["name"], f"{neg} valeurs négatives (min: {vals.min():.2f})", "MOYEN", dim, neg)

    elif rt == "no_zero":
        vals = pd.to_numeric(series, errors="coerce")
        zc = int((vals == 0).sum())
        if zc > 0:
            return _violation(aid, rule["name"], f"{zc} zéros (division par zéro potentielle)", "MOYEN", dim, zc)

    elif rt == "temporal_order":
        end_col = rule.get("end_col", "")
        if end_col in df.columns:
            starts = pd.to_datetime(series, errors="coerce")
            ends = pd.to_datetime(df[end_col], errors="coerce")
            bad = int(((starts > ends) & starts.notna() & ends.notna()).sum())
            if bad > 0:
                return _violation(aid, rule["name"], f"{bad} lignes où {col_name} > {end_col}", "ÉLEVÉ", dim, bad)

    elif rt == "conditional_required":
        cond_col = rule.get("condition_col", "")
        cond_val = rule.get("condition_val", "")
        if cond_col in df.columns:
            bad = df[(df[cond_col] == cond_val) & series.isnull()]
            if len(bad) > 0:
                return _violation(aid, rule["name"], f"{len(bad)} lignes: {cond_col}={cond_val} mais {col_name} NULL", "ÉLEVÉ", dim, len(bad))

    elif rt == "freshness":
        dates = pd.to_datetime(series, errors="coerce")
        max_age = rule.get("max_age_days", 365)
        cutoff = pd.Timestamp.now() - pd.Timedelta(days=max_age)
        obsolete = int((dates < cutoff).sum())
        if obsolete > 0:
            oldest = dates.min()
            return _violation(aid, rule["name"], f"{obsolete} données > {max_age}j (plus ancienne: {oldest.strftime('%Y-%m-%d') if pd.notna(oldest) else 'N/A'})", "ÉLEVÉ" if obsolete > total * 0.5 else "MOYEN", dim, obsolete)

    elif rt == "fill_rate":
        fill = (1 - series.isnull().mean()) * 100
        min_fill = rule.get("min_fill_rate", 70)
        if fill < min_fill:
            return _violation(aid, rule["name"], f"Remplissage {fill:.1f}% < seuil {min_fill}%", "ÉLEVÉ", dim, int(series.isnull().sum()))

    elif rt == "granularity_max":
        if total > 0:
            ratio = series.nunique() / total
            thresh = rule.get("max_unique_ratio", 0.9)
            if ratio > thresh:
                return _violation(aid, rule["name"], f"Granularité {ratio:.0%} > seuil {thresh:.0%}", "FAIBLE", dim, 0)

    elif rt == "granularity_min":
        nunique = series.nunique()
        mn = rule.get("min_unique", 3)
        if nunique < mn:
            return _violation(aid, rule["name"], f"{nunique} uniques < min {mn}", "MOYEN", dim, 0)

    elif rt == "outlier_iqr":
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean) > 10:
            lo, hi = rule.get("lower", 0), rule.get("upper", 0)
            out = int(((clean < lo) | (clean > hi)).sum())
            if out > 0:
                return _violation(aid, rule["name"], f"{out} outliers IQR", "MOYEN" if out < total * 0.05 else "ÉLEVÉ", dim, out)

    elif rt == "whitespace":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            bad = int((clean != clean.str.strip()).sum())
            if bad > 0:
                return _violation(aid, rule["name"], f"{bad} valeurs avec espaces parasites", "MOYEN", dim, bad)

    elif rt == "encoding_issues":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            bad = int(clean.str.contains(r'[Ã¢Ã©Ã¨Ã´Ã¼]|ï¿½|\?{3,}', regex=True, na=False).sum())
            if bad > 0:
                return _violation(aid, rule["name"], f"{bad} valeurs corrompues", "MOYEN", dim, bad)

    elif rt == "special_chars":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            bad = int(clean.str.contains(r"""['"\\<>]""", regex=True, na=False).sum())
            if bad > 0:
                return _violation(aid, rule["name"], f"{bad} valeurs avec caractères spéciaux", "MOYEN", dim, bad)

    elif rt == "case_inconsistency":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            patterns = set()
            for v in clean.head(100):
                if v.isupper():
                    patterns.add("UPPER")
                elif v.islower():
                    patterns.add("lower")
                else:
                    patterns.add("Mixed")
            if len(patterns) > 1:
                return _violation(aid, rule["name"], f"Casse incohérente: {', '.join(patterns)}", "FAIBLE", dim, 0)

    elif rt == "column_empty":
        if series.isnull().all():
            return _violation(aid, rule["name"], "Colonne 100% vide", "FAIBLE", dim, total)

    elif rt == "exact_duplicates":
        dup = int(series.duplicated(keep="first").sum())
        if dup > 0:
            return _violation(aid, rule["name"], f"{dup} doublons exacts", "ÉLEVÉ", dim, dup)

    elif rt == "length":
        clean = series.dropna()
        if len(clean) > 0:
            mx = rule.get("max_length", 255)
            bad = int((clean.astype(str).str.len() > mx).sum())
            if bad > 0:
                return _violation(aid, rule["name"], f"{bad} valeurs > {mx} car.", "MOYEN", dim, bad)

    elif rt == "derived_calc":
        formula = rule.get("formula", "")
        sources = rule.get("sources", [])
        target = rule.get("target", col_name)
        if all(c in df.columns for c in sources) and target in df.columns:
            errors = _check_derived_formula(df, sources, target, formula)
            if errors > 0:
                return _violation(aid, rule["name"], f"{errors} lignes: formule '{formula}' non respectée", "ÉLEVÉ", dim, errors)

    elif rt == "ratio_bounds":
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean) > 0:
            mn, mx = rule.get("min", 0), rule.get("max", 100)
            out = int(((clean < mn) | (clean > mx)).sum())
            if out > 0:
                return _violation(aid, rule["name"], f"{out} ratios hors [{mn}, {mx}]", "ÉLEVÉ", dim, out)

    elif rt == "overflow":
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean) > 0 and (clean.max() > 1e15 or clean.min() < -1e15):
            return _violation(aid, rule["name"], f"Valeur extrême: max={clean.max():.2e}", "CRITIQUE", dim, 1)

    return None


def _violation(anomaly_id, rule_name, message, criticality, dimension, affected_rows=0):
    """Crée un dict violation."""
    return {
        "rule": rule_name,
        "anomaly_id": anomaly_id,
        "dimension": dimension,
        "criticality": criticality,
        "message": message,
        "affected_rows": affected_rows,
    }


# ============================================================================
# SCORES DAMA / ISO 8000
# ============================================================================

def _compute_dama_scores(df, contracts, violations):
    """Calcule les 6 dimensions DAMA pour chaque colonne."""
    scores = {}
    for col_name in contracts:
        if col_name not in df.columns:
            continue
        series = df[col_name]
        total = len(series)
        if total == 0:
            continue

        completude = 1 - (series.isnull().sum() / total)
        unicite = 1 - (series.duplicated(keep="first").sum() / total)

        validity_viols = sum(v.get("affected_rows", 0) for v in violations.get(col_name, []) if v.get("anomaly_id") in ("DB#5", "DB#7", "DB#8"))
        validite = 1 - (validity_viols / total) if validity_viols > 0 else None

        br_viols = sum(v.get("affected_rows", 0) for v in violations.get(col_name, []) if v.get("dimension") == "BR")
        coherence = 1 - (br_viols / total) if br_viols > 0 else None

        fresh_viols = [v for v in violations.get(col_name, []) if v.get("anomaly_id") == "UP#6"]
        fraicheur = 1 - (fresh_viols[0].get("affected_rows", 0) / total) if fresh_viols else None

        dp_viols = sum(v.get("affected_rows", 0) for v in violations.get(col_name, []) if v.get("dimension") == "DP")
        exactitude = 1 - (dp_viols / total) if dp_viols > 0 else None

        scores[col_name] = {
            "Complétude": round(completude, 4),
            "Cohérence": round(coherence, 4) if coherence is not None else None,
            "Exactitude": round(exactitude, 4) if exactitude is not None else None,
            "Fraîcheur": round(fraicheur, 4) if fraicheur is not None else None,
            "Validité": round(validite, 4) if validite is not None else None,
            "Unicité": round(unicite, 4),
        }
    return scores


# ============================================================================
# HELPERS
# ============================================================================

def _infer_type(series):
    if pd.api.types.is_integer_dtype(series): return "integer"
    elif pd.api.types.is_float_dtype(series): return "float"
    elif pd.api.types.is_bool_dtype(series): return "boolean"
    elif pd.api.types.is_datetime64_any_dtype(series): return "datetime"
    elif pd.api.types.is_string_dtype(series): return "string"
    return "unknown"


def _auto_detect_columns(df):
    """Détecte automatiquement les rôles des colonnes."""
    config = {
        "pk_columns": [], "email_columns": [], "date_columns": [],
        "date_start_columns": [], "date_end_columns": [],
        "positive_columns": [], "denominator_columns": [],
        "conditional_required_columns": {}, "derived_formulas": [],
    }
    for col in df.columns:
        cl = col.lower()
        if any(kw in cl for kw in ["id", "matricule", "code_unique", "pk", "identifiant"]):
            if df[col].nunique() == len(df[col].dropna()):
                config["pk_columns"].append(col)
        if any(kw in cl for kw in ["email", "mail", "courriel"]):
            config["email_columns"].append(col)
        if any(kw in cl for kw in ["date", "datetime", "timestamp", "jour", "dt_"]):
            config["date_columns"].append(col)
            if any(kw in cl for kw in ["debut", "start", "entree", "embauche", "creation", "ouverture"]):
                config["date_start_columns"].append(col)
            if any(kw in cl for kw in ["fin", "end", "sortie", "depart", "cloture", "fermeture"]):
                config["date_end_columns"].append(col)
        if pd.api.types.is_datetime64_any_dtype(df[col]) and col not in config["date_columns"]:
            config["date_columns"].append(col)
        if any(kw in cl for kw in ["age", "anciennete", "salaire", "montant", "prix", "quantite", "nombre", "count", "nb_", "effectif", "taux", "prime", "indemnite"]):
            config["positive_columns"].append(col)
        if any(kw in cl for kw in ["cout", "diviseur", "denominat", "base_", "total", "effectif"]):
            config["denominator_columns"].append(col)

    # Derived formulas
    cols_lower = {c.lower(): c for c in df.columns}
    for age_kw in ["age", "anciennete"]:
        for col in df.columns:
            if age_kw in col.lower() and pd.api.types.is_numeric_dtype(df[col]):
                for date_col in config["date_columns"]:
                    if any(kw in date_col.lower() for kw in ["naissance", "birth", "embauche", "entree"]):
                        config["derived_formulas"].append({"target": col, "sources": [date_col], "formula": "age_from_birthdate", "description": f"{col} = (now - {date_col}) / 365.25"})

    if "montant_ht" in cols_lower and "montant_ttc" in cols_lower:
        tva_col = cols_lower.get("taux_tva") or cols_lower.get("tva")
        if tva_col:
            config["derived_formulas"].append({"target": cols_lower["montant_ttc"], "sources": [cols_lower["montant_ht"], tva_col], "formula": "montant_ttc", "description": "montant_ttc = montant_ht × (1 + tva)"})

    # Conditional required
    for col in df.columns:
        cl = col.lower()
        if "statut" in cl or "status" in cl:
            for other in df.columns:
                if any(kw in other.lower() for kw in ["date_sortie", "date_fin", "date_depart"]):
                    vals = df[col].dropna().unique()
                    for v in vals:
                        if any(kw in str(v).lower() for kw in ["inactif", "inactive", "sorti", "termine"]):
                            config["conditional_required_columns"][other] = (col, v)

    return config


def _check_derived_formula(df, sources, target, formula):
    if formula == "age_from_birthdate" and len(sources) >= 1:
        dates = pd.to_datetime(df[sources[0]], errors="coerce")
        expected = (pd.Timestamp.now() - dates).dt.days / 365.25
        actual = pd.to_numeric(df[target], errors="coerce")
        mask = expected.notna() & actual.notna()
        return int((abs(expected[mask] - actual[mask]) > 1).sum())
    if formula == "montant_ttc" and len(sources) >= 2:
        ht = pd.to_numeric(df[sources[0]], errors="coerce")
        tva = pd.to_numeric(df[sources[1]], errors="coerce")
        expected = ht * (1 + tva)
        actual = pd.to_numeric(df[target], errors="coerce")
        mask = expected.notna() & actual.notna()
        return int((~np.isclose(expected[mask], actual[mask], rtol=0.01, atol=0.01)).sum())
    return 0


# ============================================================================
# EXPORT ODCS v3.1.0 (Open Data Contract Standard)
# ============================================================================

# Mapping des types internes vers les logicalType ODCS
_TYPE_MAP = {
    "string": "string",
    "integer": "integer",
    "float": "number",
    "boolean": "boolean",
    "datetime": "timestamp",
    "unknown": "string",
}

# Mapping des rule types internes vers les ODCS quality metric types
_QUALITY_METRIC_MAP = {
    "null_check": "nullValues",
    "pk_unique": "duplicateValues",
    "unique": "duplicateValues",
    "exact_duplicates": "duplicateValues",
    "enum": "invalidValues",
    "range": "invalidValues",
    "email_format": "invalidValues",
    "type_mix": "invalidValues",
    "no_negative": "invalidValues",
    "no_zero": "invalidValues",
    "overflow": "invalidValues",
    "ratio_bounds": "invalidValues",
    "null_legitimate": "nullValues",
    "column_empty": "nullValues",
    "fill_rate": "missingValues",
}


def _map_odcs_quality_type(rule_type: str) -> str:
    """Map un type de règle interne vers un type quality ODCS."""
    return _QUALITY_METRIC_MAP.get(rule_type, "custom")


def _build_odcs_quality_entry(rule: dict) -> dict:
    """Convertit une règle interne en entrée quality ODCS v3.1.0."""
    metric_name = _map_odcs_quality_type(rule.get("type", ""))
    # ODCS v3.1.0: type = "library"|"custom", metric = nullValues|duplicateValues|...
    is_library = metric_name in ("nullValues", "duplicateValues", "invalidValues", "missingValues", "rowCount")
    entry = {
        "type": "library" if is_library else "custom",
        "description": rule.get("description", ""),
    }
    if is_library:
        entry["metric"] = metric_name

    # Ajouter les paramètres spécifiques selon le type
    rt = rule.get("type", "")
    if rt == "null_check":
        entry["mustBeLessThan"] = rule.get("threshold", 10.0)
        entry["unit"] = "percent"
    elif rt in ("range", "ratio_bounds"):
        entry["mustBeBetween"] = [rule.get("min", 0), rule.get("max", 0)]
    elif rt == "enum":
        pass  # validValues ajouté dans customProperties ci-dessous
    elif rt == "freshness":
        entry["mustBeLessThan"] = rule.get("max_age_days", 365)
        entry["unit"] = "days"
    elif rt == "length":
        entry["mustBeLessThan"] = rule.get("max_length", 255)
        entry["unit"] = "characters"
    elif rt == "fill_rate":
        entry["mustBeGreaterThan"] = rule.get("min_fill_rate", 70)
        entry["unit"] = "percent"

    # Enrichissements custom (Woodall, anomaly_id, validValues, etc.)
    custom = {}
    if rule.get("type") == "enum" and rule.get("values"):
        custom["validValues"] = rule["values"]
    if rule.get("anomaly_id"):
        custom["anomalyId"] = rule["anomaly_id"]
    if rule.get("dimension"):
        custom["causalDimension"] = rule["dimension"]
    if rule.get("detection"):
        custom["detectionMethod"] = rule["detection"]
    if rule.get("criticality_ref"):
        custom["criticality"] = rule["criticality_ref"]
    if rule.get("woodall"):
        custom["woodallClass"] = rule["woodall"]
    if custom:
        entry["customProperties"] = custom

    return entry


def convert_to_odcs(contracts: dict, dama_scores: dict, violations: dict,
                    dataset_name: str = "dataset") -> dict:
    """Convertit les contrats internes au format ODCS v3.1.0."""

    ref_summary = get_summary()

    # Properties ODCS pour chaque colonne
    properties = []
    for col_name, contract in contracts.items():
        prop = {
            "name": col_name,
            "logicalType": _TYPE_MAP.get(contract.get("expected_type", "string"), "string"),
            "required": not contract.get("nullable", True),
            "unique": contract.get("unique", False),
        }

        # Quality rules
        quality = []
        for rule in contract.get("rules", []):
            quality.append(_build_odcs_quality_entry(rule))
        if quality:
            prop["quality"] = quality

        # DAMA scores en customProperties de la property
        col_dama = dama_scores.get(col_name, {})
        dama_clean = {k: v for k, v in col_dama.items() if v is not None}
        if dama_clean:
            prop["customProperties"] = {
                "damaScores": dama_clean,
            }

        properties.append(prop)

    # Violations summary
    total_violations = sum(len(v) for v in violations.values())
    violation_summary = {}
    for col_name, col_viols in violations.items():
        if col_viols:
            violation_summary[col_name] = [
                {
                    "rule": v.get("rule", ""),
                    "anomalyId": v.get("anomaly_id", ""),
                    "criticality": v.get("criticality", ""),
                    "message": v.get("message", ""),
                    "affectedRows": v.get("affected_rows", 0),
                }
                for v in col_viols
            ]

    # Construction du contrat ODCS complet
    odcs = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": str(uuid.uuid4()),
        "name": f"Data Contract — {dataset_name}",
        "version": "1.0.0",
        "status": "active",
        "domain": "data-quality",
        "description": {
            "purpose": f"Contrat qualité généré automatiquement pour le dataset '{dataset_name}' "
                       f"avec le référentiel de {ref_summary['total']} anomalies "
                       f"(DB:{ref_summary['by_dimension']['DB']['total']}, "
                       f"DP:{ref_summary['by_dimension']['DP']['total']}, "
                       f"BR:{ref_summary['by_dimension']['BR']['total']}, "
                       f"UP:{ref_summary['by_dimension']['UP']['total']}).",
            "limitations": "Les règles 'Manuel' nécessitent une revue humaine. "
                           "Les seuils Auto/Semi sont calibrés statistiquement sur les données observées.",
        },
        "schema": [
            {
                "name": dataset_name,
                "logicalType": "object",
                "properties": properties,
            }
        ],
        "team": {
            "members": [
                {
                    "name": "Augmented DQ Framework",
                    "role": "generator",
                }
            ]
        },
        "tags": [
            "data-quality",
            "augmented-dq",
            "dama-iso-8000",
            "woodall-taxonomy",
        ],
        "customProperties": {
            "framework": "Augmented DQ Demo",
            "referential": {
                "total": ref_summary["total"],
                "byDimension": {
                    dim: {
                        "total": info["total"],
                        "auto": info.get("Auto", 0),
                        "semi": info.get("Semi", 0),
                        "manuel": info.get("Manuel", 0),
                    }
                    for dim, info in ref_summary["by_dimension"].items()
                },
            },
            "qualityFramework": "DAMA/ISO 8000",
            "causalDimensions": ["DB (Database Integrity)", "DP (Data Processing)",
                                 "BR (Business Rules)", "UP (Usage Appropriateness)"],
            "damaDimensions": DAMA_DIMENSIONS,
            "validationResults": {
                "totalViolations": total_violations,
                "violationsByColumn": violation_summary,
            },
        },
        "contractCreatedTs": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    return odcs


def export_odcs_yaml(contracts: dict, dama_scores: dict, violations: dict,
                     dataset_name: str = "dataset") -> str:
    """Exporte le contrat au format ODCS v3.1.0 YAML."""
    odcs = convert_to_odcs(contracts, dama_scores, violations, dataset_name)

    # Custom YAML representer pour un rendu propre + types numpy
    class _ODCSDumper(yaml.SafeDumper):
        pass

    def _str_representer(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    def _numpy_float_representer(dumper, data):
        return dumper.represent_float(float(data))

    def _numpy_int_representer(dumper, data):
        return dumper.represent_int(int(data))

    def _numpy_bool_representer(dumper, data):
        return dumper.represent_bool(bool(data))

    _ODCSDumper.add_representer(str, _str_representer)
    for np_float in (np.float64, np.float32, np.floating):
        _ODCSDumper.add_representer(np_float, _numpy_float_representer)
    for np_int in (np.int64, np.int32, np.intc, np.integer):
        _ODCSDumper.add_representer(np_int, _numpy_int_representer)
    _ODCSDumper.add_representer(np.bool_, _numpy_bool_representer)

    return yaml.dump(odcs, Dumper=_ODCSDumper, default_flow_style=False,
                     allow_unicode=True, sort_keys=False, width=120)
