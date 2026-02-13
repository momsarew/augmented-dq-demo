"""
Framework Probabiliste DQ v2.0
Orchestrateur principal - délègue chaque onglet à son module dédié.
"""

import os
import sys
import json
from datetime import datetime

import pandas as pd
import streamlit as st

# ============================================================================
# PATHS & IMPORTS
# ============================================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
ENGINE_DIR = os.path.join(BACKEND_DIR, "engine")

sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, ENGINE_DIR)

# CSS
try:
    from streamlit_gray_css import get_gray_css
except Exception:
    def get_gray_css(): return ""

# SÉCURITÉ
try:
    from backend.security import (
        escape_html, sanitize_for_html, sanitize_column_name,
        sanitize_dict_for_html, validate_uploaded_file, sanitize_dataframe,
        sanitize_user_input, sanitize_filename, validate_api_key,
        safe_error_message, mask_api_key, MAX_FILE_SIZE_MB
    )
    SECURITY_OK = True
except ImportError:
    SECURITY_OK = False
    import html
    def escape_html(text): return html.escape(str(text)) if text else ""
    def sanitize_for_html(text, max_length=500): return html.escape(str(text)[:max_length]) if text else ""
    def sanitize_column_name(name): return html.escape(str(name)[:100]) if name else ""
    def sanitize_dict_for_html(d): return d
    def validate_uploaded_file(f): return True, "", None
    def sanitize_dataframe(df): return df
    def sanitize_user_input(text, max_length=500, allow_newlines=False): return str(text)[:max_length] if text else ""
    def sanitize_filename(f): return f.replace('/', '_').replace('\\', '_')[:100] if f else "file"
    def validate_api_key(k): return bool(k and k.startswith('sk-')), ""
    def safe_error_message(e, c=""): return f"Erreur: {str(e)[:100]}"
    def mask_api_key(k): return f"{k[:7]}***" if k and len(k) > 7 else "***"
    MAX_FILE_SIZE_MB = 50

# ENGINE
ENGINE_OK = False
try:
    from backend.engine import analyzer, beta_calculator, ahp_elicitor, risk_scorer, lineage_propagator, comparator
    analyze_dataset = analyzer.analyze_dataset
    compute_all_beta_vectors = beta_calculator.compute_all_beta_vectors
    AHPElicitor = ahp_elicitor.AHPElicitor
    compute_risk_scores = risk_scorer.compute_risk_scores
    get_top_priorities = risk_scorer.get_top_priorities
    simulate_lineage = lineage_propagator.simulate_lineage
    compare_dama_vs_probabiliste = comparator.compare_dama_vs_probabiliste
    ENGINE_OK = True
except Exception as e:
    ENGINE_ERROR = str(e)

# MODULES OPTIONNELS
SCAN_OK = False
try:
    from streamlit_anomaly_detection import render_anomaly_detection_tab
    SCAN_OK = True
except Exception:
    pass

AUDIT_OK = False
try:
    from backend.audit_trail import get_audit_trail, AuditTrail
    from streamlit_audit_tab import render_audit_tab
    AUDIT_OK = True
except Exception:
    pass

# FRONTEND TABS
from frontend.tabs.home import render_home_tab
from frontend.tabs.dashboard import render_dashboard_tab
from frontend.tabs.vectors import render_vectors_tab
from frontend.tabs.priorities import render_priorities_tab
from frontend.tabs.elicitation import render_elicitation_tab
from frontend.tabs.risk_profile import render_risk_profile_tab
from frontend.tabs.lineage import render_lineage_tab
from frontend.tabs.dama import render_dama_tab
from frontend.tabs.reporting import render_reporting_tab
from frontend.tabs.settings import render_settings_tab_full, render_settings_tab_init
from frontend.tabs.help import render_help_tab
from frontend.tabs.data_contracts import render_data_contracts_tab

# ============================================================================
# CONFIG & SESSION STATE
# ============================================================================

st.set_page_config(page_title="Framework Probabiliste DQ", page_icon="🎯", layout="wide")
st.markdown(get_gray_css(), unsafe_allow_html=True)

