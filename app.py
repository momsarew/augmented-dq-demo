"""
Framework Probabiliste DQ - Version FINALE COMPLÈTE
Tous les onglets + Élicitation AHP + Reporting Contextuel
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

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
except:
    def get_gray_css(): return ""

# SÉCURITÉ
try:
    from backend.security import (
        escape_html,
        sanitize_for_html,
        sanitize_column_name,
        sanitize_dict_for_html,
        validate_uploaded_file,
        sanitize_dataframe,
        sanitize_user_input,
        sanitize_filename,
        validate_api_key,
        safe_error_message,
        mask_api_key,
        MAX_FILE_SIZE_MB
    )
    SECURITY_OK = True
except ImportError:
    SECURITY_OK = False
    # Fallbacks de sécurité minimaux
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

# IMPORTS ENGINE
ENGINE_OK = False
try:
    os.chdir(ENGINE_DIR)
    import analyzer, beta_calculator, ahp_elicitor, risk_scorer, lineage_propagator, comparator
    
    analyze_dataset = analyzer.analyze_dataset
    compute_all_beta_vectors = beta_calculator.compute_all_beta_vectors
    AHPElicitor = ahp_elicitor.AHPElicitor
    compute_risk_scores = risk_scorer.compute_risk_scores
    get_top_priorities = risk_scorer.get_top_priorities
    simulate_lineage = lineage_propagator.simulate_lineage
    compare_dama_vs_probabiliste = comparator.compare_dama_vs_probabiliste
    
    os.chdir(PROJECT_DIR)
    ENGINE_OK = True
except Exception as e:
    ENGINE_ERROR = str(e)
    os.chdir(PROJECT_DIR)

# Modules optionnels
try:
    from streamlit_anomaly_detection import render_anomaly_detection_tab
    SCAN_OK = True
except:
    SCAN_OK = False

# Audit Trail
try:
    from backend.audit_trail import get_audit_trail, AuditTrail
    from streamlit_audit_tab import render_audit_tab
    AUDIT_OK = True
except Exception as e:
    AUDIT_OK = False
    print(f"Audit trail non disponible: {e}")

# Data Contracts
try:
    from backend.data_contracts import DataContract, ContractValidator, ContractRepository
    from streamlit_data_contracts import render_data_contracts_tab
    CONTRACTS_OK = True
except Exception as e:
    CONTRACTS_OK = False
    print(f"Data contracts non disponible: {e}")

# ============================================================================
# CONFIG
# ============================================================================

st.set_page_config(page_title="Framework Probabiliste DQ", page_icon="🎯", layout="wide")
st.markdown(get_gray_css(), unsafe_allow_html=True)

# Session state
defaults = {
    "df": None,
    "results": None,
    "analysis_done": False,
    "anthropic_api_key": "",
    "ai_explanations": {},
    "ai_tokens_used": 0,
    "custom_weights": {},  # Pour élicitation manuelle
    "selected_profile": "gouvernance",  # Pour reporting
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# UTILS
# ============================================================================

def get_risk_color(s):
    """Couleurs modernes pour les niveaux de risque"""
    if s >= 0.40: return "#eb3349"   # Rouge moderne
    if s >= 0.25: return "#F2994A"   # Orange moderne
    if s >= 0.15: return "#F2C94C"   # Jaune moderne
    return "#38ef7d"                 # Vert moderne

def explain_with_ai(scope, data, cache_key, max_tokens=400):
    # Check cache
    if cache_key in st.session_state.ai_explanations:
        return st.session_state.ai_explanations[cache_key]
    
    # Valider API key
    api_key = st.session_state.get("anthropic_api_key", "").strip()
    if not api_key:
        return "⚠️ Configure ta clé API Claude dans la sidebar"
    
    if not api_key.startswith("sk-ant-"):
        return "⚠️ Clé API invalide (doit commencer par 'sk-ant-')"
    
    prompts = {
        "vector": "Explique vecteur 4D en 3 phrases : dimension critique, cause, action.",
        "priority": "Explique priorité en 3 phrases : pourquoi, impact, action.",
        "lineage": "Explique propagation risque en 3 phrases : aggravation, étape, gain.",
        "dama": "Compare DAMA vs Probabiliste en 3 phrases : limites, avantage, ROI.",
        "global": "Synthèse dashboard en 4 phrases : situation, critiques, actions.",
        "elicitation": "Explique ces pondérations en 3 phrases : justification métier, impact sur calculs, recommandations.",
    }
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=prompts.get(scope, prompts["global"]),
            messages=[{"role": "user", "content": json.dumps({"scope": scope, "data": data})}],
        )
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        st.session_state.ai_tokens_used += tokens_used
        explanation = response.content[0].text
        st.session_state.ai_explanations[cache_key] = explanation
        # Audit: Log requête IA
        if AUDIT_OK:
            try:
                audit = get_audit_trail()
                audit.log_ai_request(
                    request_type=f"explanation_{scope}",
                    prompt_summary=f"Explication pour {scope}",
                    tokens_used=tokens_used,
                    success=True,
                    response_summary=explanation[:100] if explanation else None
                )
            except Exception:
                pass
        return explanation
    except anthropic.AuthenticationError as e:
        return f"⚠️ Erreur authentification : Vérifie ta clé API dans la sidebar (doit être valide et active)"
    except anthropic.RateLimitError as e:
        return f"⚠️ Limite de taux atteinte : Attends quelques secondes et réessaye"
    except Exception as e:
        return f"⚠️ Erreur : {str(e)[:200]}"

def create_vector_chart(v):
    """Graphique moderne pour vecteur 4D avec gradients"""
    dims = ["DB", "DP", "BR", "UP"]
    dim_labels = ["Structure", "Traitements", "Règles Métier", "Utilisabilité"]
    vals = [v.get(f"P_{d}", 0) * 100 for d in dims]

    fig = go.Figure(data=[go.Bar(
        x=dim_labels,
        y=vals,
        marker=dict(
            color=[get_risk_color(x/100) for x in vals],
            line=dict(width=0),
            opacity=0.9
        ),
        text=[f"{x:.1f}%" for x in vals],
        textposition="outside",
        textfont=dict(color="white", size=14, family="Inter"),
        hovertemplate="<b>%{x}</b><br>Probabilité: %{y:.1f}%<extra></extra>"
    )])

    fig.update_layout(
        title=dict(
            text="Vecteur de Risque 4D",
            font=dict(size=18, color="white", family="Inter")
        ),
        height=380,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=dict(text="Probabilité (%)", font=dict(color="rgba(255,255,255,0.7)"))
        ),
        hoverlabel=dict(
            bgcolor="rgba(26,26,46,0.95)",
            font_size=14,
            font_family="Inter"
        )
    )
    return fig

def create_heatmap(scores):
    """Heatmap moderne avec palette personnalisée"""
    attrs, usages = set(), set()
    for k in scores.keys():
        p = k.rsplit("_", 1)
        if len(p) == 2:
            attrs.add(p[0])
            usages.add(p[1])

    attrs, usages = sorted(attrs), sorted(usages)
    matrix = [[float(scores.get(f"{a}_{u}", 0)) * 100 for u in usages] for a in attrs]

    # Palette de couleurs moderne
    custom_colorscale = [
        [0.0, "#38ef7d"],    # Vert (faible risque)
        [0.25, "#F2C94C"],   # Jaune
        [0.5, "#F2994A"],    # Orange
        [0.75, "#f45c43"],   # Orange-rouge
        [1.0, "#eb3349"]     # Rouge (haut risque)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=usages,
        y=attrs,
        colorscale=custom_colorscale,
        colorbar=dict(
            title=dict(text="Risque (%)", font=dict(color="white")),
            tickfont=dict(color="rgba(255,255,255,0.7)"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0
        ),
        text=[[f"{v:.1f}%" for v in r] for r in matrix],
        texttemplate="%{text}",
        textfont=dict(color="white", size=12, family="Inter"),
        hovertemplate="<b>%{y}</b> × %{x}<br>Risque: %{z:.1f}%<extra></extra>"
    ))

    fig.update_layout(
        title=dict(
            text="Matrice des Scores de Risque",
            font=dict(size=18, color="white", family="Inter")
        ),
        height=450,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=100, r=40, t=60, b=60),
        xaxis=dict(
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=dict(text="Profils d'Usage", font=dict(color="rgba(255,255,255,0.7)"))
        ),
        yaxis=dict(
            tickfont=dict(color="rgba(255,255,255,0.7)", size=12),
            title=dict(text="Attributs", font=dict(color="rgba(255,255,255,0.7)"))
        ),
        hoverlabel=dict(
            bgcolor="rgba(26,26,46,0.95)",
            font_size=14,
            font_family="Inter"
        )
    )
    return fig

def export_excel(results):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"resultats_{ts}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        pd.DataFrame([{**{"Attribut": k}, **{f"P_{d}": v.get(f"P_{d}", 0) for d in ["DB","DP","BR","UP"]}} for k, v in results.get("vecteurs_4d", {}).items()]).to_excel(w, sheet_name="Vecteurs", index=False)
        pd.DataFrame([{"Attribut": k.rsplit("_",1)[0], "Usage": k.rsplit("_",1)[1] if "_" in k else "Usage", "Score": float(v)} for k, v in results.get("scores", {}).items()]).to_excel(w, sheet_name="Scores", index=False)
        pd.DataFrame(results.get("top_priorities", [])).to_excel(w, sheet_name="Priorites", index=False)
    return out

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
# SIDEBAR (simplifiée - config API déplacée dans onglet Paramétrage)
# ============================================================================

with st.sidebar:
    st.header("📊 Données")

    # Charger la clé API automatiquement depuis secrets au démarrage
    if "anthropic_api_key" not in st.session_state:
        st.session_state.anthropic_api_key = ""
        # Essayer de charger depuis secrets
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
        # Fallback: variable d'environnement
        if not st.session_state.anthropic_api_key:
            env_key = os.getenv("ANTHROPIC_API_KEY", "")
            if env_key and env_key.strip().startswith('sk-ant-'):
                st.session_state.anthropic_api_key = env_key.strip()

    # Indicateur status API (discret)
    if st.session_state.get("anthropic_api_key"):
        st.success("🤖 IA Active", icon="✅")
    else:
        st.info("🤖 IA Inactive", icon="ℹ️")

    st.markdown("---")

    st.subheader("1️⃣ Dataset")
    st.caption(f"📏 Taille max: {MAX_FILE_SIZE_MB} MB")
    up = st.file_uploader("📁 CSV/Excel", type=["csv", "xlsx"])
    if up:
        # Validation sécurisée du fichier uploadé
        is_valid, error_msg, validated_df = validate_uploaded_file(up)

        if is_valid and validated_df is not None:
            # Sanitiser le DataFrame
            df = sanitize_dataframe(validated_df)
            st.session_state.df = df
            st.success(f"✅ {len(df)} lignes × {len(df.columns)} colonnes")

            # Audit: Log upload fichier
            if AUDIT_OK:
                try:
                    audit = get_audit_trail()
                    up.seek(0)
                    file_hash = audit.compute_file_hash(up.read())
                    up.seek(0)
                    audit.log_file_upload(
                        filename=up.name,
                        file_size=up.size,
                        file_hash=file_hash,
                        rows=len(df),
                        columns=len(df.columns),
                        column_names=list(df.columns)
                    )
                except Exception:
                    pass  # Ne pas bloquer si audit échoue
        elif error_msg:
            st.error(f"❌ {error_msg}")
        else:
            # Fallback: ancien comportement si module sécurité non chargé
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
                        usages = [{"nom": u, "type": usages_map[u], "criticite": "HIGH" if u=="Paie" else "MEDIUM"} for u in sel_usages]
                        
                        df = st.session_state.df
                        stats = analyze_dataset(df, sel_cols)
                        vecteurs = compute_all_beta_vectors(df, sel_cols, stats)
                        
                        # Utiliser custom weights si définis, sinon presets
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
                        
                        st.session_state.results = {"stats": stats, "vecteurs_4d": vecteurs, "weights": weights, "scores": scores, "top_priorities": priorities, "lineage": lineage, "comparaison": dama}
                        st.session_state.analysis_done = True
                        st.success("✅ OK")

                        # Audit: Log analyse complète
                        if AUDIT_OK:
                            try:
                                audit = get_audit_trail()
                                # Log analyse dataset
                                audit.log_analysis(
                                    analysis_type="full_analysis",
                                    columns_analyzed=sel_cols,
                                    results_summary={
                                        "nb_columns": len(sel_cols),
                                        "nb_usages": len(usages),
                                        "usages": [u["nom"] for u in usages]
                                    }
                                )
                                # Log calculs vecteurs
                                for col in sel_cols:
                                    if col in vecteurs:
                                        v = vecteurs[col]
                                        audit.log_calculation(
                                            calculation_type="beta_vectors",
                                            column=col,
                                            parameters={"usages": [u["nom"] for u in usages]},
                                            results={
                                                "P_DB": v.get("P_DB", 0),
                                                "P_DP": v.get("P_DP", 0),
                                                "P_BR": v.get("P_BR", 0),
                                                "P_UP": v.get("P_UP", 0)
                                            }
                                        )
                                # Log scores
                                for col, col_scores in scores.items():
                                    for usage, score_data in col_scores.items():
                                        if isinstance(score_data, dict):
                                            audit.log_score(
                                                score_type="risk_score",
                                                column=col,
                                                score_value=score_data.get("score", 0),
                                                weights=weights.get(usage, {}),
                                                components=score_data
                                            )
                            except Exception:
                                pass  # Ne pas bloquer si audit échoue
                    except Exception as e:
                        st.error(f"❌ {e}")
                        import traceback
                        with st.expander("Trace"):
                            st.code(traceback.format_exc())

# ============================================================================
# TABS - Structure avec onglets toujours accessibles
# ============================================================================

# Construire liste tabs selon état
if st.session_state.analysis_done:
    tab_names = []
    if SCAN_OK:
        tab_names.append("🔍 Scan")
    tab_names += ["📊 Dashboard", "🎯 Vecteurs", "⚠️ Priorités", "🎚️ Élicitation", "🎭 Profil Risque", "🔄 Lineage", "📈 DAMA", "📋 Reporting", "📜 Contracts", "📜 Historique", "⚙️ Paramètres", "❓ Aide"]
else:
    # Avant analyse : seulement Accueil, Contracts, Historique, Paramètres et Aide
    tab_names = ["🏠 Accueil", "📜 Contracts", "📜 Historique", "⚙️ Paramètres", "❓ Aide"]

tabs = st.tabs(tab_names)
idx = 0

if st.session_state.analysis_done:
    r = st.session_state.results

    # TAB SCAN (si disponible)
    if SCAN_OK:
        with tabs[idx]:
            render_anomaly_detection_tab()
        idx += 1

    # TAB DASHBOARD
    with tabs[idx]:
        st.header("📊 Dashboard Qualité")
        
        if st.button("📥 Export Excel", type="primary"):
            try:
                out = export_excel(r)
                with open(out, "rb") as f:
                    st.download_button("💾 Télécharger", f, out, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.success(f"✅ {out}")
                # Audit: Log export
                if AUDIT_OK:
                    try:
                        audit = get_audit_trail()
                        audit.log_export("results_excel", out, "xlsx", rows=len(r.get("vecteurs_4d", {})))
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"❌ {e}")
        
        st.markdown("---")
        
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Attributs", len(r["vecteurs_4d"]))
        c2.metric("Usages", len(r["weights"]))
        c3.metric("Risque max", f"{max(r['scores'].values()):.1%}")
        c4.metric("Alertes", len([s for s in r["scores"].values() if s>0.4]))
        
        st.markdown("---")
        
        if r.get("scores"):
            st.plotly_chart(create_heatmap(r["scores"]), use_container_width=True)
        
        st.markdown("---")
        st.subheader("💬 Assistance IA")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🤖 Analyser", key="dash"):
                exp = explain_with_ai("global", {"nb": len(r["vecteurs_4d"]), "max": max(r["scores"].values())}, "dash", 500)
                st.session_state.dash_exp = exp
        with col2:
            if "dash_exp" in st.session_state:
                st.info(st.session_state.dash_exp)
    
    idx += 1
    
    # TAB VECTEURS
    with tabs[idx]:
        st.header("🎯 Vecteurs 4D")
        
        for attr, vec in r["vecteurs_4d"].items():
            st.subheader(f"📌 {attr}")
            st.plotly_chart(create_vector_chart(vec), use_container_width=True, key=f"vec_{attr}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💬 Expliquer", key=f"v_{attr}"):
                    exp = explain_with_ai("vector", {f"P_{d}": vec[f"P_{d}"] for d in ["DB","DP","BR","UP"]}, f"v_{attr}", 400)
                    st.session_state[f"v_{attr}_exp"] = exp
            with col2:
                if f"v_{attr}_exp" in st.session_state:
                    st.info(st.session_state[f"v_{attr}_exp"])
            
            with st.expander("🔬 Détails Beta"):
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f"**DB**: Beta({vec['alpha_DB']:.1f}, {vec['beta_DB']:.1f})\nP={vec['P_DB']:.3f}")
                c2.markdown(f"**DP**: Beta({vec['alpha_DP']:.1f}, {vec['beta_DP']:.1f})\nP={vec['P_DP']:.3f}")
                c3.markdown(f"**BR**: Beta({vec['alpha_BR']:.1f}, {vec['beta_BR']:.1f})\nP={vec['P_BR']:.3f}")
                c4.markdown(f"**UP**: Beta({vec['alpha_UP']:.1f}, {vec['beta_UP']:.1f})\nP={vec['P_UP']:.3f}")
            
            st.markdown("---")
    
    idx += 1
    
    # TAB PRIORITÉS
    with tabs[idx]:
        st.header("⚠️ Top Priorités")
        
        for i, p in enumerate(r["top_priorities"], 1):
            emoji = "🚨" if p.get("severite")=="CRITIQUE" else "⚠️"
            st.markdown(f"### {emoji} #{i} - {p.get('attribut')} × {p.get('usage')}")
            st.markdown(f"**Risque** : {p.get('score', 0):.1%}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💬 Analyser", key=f"p{i}"):
                    exp = explain_with_ai("priority", {"score": p.get("score"), "sev": p.get("severite")}, f"p{i}", 500)
                    st.session_state[f"p{i}_exp"] = exp
            with col2:
                if f"p{i}_exp" in st.session_state:
                    st.warning(st.session_state[f"p{i}_exp"])
            
            st.markdown("---")
    
    idx += 1
    
    # ========================================================================
    # TAB ÉLICITATION AHP ⭐ CRITIQUE
    # ========================================================================
    
    with tabs[idx]:
        st.header("🎚️ Élicitation Pondérations AHP")
        
        st.info("Configure les pondérations pour chaque usage. Utilise les presets ou définis tes propres valeurs.")
        
        # Pour chaque usage
        for usage_nom, weights in r.get("weights", {}).items():
            st.subheader(f"📌 {usage_nom}")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Sliders pour ajuster
                st.markdown("**Ajuster pondérations** :")
                
                w_db = st.slider(f"DB (Structure)", 0.0, 1.0, float(weights.get("w_DB", 0.25)), 0.05, key=f"w_db_{usage_nom}")
                w_dp = st.slider(f"DP (Traitements)", 0.0, 1.0, float(weights.get("w_DP", 0.25)), 0.05, key=f"w_dp_{usage_nom}")
                w_br = st.slider(f"BR (Règles Métier)", 0.0, 1.0, float(weights.get("w_BR", 0.25)), 0.05, key=f"w_br_{usage_nom}")
                w_up = st.slider(f"UP (Utilisabilité)", 0.0, 1.0, float(weights.get("w_UP", 0.25)), 0.05, key=f"w_up_{usage_nom}")
                
                # Normaliser
                total = w_db + w_dp + w_br + w_up
                if total > 0:
                    w_db_norm, w_dp_norm, w_br_norm, w_up_norm = w_db/total, w_dp/total, w_br/total, w_up/total
                else:
                    w_db_norm = w_dp_norm = w_br_norm = w_up_norm = 0.25
                
                st.markdown("**Pondérations normalisées** :")
                st.json({"w_DB": f"{w_db_norm:.2%}", "w_DP": f"{w_dp_norm:.2%}", "w_BR": f"{w_br_norm:.2%}", "w_UP": f"{w_up_norm:.2%}"})
                
                if st.button(f"💾 Sauvegarder pour {usage_nom}", key=f"save_{usage_nom}"):
                    new_weights = {"w_DB": w_db_norm, "w_DP": w_dp_norm, "w_BR": w_br_norm, "w_UP": w_up_norm}
                    st.session_state.custom_weights[usage_nom] = new_weights
                    st.success(f"✅ Pondérations sauvegardées pour {usage_nom}. Relance analyse pour appliquer.")
                    # Audit: Log pondérations AHP
                    if AUDIT_OK:
                        try:
                            audit = get_audit_trail()
                            audit.log_ahp_weights(usage_nom, new_weights)
                        except Exception:
                            pass
            
            with col2:
                # Graphique pondérations moderne
                dim_labels = ["Structure", "Traitements", "Règles", "Utilisabilité"]
                fig = go.Figure(data=[go.Bar(
                    x=dim_labels,
                    y=[w_db_norm*100, w_dp_norm*100, w_br_norm*100, w_up_norm*100],
                    marker=dict(
                        color=["#667eea", "#764ba2", "#f093fb", "#38ef7d"],
                        line=dict(width=0),
                        opacity=0.9
                    ),
                    text=[f"{x:.1f}%" for x in [w_db_norm*100, w_dp_norm*100, w_br_norm*100, w_up_norm*100]],
                    textposition="outside",
                    textfont=dict(color="white", size=12, family="Inter"),
                    hovertemplate="<b>%{x}</b><br>Pondération: %{y:.1f}%<extra></extra>"
                )])
                fig.update_layout(
                    title=dict(
                        text=f"Pondérations {usage_nom}",
                        font=dict(size=16, color="white", family="Inter")
                    ),
                    height=320,
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    margin=dict(l=30, r=30, t=50, b=30),
                    xaxis=dict(
                        showgrid=False,
                        tickfont=dict(color="rgba(255,255,255,0.7)", size=11)
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="rgba(255,255,255,0.1)",
                        tickfont=dict(color="rgba(255,255,255,0.7)", size=11)
                    ),
                    hoverlabel=dict(
                        bgcolor="rgba(26,26,46,0.95)",
                        font_size=13,
                        font_family="Inter"
                    )
                )
                st.plotly_chart(fig, use_container_width=True, key=f"fig_{usage_nom}")
            
            # Assistance IA
            st.markdown("---")
            col_btn, col_exp = st.columns([1, 4])
            with col_btn:
                if st.button("💬 Justifier", key=f"elicit_{usage_nom}"):
                    exp = explain_with_ai("elicitation", {"usage": usage_nom, "weights": {"w_DB": w_db_norm, "w_DP": w_dp_norm, "w_BR": w_br_norm, "w_UP": w_up_norm}}, f"elicit_{usage_nom}", 500)
                    st.session_state[f"elicit_{usage_nom}_exp"] = exp
            with col_exp:
                if f"elicit_{usage_nom}_exp" in st.session_state:
                    st.info(st.session_state[f"elicit_{usage_nom}_exp"])
            
            st.markdown("---")

    idx += 1

    # ========================================================================
    # TAB PROFIL DE RISQUE - Ajustement des pondérations selon appétence
    # ========================================================================
    with tabs[idx]:
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

        # Sélection du profil de risque
        st.subheader("1️⃣ Choisis ton profil")

        profils_risque = {
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

        # Initialiser le profil de risque dans session state
        if "profil_risque" not in st.session_state:
            st.session_state.profil_risque = "equilibre"

        cols_profil = st.columns(5)
        for i, (key, profil) in enumerate(profils_risque.items()):
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
                    old_profil = st.session_state.get("profil_risque", "equilibre")
                    st.session_state.profil_risque = key
                    # Audit: Log changement profil
                    if AUDIT_OK:
                        try:
                            audit = get_audit_trail()
                            audit.log_profile_selection(
                                profile_name=profil['nom'],
                                profile_type=key,
                                weights={"multiplicateur": profil['multiplicateur']}
                            )
                        except Exception:
                            pass
                    st.rerun()

        # Afficher détails du profil sélectionné
        profil_actuel = profils_risque[st.session_state.profil_risque]
        st.markdown("---")

        st.subheader(f"2️⃣ Ton profil : {profil_actuel['nom']}")
        st.info(f"📋 {profil_actuel['description']}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🔢 Multiplicateur de risque**")
            mult = profil_actuel['multiplicateur']
            if mult > 1:
                st.warning(f"Les scores sont **amplifiés** de {(mult-1)*100:.0f}%")
            elif mult < 1:
                st.success(f"Les scores sont **atténués** de {(1-mult)*100:.0f}%")
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

        # Aperçu de l'impact sur les scores actuels
        st.subheader("3️⃣ Impact sur tes scores actuels")

        scores = r.get("scores", {})
        if scores:
            mult = profil_actuel['multiplicateur']
            seuils = profil_actuel['seuils']

            # Calculer scores ajustés
            scores_ajustes = []
            for key, score in scores.items():
                score_ajuste = min(1.0, score * mult)
                parts = key.rsplit("_", 1)
                attr = parts[0] if len(parts) == 2 else key
                usage = parts[1] if len(parts) == 2 else "N/A"

                # Déterminer le niveau selon les seuils ajustés
                if score_ajuste >= seuils['critique']:
                    niveau = "🔴 Critique"
                    color = "#eb3349"
                elif score_ajuste >= seuils['eleve']:
                    niveau = "🟠 Élevé"
                    color = "#F2994A"
                elif score_ajuste >= seuils['modere']:
                    niveau = "🟡 Modéré"
                    color = "#F2C94C"
                else:
                    niveau = "🟢 Faible"
                    color = "#38ef7d"

                scores_ajustes.append({
                    "attribut": attr,
                    "usage": usage,
                    "score_original": score,
                    "score_ajuste": score_ajuste,
                    "niveau": niveau,
                    "color": color
                })

            # Trier par score ajusté décroissant
            scores_ajustes.sort(key=lambda x: x["score_ajuste"], reverse=True)

            # Afficher tableau
            st.markdown("| Attribut | Usage | Score Original | Score Ajusté | Niveau |")
            st.markdown("|----------|-------|----------------|--------------|--------|")
            for s in scores_ajustes[:10]:  # Top 10
                st.markdown(f"| {s['attribut']} | {s['usage']} | {s['score_original']:.1%} | **{s['score_ajuste']:.1%}** | {s['niveau']} |")

            # Stats
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

            # Sauvegarder les scores ajustés dans session state
            st.session_state.scores_ajustes = {
                f"{s['attribut']}_{s['usage']}": s['score_ajuste'] for s in scores_ajustes
            }
            st.session_state.seuils_profil = seuils

        else:
            st.warning("Aucun score disponible")

        # Demande à l'IA des recommandations
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

    idx += 1

    # TAB LINEAGE
    with tabs[idx]:
        st.header("🔄 Propagation Lineage")
        
        lineage = r.get("lineage")
        if lineage:
            c1, c2 = st.columns(2)
            c1.metric("Risque source", f"{lineage.get('risk_source', 0):.1%}")
            c2.metric("Risque final", f"{lineage.get('risk_final', 0):.1%}")
            
            st.markdown("---")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💬 Analyser Propagation", key="lineage"):
                    exp = explain_with_ai("lineage", {"risk_source": lineage.get("risk_source"), "risk_final": lineage.get("risk_final")}, "lineage", 450)
                    st.session_state.lineage_exp = exp
            with col2:
                if "lineage_exp" in st.session_state:
                    st.info(st.session_state.lineage_exp)
        else:
            st.info("Aucune simulation disponible")
    
    idx += 1
    
    # TAB DAMA
    with tabs[idx]:
        st.header("📈 Comparaison DAMA")

        comp = r.get("comparaison", {})
        if comp:
            dama_scores = comp.get("dama_scores", {})

            # Fonction pour obtenir la couleur selon le score
            def get_score_color(score):
                if score is None: return "#6b7280"  # Gris pour N/A
                if score >= 0.8: return "#38ef7d"   # Vert
                if score >= 0.6: return "#F2C94C"   # Jaune
                if score >= 0.4: return "#F2994A"   # Orange
                return "#eb3349"                    # Rouge

            # Mapping des dimensions DAMA avec icônes
            dim_info = {
                "completeness": {"label": "Complétude", "icon": "📊", "desc": "Données présentes vs attendues"},
                "consistency": {"label": "Cohérence", "icon": "🔗", "desc": "Uniformité entre sources"},
                "accuracy": {"label": "Exactitude", "icon": "🎯", "desc": "Conformité à la réalité"},
                "timeliness": {"label": "Fraîcheur", "icon": "⏱️", "desc": "Actualité des données"},
                "validity": {"label": "Validité", "icon": "✅", "desc": "Respect des règles métier"},
                "uniqueness": {"label": "Unicité", "icon": "🔑", "desc": "Données sans doublons"}
            }

            # Afficher chaque attribut dans une card
            for attr_name, attr_data in dama_scores.items():
                # SÉCURITÉ: Échapper le nom d'attribut pour prévenir XSS
                safe_attr_name = sanitize_column_name(attr_name)
                st.markdown(f"""
                <div style="
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 16px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                ">
                    <h3 style="color: white; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;">
                        📌 {safe_attr_name}
                    </h3>
                </div>
                """, unsafe_allow_html=True)

                # Score global en haut
                score_global = attr_data.get("score_global", 0)
                dims_calc = attr_data.get("dimensions_calculables", 0)
                dims_total = attr_data.get("dimensions_total", 6)

                col_score, col_info = st.columns([1, 2])

                with col_score:
                    # Jauge circulaire avec Plotly
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=score_global * 100,
                        number={"suffix": "%", "font": {"size": 36, "color": "white"}},
                        gauge={
                            "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.3)"},
                            "bar": {"color": get_score_color(score_global)},
                            "bgcolor": "rgba(255,255,255,0.1)",
                            "borderwidth": 0,
                            "steps": [
                                {"range": [0, 40], "color": "rgba(235,51,73,0.2)"},
                                {"range": [40, 60], "color": "rgba(242,153,74,0.2)"},
                                {"range": [60, 80], "color": "rgba(242,201,76,0.2)"},
                                {"range": [80, 100], "color": "rgba(56,239,125,0.2)"}
                            ]
                        },
                        title={"text": "Score Global", "font": {"size": 14, "color": "rgba(255,255,255,0.7)"}}
                    ))
                    fig_gauge.update_layout(
                        height=200,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font={"color": "white"},
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{attr_name}")

                with col_info:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                        border-radius: 12px;
                        padding: 1rem;
                        margin-bottom: 0.5rem;
                    ">
                        <p style="color: rgba(255,255,255,0.6); margin: 0; font-size: 0.85rem;">Dimensions analysables</p>
                        <p style="color: white; margin: 0.25rem 0 0 0; font-size: 1.5rem; font-weight: 600;">
                            {dims_calc} <span style="color: rgba(255,255,255,0.5); font-size: 1rem;">/ {dims_total}</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    note = attr_data.get("note", "")
                    if note:
                        st.caption(f"ℹ️ {note}")

                # Grille des 6 dimensions DAMA
                st.markdown("<p style='color: rgba(255,255,255,0.7); margin: 1rem 0 0.5rem 0; font-weight: 500;'>Dimensions DAMA</p>", unsafe_allow_html=True)

                cols = st.columns(3)
                dims_list = ["completeness", "consistency", "accuracy", "timeliness", "validity", "uniqueness"]

                for i, dim_key in enumerate(dims_list):
                    with cols[i % 3]:
                        dim_value = attr_data.get(dim_key)
                        info = dim_info.get(dim_key, {"label": dim_key, "icon": "📊", "desc": ""})

                        if dim_value is None:
                            display_value = "N/A"
                            color = "#6b7280"
                            bg_color = "rgba(107, 114, 128, 0.1)"
                        else:
                            # Afficher avec 1 décimale si valeur < 5% pour éviter confusion "0%"
                            if dim_value < 0.05 and dim_value > 0:
                                display_value = f"{dim_value:.1%}"
                            else:
                                display_value = f"{dim_value:.0%}"
                            color = get_score_color(dim_value)
                            bg_color = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)"

                        st.markdown(f"""
                        <div style="
                            background: {bg_color};
                            border: 1px solid {color}40;
                            border-radius: 12px;
                            padding: 1rem;
                            margin-bottom: 0.75rem;
                            text-align: center;
                        ">
                            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{info['icon']}</div>
                            <div style="color: rgba(255,255,255,0.7); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">{info['label']}</div>
                            <div style="color: {color}; font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0;">{display_value}</div>
                            <div style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">{info['desc']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")

            # Graphique comparatif de tous les attributs
            if len(dama_scores) > 1:
                st.subheader("📊 Vue Comparative")

                attr_names = list(dama_scores.keys())
                global_scores = [dama_scores[a].get("score_global", 0) * 100 for a in attr_names]

                fig_comp = go.Figure(data=[go.Bar(
                    x=attr_names,
                    y=global_scores,
                    marker=dict(
                        color=[get_score_color(s/100) for s in global_scores],
                        opacity=0.9
                    ),
                    text=[f"{s:.1f}%" for s in global_scores],
                    textposition="outside",
                    textfont=dict(color="white", size=12),
                    hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}%<extra></extra>"
                )])

                fig_comp.update_layout(
                    title=dict(text="Scores Globaux DAMA par Attribut", font=dict(size=16, color="white")),
                    height=350,
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(tickfont=dict(color="rgba(255,255,255,0.7)")),
                    yaxis=dict(
                        tickfont=dict(color="rgba(255,255,255,0.7)"),
                        gridcolor="rgba(255,255,255,0.1)",
                        title=dict(text="Score (%)", font=dict(color="rgba(255,255,255,0.7)"))
                    ),
                    hoverlabel=dict(bgcolor="rgba(26,26,46,0.95)", font_size=13)
                )
                st.plotly_chart(fig_comp, use_container_width=True)

            st.markdown("---")

            # Assistance IA
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("💬 Synthétiser", key="dama"):
                    exp = explain_with_ai("dama", {"dama": comp.get("dama_scores"), "masked": len(comp.get("problemes_masques", []))}, "dama", 500)
                    st.session_state.dama_exp = exp
            with col2:
                if "dama_exp" in st.session_state:
                    st.success(st.session_state.dama_exp)
        else:
            st.info("Aucune comparaison disponible")
    
    idx += 1
    
    # ========================================================================
    # TAB REPORTING CONTEXTUEL ⭐ CRITIQUE
    # ========================================================================
    
    with tabs[idx]:
        st.header("📋 Restitution Adaptative")

        st.info("🎯 Rapport personnalisé selon TON profil métier")

        # Sélection profil
        profils = {
            "cfo": "💰 CFO (Chief Financial Officer)",
            "data_engineer": "🔧 Data Engineer / Développeur",
            "drh": "👥 DRH (Directeur Ressources Humaines)",
            "auditeur": "🔍 Auditeur / Compliance Officer",
            "gouvernance": "📊 Responsable Gouvernance Données",
            "manager_ops": "⚡ Manager Opérationnel",
            "custom": "✏️ Profil personnalisé..."
        }

        col1, col2 = st.columns(2)

        with col1:
            profil_select = st.selectbox("👤 Ton profil", options=list(profils.keys()), format_func=lambda x: profils[x], index=4)
            st.session_state.selected_profile = profil_select

            # Si profil personnalisé, afficher les champs de saisie
            if profil_select == "custom":
                st.markdown("---")
                st.markdown("**📝 Définir ton profil personnalisé**")

                custom_titre_raw = st.text_input(
                    "Intitulé du poste",
                    placeholder="Ex: Chief Data Officer, Analyste BI, Product Owner...",
                    key="custom_profile_title",
                    max_chars=100  # Limite de caractères
                )
                # SÉCURITÉ: Sanitiser l'input
                custom_titre = sanitize_user_input(custom_titre_raw, max_length=100)

                custom_description_raw = st.text_area(
                    "Description du rôle / Responsabilités",
                    placeholder="Ex: Responsable de la stratégie data, supervision des équipes analytics, reporting au COMEX...",
                    height=100,
                    key="custom_profile_desc",
                    max_chars=500  # Limite de caractères
                )
                # SÉCURITÉ: Sanitiser l'input (autoriser les retours à la ligne)
                custom_description = sanitize_user_input(custom_description_raw, max_length=500, allow_newlines=True)

                custom_focus_raw = st.text_input(
                    "Focus principal / Préoccupations clés",
                    placeholder="Ex: ROI des projets data, conformité RGPD, adoption des outils...",
                    key="custom_profile_focus",
                    max_chars=200  # Limite de caractères
                )
                # SÉCURITÉ: Sanitiser l'input
                custom_focus = sanitize_user_input(custom_focus_raw, max_length=200)

                # Construire le profil personnalisé
                if custom_titre:
                    profils["custom"] = f"✏️ {escape_html(custom_titre)}"

        with col2:
            # Sélection attributs (multiselect)
            attributs = list(r.get("vecteurs_4d", {}).keys())
            if attributs:
                attributs_focus = st.multiselect(
                    "📌 Attribut(s) à analyser",
                    options=attributs,
                    default=[attributs[0]] if attributs else [],
                    help="Sélectionne un ou plusieurs attributs pour le rapport"
                )
            else:
                st.warning("Aucun attribut analysé")
                attributs_focus = []

        # Sélection usage
        usages_list = list(r.get("weights", {}).keys())
        if usages_list and attributs_focus:
            usage_focus = st.selectbox("🎯 Usage métier", options=usages_list)
            
            st.markdown("---")
            
            # Vérifier si profil personnalisé est complet
            can_generate = True
            if profil_select == "custom":
                if not st.session_state.get("custom_profile_title"):
                    st.warning("⚠️ Renseigne l'intitulé de ton profil personnalisé")
                    can_generate = False

            # Afficher nombre d'attributs sélectionnés
            st.info(f"📊 **{len(attributs_focus)} attribut(s) sélectionné(s)** pour le rapport")

            # Générer rapport
            if st.button("📄 Générer Rapport Personnalisé", type="primary", use_container_width=True) and can_generate:
                with st.spinner("🤖 Claude génère ton rapport..."):
                    try:
                        # Récupérer les pondérations réelles
                        weights_data = r.get("weights", {}).get(usage_focus, {})

                        # Récupérer le lineage si disponible
                        lineage_data = r.get("lineage", {})

                        # Construire le profil pour le prompt
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

                        # Préparer les données pour TOUS les attributs sélectionnés
                        attributs_data = []
                        for attr in attributs_focus:
                            vecteur = r["vecteurs_4d"].get(attr, {})
                            score = r["scores"].get(f"{attr}_{usage_focus}", 0)

                            # Récupérer les scores DAMA réels
                            dama_data = {}
                            if r.get("comparaison") and r["comparaison"].get("dama_scores"):
                                dama_data = r["comparaison"]["dama_scores"].get(attr, {})

                            # Récupérer les priorités réelles pour cet attribut
                            priorities_for_attr = [p for p in r.get("top_priorities", []) if p.get("attribut") == attr]

                            # Identifier la dimension critique pour cet attribut
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
                                "dimension_critique": {
                                    "nom": dimension_critique[0],
                                    "valeur": round(dimension_critique[1], 4)
                                },
                                "scores_dama": {
                                    "completude": dama_data.get("completeness"),
                                    "unicite": dama_data.get("uniqueness"),
                                    "score_global_dama": dama_data.get("score_global")
                                },
                                "priorites": priorities_for_attr[:3] if priorities_for_attr else []
                            })

                        # Trier par score de risque décroissant
                        attributs_data.sort(key=lambda x: x["score_risque"], reverse=True)

                        # Calculer les stats globales
                        scores_list = [a["score_risque"] for a in attributs_data]
                        attribut_plus_risque = attributs_data[0] if attributs_data else None

                        # Prompt rapport complet avec TOUTES les données réelles
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

                        # Appel IA pour rapport complet
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
            
            # Afficher rapport généré
            if "rapport_genere" in st.session_state:
                st.markdown("---")

                # Afficher le bon nom de profil
                if profil_select == "custom":
                    profil_affiche = st.session_state.get("custom_profile_title", "Profil personnalisé")
                    profil_filename = "custom_" + profil_affiche.replace(" ", "_")[:20]
                else:
                    profil_affiche = profils[profil_select]
                    profil_filename = profil_select

                nb_attrs_rapport = len(attributs_focus)
                attrs_str = ", ".join(attributs_focus[:3]) + ("..." if nb_attrs_rapport > 3 else "")
                st.success(f"✅ Rapport généré pour : **{profil_affiche}** | {nb_attrs_rapport} attribut(s) : {attrs_str}")

                # Audit: Log génération rapport
                if AUDIT_OK:
                    try:
                        audit = get_audit_trail()
                        audit.log_report_generation(
                            report_type=f"rapport_{profil_select}",
                            format="markdown",
                            columns_included=nb_attrs_rapport
                        )
                    except Exception:
                        pass

                with st.expander("📄 Ton Rapport Personnalisé", expanded=True):
                    st.markdown(st.session_state.rapport_genere)

                # Download
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

    idx += 1

    # ========================================================================
    # TAB DATA CONTRACTS
    # ========================================================================
    with tabs[idx]:
        if CONTRACTS_OK:
            render_data_contracts_tab()
        else:
            st.header("📜 Data Contracts")
            st.warning("Module Data Contracts non disponible")

    idx += 1

    # ========================================================================
    # TAB HISTORIQUE - Audit Trail
    # ========================================================================
    with tabs[idx]:
        if AUDIT_OK:
            render_audit_tab()
        else:
            st.header("📜 Historique")
            st.warning("Module d'audit non disponible")

    idx += 1

    # ========================================================================
    # TAB PARAMÈTRES - Configuration API et préférences
    # ========================================================================
    with tabs[idx]:
        st.header("⚙️ Paramètres")

        # =====================================================================
        # CHARGEMENT AUTOMATIQUE DE LA CLÉ API DEPUIS SECRETS
        # =====================================================================
        # La clé est chargée depuis .streamlit/secrets.toml (local)
        # ou depuis Streamlit Cloud Secrets (déployé)
        # L'utilisateur normal ne peut PAS voir ou modifier la clé

        def load_api_key_from_secrets():
            """Charge la clé API depuis les secrets de manière sécurisée"""
            try:
                # Priorité 1: Streamlit secrets (fichier local ou Cloud)
                if hasattr(st, 'secrets'):
                    # Essayer le format nested (api.ANTHROPIC_API_KEY)
                    if 'api' in st.secrets and 'ANTHROPIC_API_KEY' in st.secrets['api']:
                        key = st.secrets['api']['ANTHROPIC_API_KEY']
                        if key and key.strip():
                            return key.strip()
                    # Essayer le format flat (ANTHROPIC_API_KEY)
                    if 'ANTHROPIC_API_KEY' in st.secrets:
                        key = st.secrets['ANTHROPIC_API_KEY']
                        if key and key.strip():
                            return key.strip()
            except Exception:
                pass

            # Priorité 2: Variable d'environnement
            try:
                key = os.getenv("ANTHROPIC_API_KEY", "")
                if key and key.strip():
                    return key.strip()
            except Exception:
                pass

            return ""

        def check_admin_password():
            """Vérifie si le mot de passe admin est correct"""
            try:
                if hasattr(st, 'secrets') and 'admin' in st.secrets:
                    return st.secrets['admin'].get('ADMIN_PASSWORD', '')
            except Exception:
                pass
            return "admin"  # Mot de passe par défaut si pas configuré

        # Charger la clé API automatiquement au démarrage
        if "anthropic_api_key" not in st.session_state or not st.session_state.anthropic_api_key:
            loaded_key = load_api_key_from_secrets()
            if loaded_key:
                is_valid, _ = validate_api_key(loaded_key)
                if is_valid:
                    st.session_state.anthropic_api_key = loaded_key

        # =====================================================================
        # AFFICHAGE POUR UTILISATEUR NORMAL
        # =====================================================================

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="color: white; margin: 0 0 0.5rem 0;">🔧 Configuration de l'application</h3>
            <p style="color: rgba(255,255,255,0.8); margin: 0;">
                Statut de l'application et préférences utilisateur.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Section Status API (lecture seule pour utilisateur normal)
        st.subheader("🔑 Statut API Claude")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            L'API Claude permet d'activer les fonctionnalités d'**assistance IA** :
            - 💬 Explications contextuelles des résultats
            - 📋 Génération de rapports personnalisés
            - 🎭 Recommandations selon ton profil de risque
            - 🧠 Synthèses intelligentes
            """)

            has_key = bool(st.session_state.get("anthropic_api_key"))

            if has_key:
                st.success("✅ L'API Claude est configurée et prête à l'emploi")
                # Afficher consommation
                tokens = st.session_state.get("ai_tokens_used", 0)
                cost = (tokens / 1e6) * 9
                st.metric("Tokens utilisés (session)", f"{tokens:,}", delta=f"≈ ${cost:.4f}")
            else:
                st.warning("⚠️ L'API Claude n'est pas configurée")
                st.info("💡 Contactez l'administrateur pour activer les fonctionnalités IA")

        with col2:
            # Status card
            has_key = bool(st.session_state.get("anthropic_api_key"))
            status_color = "#38ef7d" if has_key else "#eb3349"
            status_text = "Active" if has_key else "Inactive"
            status_icon = "✅" if has_key else "⏸️"

            st.markdown(f"""
            <div style="
                background: {status_color}20;
                border: 2px solid {status_color};
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
            ">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">{status_icon}</div>
                <div style="color: {status_color}; font-weight: 700; font-size: 1.2rem;">IA {status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # =====================================================================
        # SECTION ADMIN (protégée par mot de passe)
        # =====================================================================

        with st.expander("🔐 Administration (accès restreint)", expanded=False):
            st.warning("⚠️ Cette section est réservée à l'administrateur")

            # Vérifier si déjà authentifié
            if not st.session_state.get("admin_authenticated", False):
                admin_pwd = st.text_input(
                    "Mot de passe administrateur",
                    type="password",
                    key="admin_password_input",
                    placeholder="Entrer le mot de passe admin..."
                )

                if st.button("🔓 Se connecter", type="primary"):
                    correct_pwd = check_admin_password()
                    if admin_pwd == correct_pwd:
                        st.session_state.admin_authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect")

            else:
                # Admin authentifié - afficher les options de configuration
                st.success("✅ Connecté en tant qu'administrateur")

                if st.button("🚪 Se déconnecter"):
                    st.session_state.admin_authenticated = False
                    st.rerun()

                st.markdown("---")
                st.subheader("🔑 Configuration API Claude")

                # Afficher la clé actuelle (masquée)
                current_key = st.session_state.get("anthropic_api_key", "")
                if current_key:
                    st.info(f"Clé actuelle: {mask_api_key(current_key)}")

                # Permettre de modifier la clé
                new_api_key = st.text_input(
                    "Nouvelle clé API Anthropic",
                    type="password",
                    placeholder="sk-ant-api03-...",
                    help="Entrez une nouvelle clé pour remplacer l'existante",
                    max_chars=200
                )

                if st.button("💾 Sauvegarder la clé", type="primary"):
                    if new_api_key:
                        clean_key = new_api_key.strip()
                        is_valid, error_msg = validate_api_key(clean_key)

                        if is_valid:
                            st.session_state.anthropic_api_key = clean_key
                            st.success(f"✅ Clé API mise à jour: {mask_api_key(clean_key)}")

                            # Instructions pour rendre persistant
                            st.info("""
                            **Pour rendre cette clé persistante:**

                            📁 **En local:** Modifiez le fichier `.streamlit/secrets.toml`:
                            ```toml
                            [api]
                            ANTHROPIC_API_KEY = "votre-clé-ici"
                            ```

                            ☁️ **Sur Streamlit Cloud:** Allez dans Settings > Secrets et ajoutez:
                            ```toml
                            [api]
                            ANTHROPIC_API_KEY = "votre-clé-ici"
                            ```
                            """)
                        else:
                            st.error(f"❌ {error_msg}")
                    else:
                        st.warning("Entrez une clé API")

                st.markdown("---")

                # Modifier le mot de passe admin
                st.subheader("🔒 Sécurité")
                st.caption("Pour modifier le mot de passe admin, éditez `.streamlit/secrets.toml`")

        st.markdown("---")

        # Section Préférences (accessible à tous)
        st.subheader("🎨 Préférences d'affichage")

        col1, col2 = st.columns(2)

        with col1:
            st.selectbox(
                "🌍 Langue des rapports IA",
                options=["Français", "English"],
                index=0,
                help="Langue utilisée pour la génération des rapports",
                disabled=True
            )
            st.caption("🔜 Bientôt disponible")

        with col2:
            st.selectbox(
                "📊 Niveau de détail par défaut",
                options=["Synthétique", "Standard", "Détaillé"],
                index=1,
                help="Niveau de détail pour les explications IA",
                disabled=True
            )
            st.caption("🔜 Bientôt disponible")

        st.markdown("---")

        # Section Données
        st.subheader("💾 Gestion des données")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ Réinitialiser session", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key not in ["anthropic_api_key"]:  # Garder la clé API
                        del st.session_state[key]
                st.success("✅ Session réinitialisée")
                st.rerun()

        with col2:
            if st.button("🧹 Vider cache IA", use_container_width=True):
                st.session_state.ai_explanations = {}
                if "profil_risque_reco" in st.session_state:
                    del st.session_state.profil_risque_reco
                if "rapport_genere" in st.session_state:
                    del st.session_state.rapport_genere
                st.success("✅ Cache IA vidé")

        with col3:
            if st.button("📊 Infos debug", use_container_width=True):
                with st.expander("🔍 État session", expanded=True):
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

        # Section À propos
        st.subheader("ℹ️ À propos")

        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
        ">
            <h4 style="color: white; margin: 0 0 1rem 0;">🎯 Framework Probabiliste DQ</h4>
            <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;">
                <strong>Version :</strong> 1.2.0
            </p>
            <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;">
                <strong>Moteur IA :</strong> Claude Sonnet 4 (Anthropic)
            </p>
            <p style="color: rgba(255,255,255,0.7); margin: 0 0 1rem 0;">
                <strong>Framework :</strong> Streamlit + Plotly
            </p>
            <p style="color: rgba(255,255,255,0.5); margin: 0; font-size: 0.85rem;">
                Outil de démonstration pour l'analyse de qualité des données avec approche probabiliste basée sur les distributions Beta.
            </p>
        </div>
        """, unsafe_allow_html=True)

    idx += 1

    # ========================================================================
    # TAB AIDE - Guide utilisateur intégré
    # ========================================================================

    with tabs[idx]:
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

        # Comparaison DAMA vs Probabiliste
        st.subheader("📊 DAMA classique vs Notre approche")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="background: rgba(235,51,73,0.1); border: 1px solid rgba(235,51,73,0.3); border-radius: 12px; padding: 1rem;">
                <h4 style="color: #eb3349; margin: 0 0 0.5rem 0;">❌ Approche DAMA classique</h4>
                <p style="color: rgba(255,255,255,0.7); margin: 0;">Score unique : "82% de qualité"</p>
                <p style="color: rgba(255,255,255,0.5); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    → Même donnée = même note partout
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="background: rgba(56,239,125,0.1); border: 1px solid rgba(56,239,125,0.3); border-radius: 12px; padding: 1rem;">
                <h4 style="color: #38ef7d; margin: 0 0 0.5rem 0;">✅ Notre approche probabiliste</h4>
                <p style="color: rgba(255,255,255,0.7); margin: 0;">Score contextualisé : "46% Paie, 12% Dashboard"</p>
                <p style="color: rgba(255,255,255,0.5); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
                    → Même donnée = risques différents selon l'usage
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Les 4 dimensions
        st.subheader("🧠 Les 4 dimensions du risque")

        st.markdown("""
        <p style="color: rgba(255,255,255,0.7); margin-bottom: 1rem;">
            Chaque attribut est analysé sur <strong>4 dimensions causales</strong> :
        </p>
        """, unsafe_allow_html=True)

        dims_help = [
            {"code": "DB", "nom": "Structure", "icon": "🗄️", "question": "Le format/type est-il correct ?", "exemple": "VARCHAR au lieu de NUMBER", "color": "#667eea"},
            {"code": "DP", "nom": "Traitements", "icon": "⚙️", "question": "Les ETL ont-ils dégradé la donnée ?", "exemple": "Troncature, encodage cassé", "color": "#764ba2"},
            {"code": "BR", "nom": "Règles métier", "icon": "📋", "question": "La valeur respecte-t-elle les règles ?", "exemple": "Salaire négatif, date future", "color": "#f093fb"},
            {"code": "UP", "nom": "Utilisabilité", "icon": "👁️", "question": "La donnée est-elle exploitable ?", "exemple": "Trop de valeurs manquantes", "color": "#38ef7d"},
        ]

        cols = st.columns(4)
        for i, dim in enumerate(dims_help):
            with cols[i]:
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

        st.markdown("---")

        # Pourquoi les pondérations
        st.subheader("⚖️ Pourquoi les pondérations changent tout")

        st.markdown("""
        <p style="color: rgba(255,255,255,0.7);">
            Le <strong>même attribut</strong> a des risques différents selon l'usage car les pondérations varient :
        </p>
        """, unsafe_allow_html=True)

        # Tableau des pondérations
        st.markdown("""
        | Usage | DB (Structure) | DP (Traitements) | BR (Règles) | UP (Utilisabilité) | Logique |
        |-------|----------------|------------------|-------------|--------------------| --------|
        | **Paie** | 40% | 30% | 20% | 10% | Structure critique (calculs légaux) |
        | **Dashboard** | 10% | 20% | 20% | 50% | Utilisabilité prime (affichage) |
        | **Audit** | 20% | 20% | 40% | 20% | Règles métier critiques (conformité) |
        """)

        st.info("💡 **Résultat** : Un attribut avec P_DB=80% aura un score de 40% pour la Paie mais seulement 19% pour un Dashboard !")

        st.markdown("---")

        # Code couleur
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

        st.markdown("---")

        # Les onglets
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

        # 3 insights clés
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

else:
    # ========================================================================
    # ONGLET ACCUEIL (avant analyse)
    # ========================================================================
    with tabs[0]:  # 🏠 Accueil
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 20px;
            padding: 2.5rem;
            text-align: center;
            margin: 1.5rem 0;
        ">
            <div style="font-size: 3.5rem; margin-bottom: 0.75rem;">📊</div>
            <h2 style="color: white; margin-bottom: 0.75rem;">Bienvenue dans le Framework DQ</h2>
            <p style="color: rgba(255,255,255,0.7); font-size: 1.05rem; max-width: 600px; margin: 0 auto 1rem auto;">
                Analysez la qualité de vos données avec une approche probabiliste basée sur les distributions Beta.
            </p>
        <div style="
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
            margin-top: 1.5rem;
        ">
            <div style="text-align: center;">
                <div style="font-size: 1.75rem;">1️⃣</div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Upload dataset</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.75rem;">2️⃣</div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Sélectionner colonnes</p>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.75rem;">3️⃣</div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Lancer l'analyse</p>
            </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Aperçu rapide des fonctionnalités
        st.markdown("---")
        st.subheader("🚀 Ce que tu vas pouvoir faire")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="background: rgba(102,126,234,0.1); border: 1px solid rgba(102,126,234,0.3); border-radius: 12px; padding: 1rem; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
                <div style="color: white; font-weight: 600;">Analyser</div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">Scores de risque contextualisés par usage</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="background: rgba(118,75,162,0.1); border: 1px solid rgba(118,75,162,0.3); border-radius: 12px; padding: 1rem; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                <div style="color: white; font-weight: 600;">Prioriser</div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">Identifier les urgences à traiter</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="background: rgba(56,239,125,0.1); border: 1px solid rgba(56,239,125,0.3); border-radius: 12px; padding: 1rem; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
                <div style="color: white; font-weight: 600;">Rapporter</div>
                <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem; margin: 0.5rem 0 0 0;">Générer des rapports IA personnalisés</p>
            </div>
            """, unsafe_allow_html=True)

        st.info("💡 **Consulte l'onglet ❓ Aide** pour comprendre la méthodologie en détail")

        # Status API
        st.markdown("---")
        if not st.session_state.get("anthropic_api_key"):
            st.warning("🔑 **Configure ta clé API** dans l'onglet ⚙️ Paramètres pour activer l'assistance IA")
        else:
            st.success("✅ **API configurée** - Toutes les fonctionnalités IA sont actives !")

    # ========================================================================
    # ONGLET DATA CONTRACTS (avant analyse)
    # ========================================================================
    with tabs[1]:  # 📜 Contracts
        if CONTRACTS_OK:
            render_data_contracts_tab()
        else:
            st.header("📜 Data Contracts")
            st.warning("Module Data Contracts non disponible")

    # ========================================================================
    # ONGLET HISTORIQUE (avant analyse)
    # ========================================================================
    with tabs[2]:  # 📜 Historique
        if AUDIT_OK:
            render_audit_tab()
        else:
            st.header("📜 Historique")
            st.warning("Module d'audit non disponible")

    # ========================================================================
    # ONGLET PARAMÈTRES (avant analyse)
    # ========================================================================
    with tabs[3]:  # ⚙️ Paramètres
        st.header("⚙️ Paramètres")

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        ">
            <h3 style="color: white; margin: 0 0 0.5rem 0;">🔧 Configuration de l'application</h3>
            <p style="color: rgba(255,255,255,0.8); margin: 0;">
                Configure ici ta clé API et tes préférences pour l'assistance IA.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Section API Claude
        st.subheader("🔑 API Claude (Anthropic)")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            L'API Claude permet d'activer les fonctionnalités d'**assistance IA** :
            - 💬 Explications contextuelles des résultats
            - 📋 Génération de rapports personnalisés
            - 🎭 Recommandations selon ton profil de risque
            - 🧠 Synthèses intelligentes
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
                    st.success("✅ Clé API valide et enregistrée")
                else:
                    st.error("❌ Format invalide (doit commencer par 'sk-ant-')")
                    st.session_state.anthropic_api_key = ""
            else:
                st.session_state.anthropic_api_key = ""

            st.markdown("---")
            st.markdown("""
            **📌 Comment obtenir une clé API ?**
            1. Crée un compte sur [console.anthropic.com](https://console.anthropic.com)
            2. Va dans **Settings** → **API Keys**
            3. Clique sur **Create Key**
            4. Copie la clé et colle-la ci-dessus
            """)

        with col2:
            has_key = bool(st.session_state.get("anthropic_api_key"))
            status_color = "#38ef7d" if has_key else "#eb3349"
            status_text = "Configurée" if has_key else "Non configurée"
            status_icon = "✅" if has_key else "❌"

            st.markdown(f"""
            <div style="
                background: {status_color}20;
                border: 2px solid {status_color};
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
            ">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">{status_icon}</div>
                <div style="color: {status_color}; font-weight: 700; font-size: 1.2rem;">API {status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("ℹ️ À propos")
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 1.5rem;
        ">
            <h4 style="color: white; margin: 0 0 1rem 0;">🎯 Framework Probabiliste DQ</h4>
            <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;">
                <strong>Version :</strong> 1.2.0
            </p>
            <p style="color: rgba(255,255,255,0.7); margin: 0 0 0.5rem 0;">
                <strong>Moteur IA :</strong> Claude Sonnet 4 (Anthropic)
            </p>
            <p style="color: rgba(255,255,255,0.5); margin: 0; font-size: 0.85rem;">
                Outil de démonstration pour l'analyse de qualité des données avec approche probabiliste.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================================
    # ONGLET AIDE (avant analyse)
    # ========================================================================
    with tabs[4]:  # ❓ Aide
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

        # Comparaison DAMA vs Probabiliste
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
        st.subheader("🧠 Les 4 dimensions du risque")
        dims_help_init = [
            {"code": "DB", "nom": "Structure", "icon": "🗄️", "desc": "Format/type correct ?", "color": "#667eea"},
            {"code": "DP", "nom": "Traitements", "icon": "⚙️", "desc": "ETL ont dégradé ?", "color": "#764ba2"},
            {"code": "BR", "nom": "Règles métier", "icon": "📋", "desc": "Respecte les règles ?", "color": "#f093fb"},
            {"code": "UP", "nom": "Utilisabilité", "icon": "👁️", "desc": "Exploitable ?", "color": "#38ef7d"},
        ]
        cols = st.columns(4)
        for i, dim in enumerate(dims_help_init):
            with cols[i]:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border: 1px solid {dim['color']}40; border-radius: 12px; padding: 0.75rem; text-align: center;">
                    <div style="font-size: 1.5rem;">{dim['icon']}</div>
                    <div style="color: {dim['color']}; font-weight: 600;">{dim['code']} - {dim['nom']}</div>
                    <p style="color: rgba(255,255,255,0.6); font-size: 0.8rem; margin: 0.25rem 0 0 0;">{dim['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🎨 Code couleur des risques")
        cols = st.columns(4)
        colors_init = [
            {"color": "#38ef7d", "label": "< 15%", "status": "Faible"},
            {"color": "#F2C94C", "label": "15-25%", "status": "Modéré"},
            {"color": "#F2994A", "label": "25-40%", "status": "Élevé"},
            {"color": "#eb3349", "label": "> 40%", "status": "Critique"},
        ]
        for i, c in enumerate(colors_init):
            with cols[i]:
                st.markdown(f"""
                <div style="background: {c['color']}20; border: 2px solid {c['color']}; border-radius: 12px; padding: 0.75rem; text-align: center;">
                    <div style="color: {c['color']}; font-size: 1.25rem; font-weight: 700;">{c['label']}</div>
                    <div style="color: white; font-weight: 600;">{c['status']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.info("💡 **Pour commencer** : Upload ton fichier dans la sidebar et lance l'analyse !")

# Footer moderne
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
        Framework Probabiliste DQ • Propulsé par Claude AI
    </p>
</div>
""", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)
t = st.session_state.ai_tokens_used
c1.metric("🤖 Tokens IA", f"{t:,}")
c2.metric("💰 Coût session", f"${(t/1e6)*9:.4f}")
c3.metric("📊 Explications", len(st.session_state.ai_explanations))