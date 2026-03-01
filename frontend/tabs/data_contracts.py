"""
Tab Data Contracts v4 — Génération dynamique depuis le catalogue YAML.

Architecture évolutive:
  - Les anomalies sont lues depuis rules_catalog.yaml (extensible par CSV)
  - Chaque rule_type a un applicateur Python qui détermine SI la règle s'applique
  - Ajouter une anomalie avec un rule_type existant = prise en charge automatique
  - Ajouter un nouveau rule_type = ajouter applicateur + validateur Python
"""

import re
import uuid
import streamlit as st
import pandas as pd
import numpy as np
import json
import yaml
from datetime import datetime

# Import du référentiel + catalogue déclaratif
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.anomaly_referential import REFERENTIAL, get_summary, get_by_dimension
from backend.rules_catalog_loader import catalog as _catalog


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
        <h3 style="color: white; margin: 0 0 0.5rem 0;">📜 Data Contracts v3 — Référentiel {ref_summary['total']} anomalies (extensible)</h3>
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
    # RÉFÉRENTIEL (collapsible) — chargé depuis rules_catalog.yaml
    # =====================================================================
    ref_total = len(_catalog.anomalies)
    with st.expander(f"📚 Référentiel complet ({ref_total} anomalies)", expanded=False):
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
    # IMPORT CSV — Enrichir le référentiel
    # =====================================================================
    with st.expander("📥 Importer de nouvelles anomalies (CSV)", expanded=False):
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <strong>Enrichissez le référentiel</strong> en chargeant un CSV avec vos anomalies métier.<br/>
            <span style="color: rgba(255,255,255,0.7);">
                Colonnes obligatoires : <code>anomaly_id</code>, <code>name</code>, <code>description</code>,
                <code>dimension</code>, <code>detection</code>, <code>criticality</code><br/>
                Colonnes optionnelles : <code>woodall</code>, <code>algorithm</code>, <code>business_risk</code>,
                <code>frequency</code>, <code>default_rule_type</code>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Télécharger le template
        csv_template = _catalog.generate_csv_template()
        st.download_button(
            label="📄 Télécharger le template CSV",
            data=csv_template,
            file_name="anomalies_template.csv",
            mime="text/csv",
        )

        # Upload CSV
        csv_file = st.file_uploader(
            "📁 Charger un CSV d'anomalies",
            type=["csv"],
            key="anomaly_csv_upload",
        )

        if csv_file is not None:
            try:
                import_df = pd.read_csv(csv_file, dtype=str).fillna("")
                st.markdown(f"**Aperçu** — {len(import_df)} anomalies trouvées :")
                st.dataframe(import_df, use_container_width=True, hide_index=True)

                # Validation
                errors = _catalog.validate_import_df(import_df)
                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    # Identifier nouvelles vs existantes
                    existing = set(_catalog.anomalies.keys())
                    new_ids = set(import_df["anomaly_id"].str.strip()) - existing
                    update_ids = set(import_df["anomaly_id"].str.strip()) & existing

                    if new_ids:
                        st.info(f"🆕 {len(new_ids)} nouvelles anomalies : {', '.join(sorted(new_ids))}")
                    if update_ids:
                        st.warning(f"♻️ {len(update_ids)} anomalies déjà existantes : {', '.join(sorted(update_ids))}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        overwrite = st.checkbox("Écraser les anomalies existantes", value=False)
                    with col_b:
                        if st.button("✅ Importer dans le catalogue", type="primary"):
                            result = _catalog.import_from_dataframe(import_df, overwrite=overwrite)
                            if result["errors"]:
                                for err in result["errors"]:
                                    st.error(f"❌ {err}")
                            else:
                                msg_parts = []
                                if result["added"] > 0:
                                    msg_parts.append(f"🆕 {result['added']} ajoutées")
                                if result["updated"] > 0:
                                    msg_parts.append(f"♻️ {result['updated']} mises à jour")
                                if result["skipped"] > 0:
                                    msg_parts.append(f"⏭️ {result['skipped']} ignorées (déjà existantes)")
                                st.success(f"✅ Import réussi — {' · '.join(msg_parts)}")
                                st.info(f"📊 Le référentiel contient maintenant **{len(_catalog.anomalies)} anomalies**")
                                st.rerun()

            except Exception as e:
                st.error(f"❌ Erreur de lecture CSV : {e}")

    # =====================================================================
    # GÉNÉRATION
    # =====================================================================
    st.subheader("⚡ Génération automatique")

    if st.button(f"🔄 Générer les contrats ({ref_total} anomalies)", type="primary", use_container_width=True):
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
# APPLICATEURS DE RÈGLES — dispatch dynamique par rule_type
# ============================================================================
# Pour ajouter le support d'un nouveau rule_type:
#   1. Ajouter le rule_type dans rules_catalog.yaml (section rule_types)
#   2. Ajouter un applicateur ci-dessous avec @_applicator("rule_type")
#   3. Ajouter son validateur dans _check_rule()
#
# Les anomalies ajoutées par CSV/YAML utilisant un rule_type existant
# sont AUTOMATIQUEMENT prises en charge — aucune modif Python nécessaire.
# ============================================================================

_RULE_APPLICATORS = {}
_MULTI_COL_APPLICATORS = {}


def _applicator(rule_type):
    """Enregistre un applicateur pour un rule_type per-column."""
    def decorator(fn):
        _RULE_APPLICATORS[rule_type] = fn
        return fn
    return decorator


def _multi_applicator(rule_type):
    """Enregistre un applicateur multi-colonnes."""
    def decorator(fn):
        _MULTI_COL_APPLICATORS[rule_type] = fn
        return fn
    return decorator


# ── Per-column applicators ───────────────────────────────────────────────

@_applicator("null_check")
def _apply_null_check(series, col, col_config, df, contract):
    null_pct = series.isnull().mean() * 100
    threshold = 0.0 if null_pct == 0 else 10.0
    return [{"description": f"Taux nulls \u2264 {threshold}% (actuel: {null_pct:.1f}%)", "threshold": threshold}]


@_applicator("pk_unique")
def _apply_pk_unique(series, col, col_config, df, contract):
    if col not in col_config["pk_columns"]:
        return None
    return [{"description": f"Pas de doublons PK (actuel: {series.duplicated(keep='first').sum()})"}]


@_applicator("unique")
def _apply_unique(series, col, col_config, df, contract):
    if not contract.get("unique"):
        return None
    return [{"description": "Toutes valeurs doivent \u00eatre uniques"}]


@_applicator("enum")
def _apply_enum(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna()
    if len(clean) == 0 or clean.nunique() > 30:
        return None
    values = sorted(clean.unique().tolist())
    desc = f"Valeurs autoris\u00e9es ({clean.nunique()}): {', '.join(str(v) for v in values[:10])}{'...' if len(values) > 10 else ''}"
    return [{"description": desc, "values": [str(v) for v in values]}]


@_applicator("range")
def _apply_range(series, col, col_config, df, contract):
    if not pd.api.types.is_numeric_dtype(series):
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) == 0:
        return None
    q01, q99 = float(clean.quantile(0.01)), float(clean.quantile(0.99))
    return [{"description": f"Valeurs dans [{q01:.2f}, {q99:.2f}]", "min": q01, "max": q99}]


@_applicator("email_format")
def _apply_email_format(series, col, col_config, df, contract):
    if col not in col_config["email_columns"]:
        return None
    return [{"description": "Format email valide (xxx@domain.tld)"}]


@_applicator("type_mix")
def _apply_type_mix(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    non_null = series.dropna()
    if len(non_null) == 0:
        return None
    numeric_converted = pd.to_numeric(non_null, errors="coerce")
    numeric_rate = float(numeric_converted.notna().sum() / len(non_null))
    if not (0.1 < numeric_rate < 0.9):
        return None
    return [{"description": f"Types mixtes ({numeric_rate:.0%} num\u00e9riques dans texte)", "numeric_rate": numeric_rate}]


@_applicator("exact_duplicates")
def _apply_exact_duplicates(series, col, col_config, df, contract):
    if col in col_config["pk_columns"]:
        return None
    if contract.get("expected_type") == "string":
        return None
    dup_count = int(series.duplicated(keep="first").sum())
    if dup_count == 0:
        return None
    return [{"description": f"{dup_count} doublons exacts"}]


@_applicator("fuzzy_duplicates")
def _apply_fuzzy_duplicates(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    if col in col_config["pk_columns"]:
        return None
    return [{"description": "Doublons fuzzy (variations syntaxiques)"}]


@_applicator("synonyms")
def _apply_synonyms(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna()
    if len(clean) == 0 or not (3 <= clean.nunique() <= 50):
        return None
    return [{"description": "V\u00e9rifier synonymes/variantes m\u00eame concept"}]


@_applicator("unit_heterogeneity")
def _apply_unit_heterogeneity(series, col, col_config, df, contract):
    if col not in col_config["positive_columns"]:
        return None
    return [{"description": "V\u00e9rifier homog\u00e9n\u00e9it\u00e9 des unit\u00e9s"}]


@_applicator("format_consistency")
def _apply_format_consistency(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    if col not in col_config["date_columns"]:
        return None
    return [{"description": "V\u00e9rifier coh\u00e9rence formats dates"}]


@_applicator("null_legitimate")
def _apply_null_legitimate(series, col, col_config, df, contract):
    null_pct = series.isnull().mean() * 100
    if null_pct == 0:
        return None
    return [{"description": f"NULL l\u00e9gitimes: {null_pct:.1f}% (\u00e0 documenter si > 30%)"}]


@_applicator("missing_rows")
def _apply_missing_rows(series, col, col_config, df, contract):
    return [{"description": "V\u00e9rifier compl\u00e9tude vs univers attendu"}]


@_applicator("column_empty")
def _apply_column_empty(series, col, col_config, df, contract):
    if series.isnull().mean() * 100 != 100:
        return None
    return [{"description": "Colonne 100% vide"}]


@_applicator("encoding_issues")
def _apply_encoding_issues(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna().astype(str)
    if len(clean) == 0:
        return None
    issues = clean.str.contains(r'[Ã¢Ã©Ã¨Ã´Ã¼]|ï¿½|\?{3,}', regex=True, na=False).sum()
    if issues == 0:
        return None
    return [{"description": f"{issues} valeurs avec probl\u00e8mes d'encodage"}]


@_applicator("special_chars")
def _apply_special_chars(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna().astype(str)
    if len(clean) == 0:
        return None
    special = clean.str.contains(r"""['"\\<>]""", regex=True, na=False).sum()
    if special == 0:
        return None
    return [{"description": f"{special} valeurs avec caract\u00e8res sp\u00e9ciaux"}]


@_applicator("whitespace")
def _apply_whitespace(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna().astype(str)
    if len(clean) == 0:
        return None
    ws = (clean != clean.str.strip()).sum()
    if ws == 0:
        return None
    return [{"description": f"{ws} valeurs avec espaces parasites"}]


@_applicator("case_inconsistency")
def _apply_case_inconsistency(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna().astype(str)
    if len(clean) == 0:
        return None
    upper_count = clean.str.isupper().sum()
    lower_count = clean.str.islower().sum()
    mixed = len(clean) - upper_count - lower_count
    if not (mixed > 0 and upper_count > 0 and lower_count > 0):
        return None
    return [{"description": f"Casse incoh\u00e9rente ({upper_count} UPPER, {lower_count} lower, {mixed} Mixed)"}]


@_applicator("overflow")
def _apply_overflow(series, col, col_config, df, contract):
    if not pd.api.types.is_numeric_dtype(series):
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) == 0:
        return None
    if not (clean.max() > 1e15 or clean.min() < -1e15):
        return None
    return [{"description": f"Valeurs extr\u00eames (max: {clean.max():.2e})"}]


@_applicator("no_zero")
def _apply_no_zero(series, col, col_config, df, contract):
    if col not in col_config["denominator_columns"]:
        return None
    if not pd.api.types.is_numeric_dtype(series):
        return None
    zero_count = int((pd.to_numeric(series, errors="coerce") == 0).sum())
    return [{"description": f"Pas de z\u00e9ros d\u00e9nominateur (actuel: {zero_count})"}]


@_applicator("length")
def _apply_length(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    clean = series.dropna().astype(str)
    if len(clean) == 0:
        return None
    max_len = int(clean.str.len().max())
    return [{"description": f"Longueur max \u2264 {max_len} car.", "max_length": max_len}]


@_applicator("date_format_ambiguity")
def _apply_date_format_ambiguity(series, col, col_config, df, contract):
    if col not in col_config["date_columns"]:
        return None
    if contract.get("expected_type") != "string":
        return None
    return [{"description": "V\u00e9rifier parsing dates (DD/MM vs MM/DD)"}]


@_applicator("cartesian_join_risk")
def _apply_cartesian_join_risk(series, col, col_config, df, contract):
    if col not in col_config["pk_columns"]:
        return None
    return [{"description": "Risque jointure cart\u00e9sienne si PK non unique"}]


@_applicator("no_negative")
def _apply_no_negative(series, col, col_config, df, contract):
    if col not in col_config["positive_columns"]:
        return None
    if not pd.api.types.is_numeric_dtype(series):
        return None
    neg_count = int((pd.to_numeric(series, errors="coerce") < 0).sum())
    return [{"description": f"Pas de n\u00e9gatifs sur champ positif (actuel: {neg_count})"}]


@_applicator("ratio_bounds")
def _apply_ratio_bounds(series, col, col_config, df, contract):
    if not pd.api.types.is_numeric_dtype(series):
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) == 0:
        return None
    if not col.lower().startswith(("taux", "ratio", "pct", "pourcentage")):
        return None
    return [{"description": "Ratio dans [0, 1] ou [0, 100]", "min": 0, "max": 100}]


@_applicator("granularity_max")
def _apply_granularity_max(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    total = len(series)
    if total == 0:
        return None
    ratio = series.nunique() / total
    if ratio <= 0.9:
        return None
    return [{"description": f"Granularit\u00e9 excessive ({ratio:.0%} uniques)", "max_unique_ratio": 0.9}]


@_applicator("granularity_min")
def _apply_granularity_min(series, col, col_config, df, contract):
    if contract.get("expected_type") != "string":
        return None
    total = len(series)
    if total <= 50:
        return None
    nunique = series.nunique()
    if nunique > 2:
        return None
    return [{"description": f"Granularit\u00e9 insuffisante ({nunique} uniques / {total} lignes)", "min_unique": 3}]


@_applicator("freshness")
def _apply_freshness(series, col, col_config, df, contract):
    if col not in col_config["date_columns"]:
        return None
    return [{"description": "Donn\u00e9es de moins de 365 jours", "max_age_days": 365}]


@_applicator("fill_rate")
def _apply_fill_rate(series, col, col_config, df, contract):
    null_pct = series.isnull().mean() * 100
    if null_pct <= 30:
        return None
    return [{"description": f"Taux remplissage {100-null_pct:.1f}% (seuil: 70%)", "min_fill_rate": 70}]


@_applicator("outlier_iqr")
def _apply_outlier_iqr(series, col, col_config, df, contract):
    if not pd.api.types.is_numeric_dtype(series):
        return None
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if len(clean) <= 10:
        return None
    q1, q3 = float(clean.quantile(0.25)), float(clean.quantile(0.75))
    iqr = q3 - q1
    if iqr <= 0:
        return None
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outlier_count = int(((clean < lower) | (clean > upper)).sum())
    if outlier_count == 0:
        return None
    return [{"description": f"Outliers IQR: {outlier_count} hors [{lower:.2f}, {upper:.2f}]",
             "lower": lower, "upper": upper, "dimension": "UP", "detection": "Auto"}]


# ── Multi-column applicators ─────────────────────────────────────────────

@_multi_applicator("temporal_order")
def _apply_temporal_order(df, col_config, contracts):
    results = []
    for start_col in col_config["date_start_columns"]:
        for end_col in col_config["date_end_columns"]:
            if end_col != start_col and end_col in df.columns:
                results.append((start_col, {
                    "description": f"{start_col} doit \u00eatre \u2264 {end_col}",
                    "start_col": start_col, "end_col": end_col,
                }))
    return results


@_multi_applicator("derived_calc")
def _apply_derived_calc(df, col_config, contracts):
    results = []
    for formula_info in col_config.get("derived_formulas", []):
        target = formula_info["target"]
        if target in contracts:
            results.append((target, {
                "description": f"Formule: {formula_info['description']}",
                "sources": formula_info["sources"],
                "target": target,
                "formula": formula_info["formula"],
            }))
    return results


@_multi_applicator("conditional_required")
def _apply_conditional_required(df, col_config, contracts):
    results = []
    for col, (cond_col, cond_val) in col_config.get("conditional_required_columns", {}).items():
        if cond_col in df.columns and col in contracts:
            results.append((col, {
                "description": f"SI {cond_col}={cond_val} ALORS {col} NOT NULL",
                "condition_col": cond_col, "condition_val": cond_val,
            }))
    return results


# ============================================================================
# G\u00c9N\u00c9RATION AUTOMATIQUE — dynamique depuis le catalogue
# ============================================================================

def _auto_generate_contracts(df: pd.DataFrame) -> dict:
    """G\u00e9n\u00e8re des contrats depuis le catalogue YAML \u2014 toute anomalie avec
    un default_rule_type est automatiquement prise en charge."""
    contracts = {}
    col_config = _auto_detect_columns(df)

    # Phase 1: R\u00e8gles per-column (it\u00e8re sur le catalogue)
    for col in df.columns:
        series = df[col]
        expected_type = _infer_type(series)

        contract = {
            "expected_type": expected_type,
            "nullable": bool(series.isnull().any()),
            "unique": bool(series.nunique() == len(series.dropna())) if len(series.dropna()) > 0 else False,
            "rules": [],
        }
        rules = contract["rules"]
        seen_rule_types = set()

        for anomaly_id, anomaly in _catalog.anomalies.items():
            rule_type = anomaly.get("default_rule_type")
            if not rule_type or rule_type in _MULTI_COL_APPLICATORS:
                continue
            applicator = _RULE_APPLICATORS.get(rule_type)
            if not applicator:
                continue
            results = applicator(series, col, col_config, df, contract)
            if results:
                for params in results:
                    params = dict(params)
                    desc = params.pop("description")
                    rules.append(_rule(anomaly_id, desc, rule_type, **params))
                seen_rule_types.add(rule_type)

        # Outlier IQR: compl\u00e9ment statistique (si pas d\u00e9j\u00e0 couvert par une anomalie)
        if "outlier_iqr" not in seen_rule_types:
            applicator = _RULE_APPLICATORS.get("outlier_iqr")
            if applicator:
                results = applicator(series, col, col_config, df, contract)
                if results:
                    for params in results:
                        params = dict(params)
                        desc = params.pop("description")
                        rules.append(_rule("", desc, "outlier_iqr", **params))

        contracts[col] = contract

    # Phase 2: R\u00e8gles multi-colonnes
    for anomaly_id, anomaly in _catalog.anomalies.items():
        rule_type = anomaly.get("default_rule_type")
        if not rule_type or rule_type not in _MULTI_COL_APPLICATORS:
            continue
        applicator = _MULTI_COL_APPLICATORS[rule_type]
        results = applicator(df, col_config, contracts)
        if results:
            for target_col, params in results:
                if target_col in contracts:
                    params = dict(params)
                    desc = params.pop("description")
                    contracts[target_col]["rules"].append(
                        _rule(anomaly_id, desc, rule_type, **params))

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

    elif rt == "fuzzy_duplicates":
        clean = series.dropna().astype(str)
        unique_vals = clean.unique()
        if 1 < len(unique_vals) <= 500:
            from difflib import SequenceMatcher
            pairs = []
            for i in range(len(unique_vals)):
                for j in range(i + 1, len(unique_vals)):
                    if SequenceMatcher(None, unique_vals[i].lower(), unique_vals[j].lower()).ratio() >= 0.85:
                        pairs.append((unique_vals[i], unique_vals[j]))
            if pairs:
                ex = "; ".join(f"'{a}'≈'{b}'" for a, b in pairs[:3])
                return _violation(aid, rule["name"], f"{len(pairs)} paires proches: {ex}", "MOYEN", dim, len(pairs))

    elif rt == "synonyms":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            groups = {}
            for v in clean:
                groups.setdefault(v.lower().strip(), set()).add(v)
            syns = {k: v for k, v in groups.items() if len(v) > 1}
            if syns:
                ex = "; ".join("/".join(sorted(v)) for v in list(syns.values())[:3])
                return _violation(aid, rule["name"], f"{len(syns)} synonymes: {ex}", "MOYEN", dim, sum(len(v) for v in syns.values()))

    elif rt == "format_consistency":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            pats = clean.apply(lambda x: re.sub(r'\d', 'D', x))
            unique_pats = pats.unique()
            if len(unique_pats) > 1:
                top = pats.value_counts().head(3)
                ex = ", ".join(f"'{p}': {c}" for p, c in top.items())
                return _violation(aid, rule["name"], f"{len(unique_pats)} formats: {ex}", "MOYEN", dim, 0)

    elif rt == "date_format_ambiguity":
        clean = series.dropna().astype(str)
        if len(clean) > 0:
            ambiguous = 0
            for v in clean.head(200):
                parts = re.split(r'[-/.]', v)
                if len(parts) >= 3:
                    try:
                        nums = [int(p) for p in parts[:3]]
                        if len(parts[0]) == 4:
                            m, d = nums[1], nums[2]
                        else:
                            m, d = nums[1], nums[0]
                        if 1 <= m <= 12 and 1 <= d <= 12 and m != d:
                            ambiguous += 1
                    except ValueError:
                        pass
            if ambiguous > 0:
                return _violation(aid, rule["name"], f"{ambiguous} dates ambiguës DD/MM vs MM/DD", "MOYEN", dim, ambiguous)

    elif rt == "cartesian_join_risk":
        dup_count = int(series.duplicated(keep="first").sum())
        if dup_count > 0:
            return _violation(aid, rule["name"], f"{dup_count} doublons → risque cartésien", "CRITIQUE", dim, dup_count)

    elif rt == "unit_heterogeneity":
        clean = pd.to_numeric(series, errors="coerce").dropna()
        if len(clean) > 5:
            pos = clean[clean > 0]
            if len(pos) > 5:
                log_range = np.log10(pos.max()) - np.log10(pos.min())
                if log_range > 2:
                    return _violation(aid, rule["name"],
                        f"Amplitude {10**log_range:.0f}x ({pos.min():.2f} → {pos.max():.2f})",
                        "MOYEN", dim, 0)

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

def _get_dama_category(anomaly_id: str) -> str:
    """Retourne la catégorie DAMA d'une anomalie via son rule_type dans le catalogue."""
    anomaly = _catalog.anomalies.get(anomaly_id, {})
    rule_type = anomaly.get("default_rule_type", "")
    rt_config = _catalog.rule_types.get(rule_type, {})
    return rt_config.get("category", "")


def _compute_dama_scores(df, contracts, violations):
    """Calcule les 6 dimensions DAMA pour chaque colonne.

    Utilise les catégories déclaratives du catalogue YAML (rule_types.category)
    pour mapper dynamiquement violations → dimensions DAMA.
    """
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

        # Validité: violations dont le rule_type a category="Validité"
        validity_viols = sum(v.get("affected_rows", 0) for v in violations.get(col_name, [])
                            if _get_dama_category(v.get("anomaly_id", "")) == "Validité")
        validite = 1 - (validity_viols / total) if validity_viols > 0 else None

        # Cohérence: violations dimension BR (déjà dynamique)
        br_viols = sum(v.get("affected_rows", 0) for v in violations.get(col_name, []) if v.get("dimension") == "BR")
        coherence = 1 - (br_viols / total) if br_viols > 0 else None

        # Fraîcheur: violations dont le rule_type a category="Fraîcheur"
        fresh_viols = [v for v in violations.get(col_name, [])
                      if _get_dama_category(v.get("anomaly_id", "")) == "Fraîcheur"]
        fraicheur = 1 - (fresh_viols[0].get("affected_rows", 0) / total) if fresh_viols else None

        # Exactitude: violations dimension DP (déjà dynamique)
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

# Mapping ODCS chargé depuis le catalogue déclaratif (rules_catalog.yaml)
# Plus besoin de modifier ce fichier pour ajouter des rule_types.
def _map_odcs_quality_type(rule_type: str) -> str:
    """Map un type de règle interne vers un type quality ODCS (via catalog)."""
    return _catalog.get_odcs_metric(rule_type)


def _build_odcs_quality_entry(rule: dict, col_name: str = "", dataset_name: str = "dataset") -> dict:
    """Convertit une règle interne en entrée quality ODCS v3.1.0.

    Délègue au catalogue déclaratif (rules_catalog.yaml) pour le mapping
    ODCS, les requêtes SQL et les seuils. Ainsi, ajouter un nouveau
    rule_type dans le YAML suffit — pas besoin de modifier ce code.
    """
    return _catalog.build_odcs_entry(rule, col_name, dataset_name)


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
            quality.append(_build_odcs_quality_entry(rule, col_name, dataset_name))
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