defaults = {
    "df": None, "results": None, "analysis_done": False,
    "anthropic_api_key": "", "ai_explanations": {},
    "ai_tokens_used": 0, "custom_weights": {}, "selected_profile": "gouvernance",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div style="text-align: center; padding: 1rem 0 2rem 0;">
    <h1 style="margin-bottom: 0.5rem;">🎯 Framework Probabiliste DQ</h1>
    <p style="color: rgba(255,255,255,0.6); font-size: 1.1rem; margin: 0;">
        Analyse de qualité des données basée sur les distributions Beta
    </p>
</div>
""", unsafe_allow_html=True)

if not ENGINE_OK:
    st.error(f"❌ Engine : {ENGINE_ERROR}")
    st.stop()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("📊 Données")

    # Auto-load API key from secrets
    if "anthropic_api_key" not in st.session_state:
        st.session_state.anthropic_api_key = ""
        try:
            if hasattr(st, 'secrets'):
                if 'api' in st.secrets and st.secrets['api'].get('ANTHROPIC_API_KEY'):
                    key = st.secrets['api']['ANTHROPIC_API_KEY']
                    if key and key.strip().startswith('sk-ant-'):
                        st.session_state.anthropic_api_key = key.strip()
                elif st.secrets.get('ANTHROPIC_API_KEY'):
                    key = st.secrets['ANTHROPIC_API_KEY']
                    if key and key.strip().startswith('sk-ant-'):
                        st.session_state.anthropic_api_key = key.strip()
        except Exception:
            pass
        if not st.session_state.anthropic_api_key:
            env_key = os.getenv("ANTHROPIC_API_KEY", "")
            if env_key and env_key.strip().startswith('sk-ant-'):
                st.session_state.anthropic_api_key = env_key.strip()

    if st.session_state.get("anthropic_api_key"):
        st.success("🤖 IA Active", icon="✅")
    else:
        st.info("🤖 IA Inactive", icon="ℹ️")

    st.markdown("---")

    st.subheader("1️⃣ Dataset")
    st.caption(f"📏 Taille max: {MAX_FILE_SIZE_MB} MB")
    up = st.file_uploader("📁 CSV/Excel", type=["csv", "xlsx"])
    if up:
        is_valid, error_msg, validated_df = validate_uploaded_file(up)
        if is_valid and validated_df is not None:
            df = sanitize_dataframe(validated_df)
            st.session_state.df = df
            st.success(f"✅ {len(df)} lignes × {len(df.columns)} colonnes")
            if AUDIT_OK:
                try:
                    audit = get_audit_trail()
                    up.seek(0)
                    file_hash = audit.compute_file_hash(up.read())
                    up.seek(0)
                    audit.log_file_upload(filename=up.name, file_size=up.size, file_hash=file_hash, rows=len(df), columns=len(df.columns), column_names=list(df.columns))
                except Exception:
                    pass
        elif error_msg:
            st.error(f"❌ {error_msg}")
        else:
            try:
                up.seek(0)
                df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                st.session_state.df = df
                st.success(f"✅ {len(df)} lignes")
            except Exception as e:
                st.error(f"❌ {safe_error_message(e, 'file_upload')}")

    if st.session_state.df is not None:
        st.subheader("2️⃣ Colonnes")
        cols = st.session_state.df.columns.tolist()
        sel_cols = st.multiselect("Sélectionner", cols, cols[:3])

        st.subheader("3️⃣ Usages")
        usages_map = {"Paie": "paie_reglementaire", "Reporting": "reporting_social", "Dashboard": "dashboard_operationnel"}
        sel_usages = st.multiselect("Sélectionner", list(usages_map.keys()), ["Paie", "Reporting"])

        if st.button("🚀 ANALYSE", type="primary", use_container_width=True):
            if not sel_cols or not sel_usages:
                st.error("⚠️ Sélectionne colonnes + usages")
            else:
                with st.spinner("⏳"):
                    try:
                        usages = [{"nom": u, "type": usages_map[u], "criticite": "HIGH" if u == "Paie" else "MEDIUM"} for u in sel_usages]
                        df = st.session_state.df
                        stats = analyze_dataset(df, sel_cols)
                        vecteurs = compute_all_beta_vectors(df, sel_cols, stats)

                        ahp = AHPElicitor()
                        weights = {}
                        for u in usages:
                            if u["nom"] in st.session_state.custom_weights:
                                weights[u["nom"]] = st.session_state.custom_weights[u["nom"]]
                            else:
                                weights[u["nom"]] = ahp.get_weights_preset(u["type"])

                        scores = compute_risk_scores(vecteurs, weights, usages)
                        priorities = get_top_priorities(scores, top_n=5)
                        lineage = simulate_lineage(vecteurs[sel_cols[0]], weights[usages[0]["nom"]]) if sel_cols and usages else None
                        dama = compare_dama_vs_probabiliste(df, sel_cols, scores, vecteurs)

                        st.session_state.results = {
                            "stats": stats, "vecteurs_4d": vecteurs, "weights": weights,
                            "scores": scores, "top_priorities": priorities,
                            "lineage": lineage, "comparaison": dama
                        }
                        st.session_state.analysis_done = True
                        st.success("✅ OK")

                        if AUDIT_OK:
                            try:
                                audit = get_audit_trail()
                                audit.log_analysis(analysis_type="full_analysis", columns_analyzed=sel_cols, results_summary={"nb_columns": len(sel_cols), "nb_usages": len(usages), "usages": [u["nom"] for u in usages]})
                                for col in sel_cols:
                                    if col in vecteurs:
                                        v = vecteurs[col]
                                        audit.log_calculation(calculation_type="beta_vectors", column=col, parameters={"usages": [u["nom"] for u in usages]}, results={"P_DB": v.get("P_DB", 0), "P_DP": v.get("P_DP", 0), "P_BR": v.get("P_BR", 0), "P_UP": v.get("P_UP", 0)})
                            except Exception:
                                pass
                    except Exception as e:
                        st.error(f"❌ {e}")
                        import traceback
                        with st.expander("Trace"):
                            st.code(traceback.format_exc())

# ============================================================================
# TABS - Route to dedicated modules
# ============================================================================

if st.session_state.analysis_done:
    r = st.session_state.results

    tab_names = []
    if SCAN_OK:
        tab_names.append("🔍 Scan")
    tab_names += ["📊 Dashboard", "🎯 Vecteurs", "⚠️ Priorités", "🎚️ Élicitation",
                   "🎭 Profil Risque", "🔄 Lineage", "📈 DAMA", "📋 Reporting",
                   "📜 Contracts", "📜 Historique", "⚙️ Paramètres", "❓ Aide"]

    tabs = st.tabs(tab_names)
    idx = 0

    if SCAN_OK:
        with tabs[idx]:
            render_anomaly_detection_tab()
        idx += 1

    with tabs[idx]:
        render_dashboard_tab(r)
    idx += 1

    with tabs[idx]:
        render_vectors_tab(r)
    idx += 1

    with tabs[idx]:
        render_priorities_tab(r)
    idx += 1

    with tabs[idx]:
        render_elicitation_tab(r)
    idx += 1

    with tabs[idx]:
        render_risk_profile_tab(r)
    idx += 1

    with tabs[idx]:
        render_lineage_tab(r)
    idx += 1

    with tabs[idx]:
        render_dama_tab(r, sanitize_column_name)
    idx += 1

    with tabs[idx]:
        render_reporting_tab(r, escape_html, sanitize_user_input)
    idx += 1

    with tabs[idx]:
        render_data_contracts_tab()
    idx += 1

    with tabs[idx]:
        if AUDIT_OK:
            render_audit_tab()
        else:
            st.header("📜 Historique")
            st.warning("Module d'audit non disponible")
    idx += 1

    with tabs[idx]:
        render_settings_tab_full(validate_api_key, mask_api_key)
    idx += 1

    with tabs[idx]:
        render_help_tab(full=True)

else:
    tab_names = ["🏠 Accueil", "📜 Historique", "⚙️ Paramètres", "❓ Aide"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_home_tab()

    with tabs[1]:
        if AUDIT_OK:
            render_audit_tab()
        else:
            st.header("📜 Historique")
            st.warning("Module d'audit non disponible")

    with tabs[2]:
        render_settings_tab_init()

    with tabs[3]:
        render_help_tab(full=False)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 2rem;
    border: 1px solid rgba(255,255,255,0.1);
">
    <p style="text-align: center; color: rgba(255,255,255,0.5); margin: 0; font-size: 0.9rem;">
        Framework Probabiliste DQ v2.0 • Propulsé par Claude AI
    </p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
t = st.session_state.ai_tokens_used
c1.metric("🤖 Tokens IA", f"{t:,}")
c2.metric("💰 Coût session", f"${(t / 1e6) * 9:.4f}")
c3.metric("📊 Explications", len(st.session_state.ai_explanations))
