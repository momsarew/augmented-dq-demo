"""
Framework Probabiliste DQ - Application Streamlit
Interface web complète pour analyse qualité données

Lancement : streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import sys
import os
from datetime import datetime, timedelta
import time
import json

# Import CSS minimaliste Apple
from streamlit_minimal_css import apply_minimal_css

# Import Anthropic pour LLM
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
import anthropic
import json

# Ajouter path backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import moteur
from backend.engine import (
    analyze_dataset,
    compute_all_beta_vectors,
    elicit_weights_auto,
    compute_risk_scores,
    get_top_priorities,
    simulate_lineage,
    compare_dama_vs_probabiliste
)

# Import système détection anomalies
from streamlit_anomaly_detection import render_anomaly_detection_tab


# ============================================================================
# CONFIGURATION PAGE
# ============================================================================

st.set_page_config(
    page_title="Framework Probabiliste DQ",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Appliquer CSS minimaliste
apply_minimal_css()



# ============================================================================
# SESSION STATE (pour conserver données entre interactions)
# ============================================================================

if 'df' not in st.session_state:
    st.session_state.df = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_risk_color(score: float) -> str:
    """Retourne couleur selon score risque"""
    if score >= 0.40:
        return "#ff0000"  # Rouge
    elif score >= 0.25:
        return "#ff9900"  # Orange
    elif score >= 0.15:
        return "#ffcc00"  # Jaune
    elif score >= 0.10:
        return "#90ee90"  # Vert clair
    else:
        return "#00ff00"  # Vert


def call_claude_api(messages: List[Dict], system_prompt: str = None) -> str:
    """
    Appelle Claude API pour dialogue élicitation
    
    Args:
        messages: Historique conversation [{"role": "user/assistant", "content": "..."}]
        system_prompt: Prompt système optionnel
    
    Returns:
        Réponse de Claude
    """
    try:
        # Vérifier si clé API configurée
        api_key = st.session_state.get('claude_api_key', None)
        
        if not api_key:
            return """⚠️ **Clé API Claude non configurée**
            
Pour activer le dialogue IA réel, configure ta clé API dans la sidebar :
1. Va sur https://console.anthropic.com/
2. Crée une clé API
3. Colle-la dans le champ "Clé API Claude" (sidebar)

**En attendant, voici une réponse simulée** :
✅ Noté ! J'augmente **w_DB à 40%** pour la Paie.

Les données structurelles (VARCHAR au lieu DECIMAL) sont effectivement critiques pour la conformité réglementaire de la paie.

Quelle est la **deuxième dimension la plus importante** pour ce cas d'usage ?"""
        
        # Import dynamique (seulement si clé présente)
        try:
            import anthropic
        except ImportError:
            return """⚠️ **Module Anthropic non installé**
            
Pour installer : `pip install anthropic`

Réponse simulée en attendant..."""
        
        # Appeler API Claude
        client = anthropic.Anthropic(api_key=api_key)
        
        # Prompt système par défaut
        if not system_prompt:
            system_prompt = """Tu es un expert en Data Quality et en sciences de la décision. 
Tu aides à éliciter les pondérations AHP pour un framework probabiliste de qualité des données.

Tu poses des questions progressives pour comprendre l'importance relative des 4 dimensions :
- [DB] Database : Contraintes structurelles (types, nullable, clés)
- [DP] Data Processing : Erreurs transformations ETL
- [BR] Business Rules : Violations règles métier
- [UP] Usage-fit : Inadéquation contextuelle

Ton style :
- Questions courtes et ciblées
- Exemples concrets
- Validation des choix utilisateur
- Propositions de valeurs Beta si pertinent

Contexte actuel : Élicitation pour usage "Paie réglementaire" (conformité légale stricte)."""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        
        # Extraire texte réponse
        return response.content[0].text
        
    except Exception as e:
        return f"""⚠️ **Erreur API Claude** : {str(e)}

Vérifie que :
- Ta clé API est valide
- Tu as des crédits disponibles
- Ta connexion internet fonctionne

Réponse simulée en attendant..."""


def get_risk_color(score: float) -> str:
    """Retourne couleur selon score risque"""
    if score >= 0.40:
        return "#ff0000"  # Rouge
    elif score >= 0.25:
        return "#ff9900"  # Orange
    elif score >= 0.15:
        return "#ffcc00"  # Jaune
    elif score >= 0.10:
        return "#90ee90"  # Vert clair
    else:
        return "#00ff00"  # Vert


def create_vector_chart(vector_4d: Dict) -> go.Figure:
    """Crée graphique barres vecteur 4D"""
    dimensions = ['DB', 'DP', 'BR', 'UP']
    values = [
        vector_4d.get('P_DB', 0) * 100,
        vector_4d.get('P_DP', 0) * 100,
        vector_4d.get('P_BR', 0) * 100,
        vector_4d.get('P_UP', 0) * 100
    ]
    
    colors = [get_risk_color(v/100) for v in values]
    
    fig = go.Figure(data=[
        go.Bar(
            x=dimensions,
            y=values,
            marker=dict(color=colors),
            text=[f"{v:.1f}%" for v in values],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Vecteur Qualité 4D",
        xaxis_title="Dimensions",
        yaxis_title="Taux erreur (%)",
        height=400,
        template="plotly_dark"
    )
    
    return fig


def export_to_excel(results: Dict, output_path: str = "resultats_framework_dq.xlsx"):
    """
    Exporte résultats complets vers Excel multi-onglets
    """
    from datetime import datetime
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    
    # Ajouter timestamp au nom fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"resultats_framework_dq_{timestamp}.xlsx"
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        
        # ====================================================================
        # ONGLET 1 : VECTEURS 4D
        # ====================================================================
        vecteurs_data = []
        for attr, vector in results['vecteurs_4d'].items():
            vecteurs_data.append({
                'Attribut': attr,
                'P_DB': vector.get('P_DB', 0),
                'alpha_DB': vector.get('alpha_DB', 0),
                'beta_DB': vector.get('beta_DB', 0),
                'std_DB': vector.get('std_DB', 0),
                'ci_lower_DB': vector.get('ci_lower_DB', 0),
                'ci_upper_DB': vector.get('ci_upper_DB', 0),
                'P_DP': vector.get('P_DP', 0),
                'alpha_DP': vector.get('alpha_DP', 0),
                'beta_DP': vector.get('beta_DP', 0),
                'std_DP': vector.get('std_DP', 0),
                'ci_lower_DP': vector.get('ci_lower_DP', 0),
                'ci_upper_DP': vector.get('ci_upper_DP', 0),
                'P_BR': vector.get('P_BR', 0),
                'alpha_BR': vector.get('alpha_BR', 0),
                'beta_BR': vector.get('beta_BR', 0),
                'std_BR': vector.get('std_BR', 0),
                'ci_lower_BR': vector.get('ci_lower_BR', 0),
                'ci_upper_BR': vector.get('ci_upper_BR', 0),
                'P_UP': vector.get('P_UP', 0),
                'alpha_UP': vector.get('alpha_UP', 0),
                'beta_UP': vector.get('beta_UP', 0),
                'std_UP': vector.get('std_UP', 0),
                'ci_lower_UP': vector.get('ci_lower_UP', 0),
                'ci_upper_UP': vector.get('ci_upper_UP', 0)
            })
        
        df_vecteurs = pd.DataFrame(vecteurs_data)
        df_vecteurs.to_excel(writer, sheet_name='Vecteurs_4D', index=False)
        
        # ====================================================================
        # ONGLET 2 : SCORES RISQUE
        # ====================================================================
        scores_data = []
        for key, score in results['scores'].items():
            parts = key.rsplit('_', 1)
            attribut = parts[0] if len(parts) > 1 else key
            usage = parts[1] if len(parts) > 1 else "Unknown"
            
            scores_data.append({
                'Attribut': attribut,
                'Usage': usage,
                'Score_Risque': score,
                'Score_Pourcent': f"{score:.1%}",
                'Criticité': 'CRITIQUE' if score > 0.4 else 'ÉLEVÉ' if score > 0.25 else 'MOYEN' if score > 0.15 else 'ACCEPTABLE'
            })
        
        df_scores = pd.DataFrame(scores_data)
        df_scores_pivot = df_scores.pivot(index='Attribut', columns='Usage', values='Score_Risque')
        df_scores_pivot.to_excel(writer, sheet_name='Scores_Risque')
        
        # ====================================================================
        # ONGLET 3 : PONDÉRATIONS USAGES
        # ====================================================================
        weights_data = []
        for usage_name, weights in results['weights'].items():
            weights_data.append({
                'Usage': usage_name,
                'w_DB': weights.get('w_DB', 0),
                'w_DP': weights.get('w_DP', 0),
                'w_BR': weights.get('w_BR', 0),
                'w_UP': weights.get('w_UP', 0),
                'Rationale': weights.get('rationale', '')
            })
        
        df_weights = pd.DataFrame(weights_data)
        df_weights.to_excel(writer, sheet_name='Pondérations_AHP', index=False)
        
        # ====================================================================
        # ONGLET 4 : PRIORITÉS ACTIONS
        # ====================================================================
        priorities_data = []
        for i, priority in enumerate(results['top_priorities'], 1):
            priorities_data.append({
                'Rang': i,
                'Attribut': priority['attribut'],
                'Usage': priority['usage'],
                'Score_Risque': priority['score'],
                'Score_Pourcent': f"{priority['score']:.1%}",
                'Sévérité': priority['severite'],
                'Enregistrements_Affectés': priority['records_affected'],
                'Impact_Mensuel_€': priority['impact_mensuel'],
                'Action_Principale': priority['actions'][0] if priority.get('actions') else ''
            })
        
        df_priorities = pd.DataFrame(priorities_data)
        df_priorities.to_excel(writer, sheet_name='Priorités_Actions', index=False)
        
        # ====================================================================
        # ONGLET 5 : LINEAGE (si disponible)
        # ====================================================================
        if results.get('lineage'):
            lineage = results['lineage']
            lineage_data = []
            
            for step in lineage['history']:
                lineage_data.append({
                    'Étape': step['etape'],
                    'P_DB': step['P_DB'],
                    'P_DP': step['P_DP'],
                    'P_BR': step['P_BR'],
                    'P_UP': step['P_UP']
                })
            
            df_lineage = pd.DataFrame(lineage_data)
            df_lineage.to_excel(writer, sheet_name='Lineage_Propagation', index=False)
            
            # Métriques lineage
            lineage_summary = pd.DataFrame([{
                'Risque_Source': lineage['risk_source'],
                'Risque_Final': lineage['risk_final'],
                'Delta_Absolu': lineage['delta']['delta_absolute'],
                'Delta_Relatif': lineage['delta']['delta_relative'],
                'Interprétation': lineage['delta']['interpretation']
            }])
            lineage_summary.to_excel(writer, sheet_name='Lineage_Summary', index=False)
        
        # ====================================================================
        # ONGLET 6 : COMPARAISON DAMA
        # ====================================================================
        dama_data = []
        for attr, dama_score in results['comparaison']['dama_scores'].items():
            dama_data.append({
                'Attribut': attr,
                'Score_DAMA_Global': dama_score['score_global'],
                'DAMA_Completeness': dama_score.get('completeness', 0),
                'DAMA_Consistency': dama_score.get('consistency', 0),
                'DAMA_Accuracy': dama_score.get('accuracy', 0),
                'DAMA_Validity': dama_score.get('validity', 0)
            })
        
        df_dama = pd.DataFrame(dama_data)
        df_dama.to_excel(writer, sheet_name='Comparaison_DAMA', index=False)
        
        # Problèmes masqués
        if results['comparaison'].get('problemes_masques'):
            problemes_data = []
            for pb in results['comparaison']['problemes_masques']:
                problemes_data.append({
                    'Attribut': pb['attribut'],
                    'Type_Problème': pb['type'],
                    'Explication': pb['explication']
                })
            
            df_problemes = pd.DataFrame(problemes_data)
            df_problemes.to_excel(writer, sheet_name='Problèmes_Masqués_DAMA', index=False)
    
    return output_path


def export_to_csv(results: Dict, output_dir: str = "."):
    """
    Exporte résultats en plusieurs fichiers CSV
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files_created = []
    
    # Vecteurs 4D
    vecteurs_data = []
    for attr, vector in results['vecteurs_4d'].items():
        vecteurs_data.append({
            'Attribut': attr,
            **{k: v for k, v in vector.items()}
        })
    
    df_vecteurs = pd.DataFrame(vecteurs_data)
    file_vecteurs = f"{output_dir}/vecteurs_4d_{timestamp}.csv"
    df_vecteurs.to_csv(file_vecteurs, index=False)
    files_created.append(file_vecteurs)
    
    # Scores
    scores_data = []
    for key, score in results['scores'].items():
        parts = key.rsplit('_', 1)
        scores_data.append({
            'Attribut': parts[0] if len(parts) > 1 else key,
            'Usage': parts[1] if len(parts) > 1 else "Unknown",
            'Score_Risque': score
        })
    
    df_scores = pd.DataFrame(scores_data)
    file_scores = f"{output_dir}/scores_risque_{timestamp}.csv"
    df_scores.to_csv(file_scores, index=False)
    files_created.append(file_scores)
    
    # Priorités
    df_priorities = pd.DataFrame(results['top_priorities'])
    file_priorities = f"{output_dir}/priorites_{timestamp}.csv"
    df_priorities.to_csv(file_priorities, index=False)
    files_created.append(file_priorities)
    
    return files_created


def generate_ai_comment(context: str, data: Dict, api_key: str) -> str:
    """
    Génère un commentaire IA contextualisé avec Claude
    
    Args:
        context: Type de section (heatmap, vector, priority, lineage, dama)
        data: Données à commenter
        api_key: Clé API Anthropic
    
    Returns:
        Commentaire IA en texte
    """
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construire prompt selon contexte
        prompts = {
            "heatmap": f"""Tu es un expert Data Quality. Analyse cette matrice de scores risque et fournis un commentaire de 3-4 phrases maximum.

Données: {json.dumps(data, indent=2)}

Concentre-toi sur:
1. Les patterns principaux (attributs/usages les plus risqués)
2. Les différences de scores selon contexte (même attribut, usages différents)
3. Une recommandation prioritaire

Ton style: Direct, pédagogique, actionnable. Utilise "Je remarque que...", "Cela signifie...", "Je recommande...".""",

            "vector": f"""Tu es un expert Data Quality. Commente ce vecteur 4D Beta et explique sa signification en 3-4 phrases maximum.

Attribut: {data.get('attribut', 'Unknown')}
Vecteurs:
- P_DB = {data.get('P_DB', 0):.1%} (Database)
- P_DP = {data.get('P_DP', 0):.1%} (Data Processing)  
- P_BR = {data.get('P_BR', 0):.1%} (Business Rules)
- P_UP = {data.get('P_UP', 0):.1%} (Usage-fit)

Explique:
1. Quelle dimension domine et pourquoi
2. Ce que révèle la distribution Beta sous-jacente (confiance)
3. Implication opérationnelle concrète

Style: Technique mais accessible, pédagogique.""",

            "priority": f"""Tu es un expert Data Quality. Commente cette priorité d'action en 3-4 phrases maximum.

Priorité: {data.get('attribut', 'Unknown')} × {data.get('usage', 'Unknown')}
Score risque: {data.get('score', 0):.1%}
Sévérité: {data.get('severite', 'Unknown')}
Impact: {data.get('records_affected', 0)} enregistrements, {data.get('impact_mensuel', 0):,}€/mois

Fournis:
1. Pourquoi ce combo attribut×usage est critique
2. Recommandation d'action immédiate concrète
3. Estimation ROI si correction

Style: Consultant senior, actionnable, chiffré.""",

            "lineage": f"""Tu es un expert Data Quality. Commente cette propagation de risque en 3-4 phrases maximum.

Propagation:
- Risque initial: {data.get('risk_source', 0):.1%}
- Risque final: {data.get('risk_final', 0):.1%}
- Delta: {data.get('delta_absolute', 0):.1%} points
- Étapes pipeline: {len(data.get('history', []))}

Explique:
1. Comment le risque s'est aggravé dans le pipeline
2. Quelle étape a le plus dégradé (si visible)
3. Gain détection proactive (9h vs 3 semaines)

Style: Analyse forensique, factuelle, impactante.""",

            "dama": f"""Tu es un expert Data Quality. Compare les approches DAMA vs Probabiliste en 3-4 phrases maximum.

Comparaison:
- Score DAMA moyen: {data.get('dama_avg', 0):.1%}
- Problèmes masqués: {data.get('masked_count', 0)}
- Gains méthodologiques: {len(data.get('gains', []))}

Synthétise:
1. Pourquoi DAMA masque certains problèmes critiques
2. L'avantage principal du framework probabiliste
3. Impact business concret (-70% faux positifs, ROI 8-18×)

Style: Comparatif mais objectif, factuel, business-oriented."""
        }
        
        prompt = prompts.get(context, prompts["heatmap"])
        
        # Appel API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system="Tu es un expert Data Quality qui commente des analyses avec un style direct, pédagogique et actionnable. Toujours 3-4 phrases maximum, sans jargon inutile.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"⚠️ Erreur génération commentaire : {str(e)}"


def create_heatmap(scores: Dict) -> go.Figure:
    """Crée heatmap scores [Attribut × Usage]"""
    # Parser scores en matrice
    attributs = set()
    usages = set()
    
    for key in scores.keys():
        parts = key.rsplit('_', 1)
        if len(parts) == 2:
            attributs.add(parts[0])
            usages.add(parts[1])
    
    attributs = sorted(list(attributs))
    usages = sorted(list(usages))
    
    # Construire matrice
    matrix = []
    for attr in attributs:
        row = []
        for usage in usages:
            key = f"{attr}_{usage}"
            row.append(scores.get(key, 0) * 100)
        matrix.append(row)
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=usages,
        y=attributs,
        colorscale='RdYlGn_r',
        text=[[f"{v:.1f}%" for v in row] for row in matrix],
        texttemplate='%{text}',
        textfont={"size": 12},
        colorbar=dict(title="Risque (%)")
    ))
    
    fig.update_layout(
        title="Matrice Scores Risque [Attribut × Usage]",
        height=400,
        template="plotly_dark"
    )
    
    return fig


# ============================================================================
# HEADER
# ============================================================================


# ============================================================================
# TOGGLE THEME
# ============================================================================

col_theme, col_main = st.columns([1, 11])
with col_theme:
    theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
    if st.button(theme_icon, key="theme_toggle", help="Changer thème"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()

st.title("📊 Framework Probabiliste DQ")

# Descriptif projet
with st.expander("📋 À propos", expanded=False):
    st.markdown("""
    Framework probabiliste de Data Quality basé sur des distributions Beta.

    **Dimensions** : DB (Database), DP (Data Processing), BR (Business Rules), UP (Usage-fit)

    **Contact** : Thierno DIAW
    """)

st.markdown("---")


# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Configuration API Claude
    st.subheader("🔑 API Claude (Anthropic)")
    
    # Tenter de charger clé API depuis Streamlit secrets (Cloud) ou variable env
    api_key_default = ""
    try:
        # Streamlit Cloud secrets
        api_key_default = st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        # Variable environnement locale
        api_key_default = os.getenv("ANTHROPIC_API_KEY", "")
    
    api_key_input = st.text_input(
        "Clé API Claude",
        type="password",
        value=api_key_default,
        help="Nécessaire pour le dialogue IA dans l'onglet Élicitation. Obtenir une clé : https://console.anthropic.com/",
        placeholder="sk-ant-api03-..."
    )
    
    if api_key_input:
        st.session_state.anthropic_api_key = api_key_input
        st.success("✅ Clé API configurée")
    else:
        if 'anthropic_api_key' not in st.session_state:
            st.warning("⚠️ Onglet Élicitation IA nécessite une clé API")
            with st.expander("💡 Comment obtenir une clé ?"):
                st.markdown("Obtenir une clé API sur https://console.anthropic.com/")
    
    st.markdown("---")
    
    # Upload fichier
    st.subheader("1️⃣ Upload Ton Dataset")
    uploaded_file = st.file_uploader(
        "📁 Choisis ton fichier CSV ou Excel",
        type=['csv', 'xlsx', 'xls'],
        help="Ton dataset à analyser (tous secteurs : RH, Finance, Marketing, Supply Chain, etc.)"
    )
    
    # Si fichier uploadé
    if uploaded_file:
        # Charger données
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.success(f"✅ {uploaded_file.name} chargé ({len(st.session_state.df)} lignes)")
        
        # Afficher preview
        with st.expander("👁️ Preview données"):
            st.dataframe(st.session_state.df.head(10))
        
        # Sélection colonnes
        st.subheader("2️⃣ Colonnes à analyser")
        all_columns = st.session_state.df.columns.tolist()
        
        # Suggestions automatiques
        suggested = [col for col in all_columns if any(
            kw in col.lower() for kw in ['anciennete', 'date', 'level', 'salaire', 'prime', 'matricule']
        )]
        
        selected_columns = st.multiselect(
            "Sélectionner colonnes",
            options=all_columns,
            default=suggested if suggested else all_columns[:3],
            help="Colonnes critiques pour analyse qualité"
        )
        
        # Configuration usages
        st.subheader("3️⃣ Usages métier")
        
        # Usages presets
        preset_usage_types = {
            "Paie réglementaire": "paie_reglementaire",
            "Reporting Social (CSE)": "reporting_social",
            "Dashboard Opérationnel": "dashboard_operationnel",
            "Audit Conformité": "audit_conformite",
            "Analytics Décisionnel": "analytics_decisional"
        }
        
        # Stocker usages personnalisés dans session state
        if 'custom_usages' not in st.session_state:
            st.session_state.custom_usages = {}
        
        # Combiner presets + custom
        all_usage_types = {**preset_usage_types, **st.session_state.custom_usages}
        
        # Bouton ajouter usage personnalisé
        col_add1, col_add2 = st.columns([3, 1])
        with col_add1:
            st.markdown("**Usages disponibles**")
        with col_add2:
            add_usage = st.button("➕ Ajouter", use_container_width=True, help="Créer un usage métier personnalisé")
        
        # Formulaire ajout usage
        if add_usage or 'show_add_form' in st.session_state and st.session_state.show_add_form:
            st.session_state.show_add_form = True
            
            with st.expander("➕ Nouvel usage personnalisé", expanded=True):
                with st.form("add_custom_usage_form"):
                    st.markdown("### Créer un usage métier")
                    
                    usage_name = st.text_input(
                        "Nom de l'usage",
                        placeholder="Ex: Reporting URSSAF, Pilotage RH, Audit CNIL...",
                        help="Nom descriptif de votre usage métier"
                    )
                    
                    st.markdown("#### Pondérations AHP")
                    st.caption("Définir l'importance de chaque dimension (total = 100%)")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        w_db_new = st.slider("DB", 0, 100, 25, 5, key="new_db", help="Database: Contraintes structurelles")
                    with col2:
                        w_dp_new = st.slider("DP", 0, 100, 25, 5, key="new_dp", help="Data Processing: Transformations ETL")
                    with col3:
                        w_br_new = st.slider("BR", 0, 100, 25, 5, key="new_br", help="Business Rules: Règles métier")
                    with col4:
                        w_up_new = st.slider("UP", 0, 100, 25, 5, key="new_up", help="Usage-fit: Adéquation contextuelle")
                    
                    total_new = w_db_new + w_dp_new + w_br_new + w_up_new
                    
                    if total_new == 100:
                        st.success(f"✅ Somme = {total_new}%")
                    else:
                        st.error(f"⚠️ Somme = {total_new}% (doit être 100%)")
                    
                    rationale = st.text_area(
                        "Justification (optionnel)",
                        placeholder="Ex: Priorité conformité légale, peu de flexibilité contextuelle...",
                        help="Expliquer pourquoi ces pondérations"
                    )
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        submitted = st.form_submit_button("✅ Créer usage", type="primary", use_container_width=True)
                    
                    with col_btn2:
                        cancelled = st.form_submit_button("❌ Annuler", use_container_width=True)
                    
                    if submitted:
                        if not usage_name:
                            st.error("⚠️ Le nom de l'usage est obligatoire")
                        elif usage_name in all_usage_types:
                            st.error(f"⚠️ Un usage '{usage_name}' existe déjà")
                        elif total_new != 100:
                            st.error("⚠️ La somme des pondérations doit être 100%")
                        else:
                            # Ajouter usage personnalisé
                            st.session_state.custom_usages[usage_name] = {
                                'type': 'custom',
                                'w_DB': w_db_new / 100,
                                'w_DP': w_dp_new / 100,
                                'w_BR': w_br_new / 100,
                                'w_UP': w_up_new / 100,
                                'rationale': rationale if rationale else f"Usage personnalisé : {usage_name}"
                            }
                            st.session_state.show_add_form = False
                            st.success(f"✅ Usage '{usage_name}' créé avec succès !")
                            st.rerun()
                    
                    if cancelled:
                        st.session_state.show_add_form = False
                        st.rerun()
        
        # Sélection usages (presets + custom)
        selected_usages = st.multiselect(
            "Sélectionner usages",
            options=list(all_usage_types.keys()),
            default=[k for k in list(all_usage_types.keys())[:2] if k in all_usage_types],
            help="Contextes métier pour scoring risque"
        )
        
        # Afficher usages personnalisés avec option suppression
        if st.session_state.custom_usages:
            with st.expander("🗑️ Gérer usages personnalisés", expanded=False):
                for custom_name, custom_data in list(st.session_state.custom_usages.items()):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{custom_name}**")
                        st.caption(f"DB={custom_data['w_DB']:.0%}, DP={custom_data['w_DP']:.0%}, BR={custom_data['w_BR']:.0%}, UP={custom_data['w_UP']:.0%}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{custom_name}", help=f"Supprimer {custom_name}"):
                            del st.session_state.custom_usages[custom_name]
                            # Retirer de sélection si présent
                            if custom_name in selected_usages:
                                selected_usages.remove(custom_name)
                            st.rerun()
                    st.markdown("---")
        
        # Mode édition pondérations
        if selected_usages:
            from backend.engine.ahp_elicitor import AHPElicitor
            elicitor = AHPElicitor()
            
            # Stocker pondérations personnalisées dans session state
            if 'custom_weights' not in st.session_state:
                st.session_state.custom_weights = {}
            
            st.markdown("---")
            st.markdown("### ⚙️ Configuration pondérations")
            
            mode = st.radio(
                "Mode configuration",
                ["📊 Utiliser valeurs par défaut", "✏️ Ajuster finement les pondérations"],
                help="Par défaut = valeurs expertes, Ajuster = modifier manuellement"
            )
            
            if mode == "✏️ Ajuster finement les pondérations":
                st.info("💡 Ajuste les pondérations avec les sliders. La somme doit faire 100%.")
                
                for usage_name in selected_usages:
                    # Récupérer valeurs par défaut
                    if usage_name not in st.session_state.custom_weights:
                        # Si preset, charger preset
                        if usage_name in preset_usage_types:
                            usage_type = preset_usage_types[usage_name]
                            preset = elicitor.get_weights_preset(usage_type)
                            st.session_state.custom_weights[usage_name] = {
                                'w_DB': preset['w_DB'],
                                'w_DP': preset['w_DP'],
                                'w_BR': preset['w_BR'],
                                'w_UP': preset['w_UP']
                            }
                        # Si custom, utiliser valeurs custom
                        elif usage_name in st.session_state.custom_usages:
                            custom_data = st.session_state.custom_usages[usage_name]
                            st.session_state.custom_weights[usage_name] = {
                                'w_DB': custom_data['w_DB'],
                                'w_DP': custom_data['w_DP'],
                                'w_BR': custom_data['w_BR'],
                                'w_UP': custom_data['w_UP']
                            }
                    
                    with st.expander(f"⚙️ {usage_name}", expanded=True):
                        # Indicateur si custom
                        if usage_name in st.session_state.custom_usages:
                            st.badge("Custom", icon="✨")
                        
                        st.markdown(f"**{usage_name}**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            w_db = st.slider(
                                "DB",
                                min_value=0,
                                max_value=100,
                                value=int(st.session_state.custom_weights[usage_name]['w_DB'] * 100),
                                step=5,
                                key=f"slider_db_{usage_name}",
                                help="Database: Contraintes structurelles"
                            )
                        
                        with col2:
                            w_dp = st.slider(
                                "DP",
                                min_value=0,
                                max_value=100,
                                value=int(st.session_state.custom_weights[usage_name]['w_DP'] * 100),
                                step=5,
                                key=f"slider_dp_{usage_name}",
                                help="Data Processing: Transformations ETL"
                            )
                        
                        with col3:
                            w_br = st.slider(
                                "BR",
                                min_value=0,
                                max_value=100,
                                value=int(st.session_state.custom_weights[usage_name]['w_BR'] * 100),
                                step=5,
                                key=f"slider_br_{usage_name}",
                                help="Business Rules: Règles métier"
                            )
                        
                        with col4:
                            w_up = st.slider(
                                "UP",
                                min_value=0,
                                max_value=100,
                                value=int(st.session_state.custom_weights[usage_name]['w_UP'] * 100),
                                step=5,
                                key=f"slider_up_{usage_name}",
                                help="Usage-fit: Adéquation contextuelle"
                            )
                        
                        # Calculer somme
                        total = w_db + w_dp + w_br + w_up
                        
                        # Afficher somme avec couleur
                        if total == 100:
                            st.success(f"✅ Somme = {total}% (OK)")
                        else:
                            st.error(f"⚠️ Somme = {total}% (doit être 100%)")
                        
                        # Normaliser automatiquement si demandé
                        if total != 100:
                            if st.button(f"🔄 Normaliser automatiquement", key=f"normalize_{usage_name}"):
                                # Normaliser à 100%
                                if total > 0:
                                    st.session_state.custom_weights[usage_name] = {
                                        'w_DB': round(w_db / total, 2),
                                        'w_DP': round(w_dp / total, 2),
                                        'w_BR': round(w_br / total, 2),
                                        'w_UP': round(w_up / total, 2)
                                    }
                                    st.rerun()
                        else:
                            # Sauvegarder valeurs
                            st.session_state.custom_weights[usage_name] = {
                                'w_DB': w_db / 100,
                                'w_DP': w_dp / 100,
                                'w_BR': w_br / 100,
                                'w_UP': w_up / 100
                            }
                        
                        # Bouton reset
                        if st.button(f"🔄 Réinitialiser", key=f"reset_{usage_name}"):
                            if usage_name in preset_usage_types:
                                usage_type = preset_usage_types[usage_name]
                                preset = elicitor.get_weights_preset(usage_type)
                                st.session_state.custom_weights[usage_name] = {
                                    'w_DB': preset['w_DB'],
                                    'w_DP': preset['w_DP'],
                                    'w_BR': preset['w_BR'],
                                    'w_UP': preset['w_UP']
                                }
                            elif usage_name in st.session_state.custom_usages:
                                custom_data = st.session_state.custom_usages[usage_name]
                                st.session_state.custom_weights[usage_name] = {
                                    'w_DB': custom_data['w_DB'],
                                    'w_DP': custom_data['w_DP'],
                                    'w_BR': custom_data['w_BR'],
                                    'w_UP': custom_data['w_UP']
                                }
                            st.rerun()
            
            else:
                # Mode par défaut : afficher juste les valeurs
                with st.expander("📊 Voir pondérations (valeurs par défaut)", expanded=False):
                    for usage_name in selected_usages:
                        # Charger valeurs par défaut
                        if usage_name in preset_usage_types:
                            usage_type = preset_usage_types[usage_name]
                            weights = elicitor.get_weights_preset(usage_type)
                        elif usage_name in st.session_state.custom_usages:
                            weights = st.session_state.custom_usages[usage_name]
                        else:
                            continue
                        
                        st.markdown(f"**{usage_name}**")
                        if usage_name in st.session_state.custom_usages:
                            st.caption("✨ Usage personnalisé")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("DB", f"{weights['w_DB']:.0%}")
                        col2.metric("DP", f"{weights['w_DP']:.0%}")
                        col3.metric("BR", f"{weights['w_BR']:.0%}")
                        col4.metric("UP", f"{weights['w_UP']:.0%}")
                        st.caption(weights.get('rationale', ''))
                        st.markdown("---")
        
        # Bouton ANALYSER
        st.markdown("---")
        if st.button("🚀 LANCER ANALYSE", type="primary", use_container_width=True):
            if not selected_columns:
                st.error("⚠️ Sélectionne au moins une colonne !")
            elif not selected_usages:
                st.error("⚠️ Sélectionne au moins un usage !")
            else:
                # LANCER ANALYSE
                with st.spinner("⏳ Analyse en cours..."):
                    try:
                        # Préparer config usages
                        usages = []
                        for name in selected_usages:
                            # Utiliser valeurs custom si c'est un usage custom
                            if name in st.session_state.custom_usages:
                                usages.append({
                                    "nom": name,
                                    "type": "custom",
                                    "criticite": "MEDIUM"
                                })
                            else:
                                usages.append({
                                    "nom": name.split('(')[0].strip(),
                                    "type": all_usage_types[name],
                                    "criticite": "HIGH" if "Paie" in name else "MEDIUM"
                                })
                        
                        # 1. Stats exploratoires
                        stats = analyze_dataset(st.session_state.df, selected_columns)
                        
                        # 2. Vecteurs 4D
                        vecteurs_4d = compute_all_beta_vectors(st.session_state.df, selected_columns, stats)
                        
                        # 3. Pondérations
                        # Si mode personnalisé ET poids valides, utiliser custom, sinon valeurs par défaut
                        if mode == "✏️ Ajuster finement les pondérations" and st.session_state.custom_weights:
                            # Vérifier que tous les usages ont des poids valides
                            weights = {}
                            all_valid = True
                            
                            for usage_name in selected_usages:
                                if usage_name in st.session_state.custom_weights:
                                    custom = st.session_state.custom_weights[usage_name]
                                    total = sum(custom.values())
                                    
                                    if abs(total - 1.0) < 0.01:  # Tolérance 1%
                                        # Utiliser nom nettoyé
                                        clean_name = usage_name.split('(')[0].strip() if '(' in usage_name else usage_name
                                        weights[clean_name] = {
                                            'w_DB': custom['w_DB'],
                                            'w_DP': custom['w_DP'],
                                            'w_BR': custom['w_BR'],
                                            'w_UP': custom['w_UP'],
                                            'rationale': 'Pondérations ajustées manuellement'
                                        }
                                    else:
                                        all_valid = False
                                        st.error(f"⚠️ {usage_name}: somme = {total:.0%} (doit être 100%)")
                            
                            if not all_valid:
                                st.stop()
                        else:
                            # Utiliser valeurs par défaut
                            weights = {}
                            for usage in usages:
                                usage_name = usage['nom']
                                
                                # Si usage custom, utiliser ses valeurs
                                if usage_name in st.session_state.custom_usages:
                                    custom_data = st.session_state.custom_usages[usage_name]
                                    weights[usage_name] = {
                                        'w_DB': custom_data['w_DB'],
                                        'w_DP': custom_data['w_DP'],
                                        'w_BR': custom_data['w_BR'],
                                        'w_UP': custom_data['w_UP'],
                                        'rationale': custom_data.get('rationale', 'Usage personnalisé')
                                    }
                                # Sinon utiliser preset
                                else:
                                    preset_weights = elicit_weights_auto([usage], vecteurs_4d)
                                    weights.update(preset_weights)
                        
                        # 4. Scores risque
                        scores = compute_risk_scores(vecteurs_4d, weights, usages)
                        
                        # 5. Top priorités
                        top_priorities = get_top_priorities(scores, top_n=5)
                        
                        # 6. Lineage (premier attribut/usage)
                        lineage = None
                        if len(selected_columns) > 0 and len(usages) > 0:
                            first_attr = selected_columns[0]
                            first_usage_name = usages[0]['nom']
                            if first_attr in vecteurs_4d and first_usage_name in weights:
                                lineage = simulate_lineage(vecteurs_4d[first_attr], weights[first_usage_name])
                        
                        # 7. Comparaison DAMA
                        comparaison = compare_dama_vs_probabiliste(
                            st.session_state.df,
                            selected_columns,
                            scores,
                            vecteurs_4d
                        )
                        
                        # Stocker résultats
                        st.session_state.results = {
                            'stats': stats,
                            'vecteurs_4d': vecteurs_4d,
                            'weights': weights,
                            'scores': scores,
                            'top_priorities': top_priorities,
                            'lineage': lineage,
                            'comparaison': comparaison
                        }
                        
                        st.session_state.analysis_done = True
                        st.success("✅ Analyse terminée !")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur analyse : {str(e)}")
                        st.exception(e)


# ============================================================================
# MAIN - AFFICHAGE RÉSULTATS
# ============================================================================

if st.session_state.analysis_done and st.session_state.results:
    results = st.session_state.results
    
    # ONGLETS - SCAN EN PREMIER !
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "🔍 Scan Anomalies",  # ← NOUVEAU 1ER !
        "📊 Dashboard",
        "🎯 Vecteurs 4D",
        "⚠️ Priorités",
        "🔄 Lineage",
        "📈 Comparaison DAMA",
        "💬 Élicitation IA",
        "🔔 Surveillance",
        "📋 Restitution Adaptative"
    ])
    
    # ========================================================================
    # TAB 1 : SCAN ANOMALIES (NOUVEAU PREMIER ONGLET)
    # ========================================================================
    with tab1:
        render_anomaly_detection_tab()
    
    # ========================================================================
    # TAB 2 : DASHBOARD (ancien tab1)
    # ========================================================================
    with tab3:
        st.header("📊 Dashboard Qualité")
        
        # Boutons Export en haut
        col_export1, col_export2, col_export3 = st.columns([2, 2, 4])
        
        with col_export1:
            if st.button("📥 Export Excel", type="primary", use_container_width=True):
                try:
                    output_file = export_to_excel(results)
                    
                    # Lire fichier pour download
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="💾 Télécharger Excel",
                            data=f,
                            file_name=output_file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    st.success(f"✅ Excel créé : {output_file}")
                except Exception as e:
                    st.error(f"❌ Erreur export Excel : {str(e)}")
        
        with col_export2:
            if st.button("📥 Export CSV", use_container_width=True):
                try:
                    files = export_to_csv(results)
                    st.success(f"✅ {len(files)} fichiers CSV créés")
                    for file in files:
                        st.text(f"• {file}")
                except Exception as e:
                    st.error(f"❌ Erreur export CSV : {str(e)}")
        
        st.markdown("---")
        
        # Métriques clés
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Attributs analysés",
                len(results['vecteurs_4d']),
                help="Nombre colonnes analysées"
            )
        
        with col2:
            st.metric(
                "Usages métier",
                len(results['weights']),
                help="Contextes métier configurés"
            )
        
        with col3:
            top_score = max(results['scores'].values()) if results['scores'] else 0
            st.metric(
                "Risque max",
                f"{top_score:.1%}",
                delta=f"{'CRITIQUE' if top_score > 0.4 else 'OK'}",
                delta_color="inverse"
            )
        
        with col4:
            critical_count = len([s for s in results['scores'].values() if s > 0.4])
            st.metric(
                "Alertes critiques",
                critical_count,
                help="Scores > 40%"
            )
        
        st.markdown("---")
        
        # Heatmap scores
        st.subheader("🔥 Matrice Scores Risque")
        fig_heatmap = create_heatmap(results['scores'])
        st.plotly_chart(fig_heatmap, use_container_width=True, key="heatmap_dashboard")
        
        # Bouton commentaire IA
        if st.button("💬 Expliquer avec Claude", key="explain_heatmap", help="Générer un commentaire IA sur cette matrice"):
            if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                with st.spinner("Claude analyse la matrice..."):
                    # Préparer données pour IA
                    top_scores = sorted(results['scores'].items(), key=lambda x: x[1], reverse=True)[:5]
                    data_for_ai = {
                        "total_combinations": len(results['scores']),
                        "top_5_risks": [{"combo": k, "score": f"{v:.1%}"} for k, v in top_scores],
                        "critical_count": len([s for s in results['scores'].values() if s > 0.4]),
                        "attributs_analyzed": len(results['vecteurs_4d']),
                        "usages_configured": len(results['weights'])
                    }
                    
                    comment = generate_ai_comment("heatmap", data_for_ai, st.session_state.anthropic_api_key)
                    
                    st.info(f"💬 **Commentaire Claude** :\n\n{comment}")
            else:
                st.warning("⚠️ Configure ta clé API Claude dans la sidebar pour utiliser les commentaires IA")
    
    # ========================================================================
    # TAB 2 : VECTEURS 4D
    # ========================================================================
    with tab3:
        st.header("🎯 Vecteurs Qualité 4D")
        
        for attr, vector in results['vecteurs_4d'].items():
            st.subheader(f"📌 {attr}")
            
            # Graphique
            fig = create_vector_chart(vector)
            st.plotly_chart(fig, use_container_width=True, key=f"vector_chart_{attr}")
            
            # Bouton commentaire IA
            if st.button("💬 Expliquer avec Claude", key=f"explain_vector_{attr}", help="Analyser ce vecteur 4D"):
                if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                    with st.spinner("Claude analyse le vecteur..."):
                        data_for_ai = {
                            "attribut": attr,
                            "P_DB": vector.get('P_DB', 0),
                            "P_DP": vector.get('P_DP', 0),
                            "P_BR": vector.get('P_BR', 0),
                            "P_UP": vector.get('P_UP', 0),
                            "alpha_DB": vector.get('alpha_DB', 0),
                            "beta_DB": vector.get('beta_DB', 0),
                            "confidence": "HIGH" if vector.get('beta_DB', 0) > 50 else "MEDIUM"
                        }
                        
                        comment = generate_ai_comment("vector", data_for_ai, st.session_state.anthropic_api_key)
                        
                        st.info(f"💬 **Commentaire Claude** :\n\n{comment}")
                else:
                    st.warning("⚠️ Configure ta clé API Claude dans la sidebar")
            
            # Détails Beta
            with st.expander("🔬 Paramètres Beta détaillés"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("**[DB] Database**")
                    st.write(f"Beta({vector['alpha_DB']:.1f}, {vector['beta_DB']:.1f})")
                    st.write(f"P = {vector['P_DB']:.3f}")
                    st.write(f"σ = {vector.get('std_DB', 0):.3f}")
                
                with col2:
                    st.markdown("**[DP] Data Processing**")
                    st.write(f"Beta({vector['alpha_DP']:.1f}, {vector['beta_DP']:.1f})")
                    st.write(f"P = {vector['P_DP']:.3f}")
                    st.write(f"σ = {vector.get('std_DP', 0):.3f}")
                
                with col3:
                    st.markdown("**[BR] Business Rules**")
                    st.write(f"Beta({vector['alpha_BR']:.1f}, {vector['beta_BR']:.1f})")
                    st.write(f"P = {vector['P_BR']:.3f}")
                    st.write(f"σ = {vector.get('std_BR', 0):.3f}")
                
                with col4:
                    st.markdown("**[UP] Usage-fit**")
                    st.write(f"Beta({vector['alpha_UP']:.1f}, {vector['beta_UP']:.1f})")
                    st.write(f"P = {vector['P_UP']:.3f}")
                    st.write(f"σ = {vector.get('std_UP', 0):.3f}")
            
            st.markdown("---")
    
    # ========================================================================
    # TAB 3 : PRIORITÉS
    # ========================================================================
    with tab4:
        st.header("⚠️ Top Priorités Actions")
        
        for i, priority in enumerate(results['top_priorities'][:3], 1):  # Top 3 seulement avec bouton IA
            # Couleur box selon sévérité
            if priority['severite'] == 'CRITIQUE':
                box_class = "danger-box"
                emoji = "🚨"
            elif priority['severite'] == 'ÉLEVÉ':
                box_class = "warning-box"
                emoji = "⚠️"
            else:
                box_class = "success-box"
                emoji = "✅"
            
            st.markdown(f"""
            <div class="{box_class}">
                <h3>{emoji} #{i} - {priority['attribut']} × {priority['usage']}</h3>
                <p><strong>Score risque :</strong> {priority['score']:.1%} ({priority['severite']})</p>
                <p><strong>Impact :</strong> {priority['records_affected']} enregistrements, {priority['impact_mensuel']:,}€/mois</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Actions recommandées
            with st.expander("📋 Actions recommandées"):
                for action in priority.get('actions', []):
                    st.write(f"• {action}")
            
            # Bouton commentaire IA
            if st.button("💬 Analyser avec Claude", key=f"explain_priority_{i}", help="Recommandation IA pour cette priorité"):
                if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                    with st.spinner("Claude analyse la priorité..."):
                        comment = generate_ai_comment("priority", priority, st.session_state.anthropic_api_key)
                        st.info(f"💬 **Recommandation Claude** :\n\n{comment}")
                else:
                    st.warning("⚠️ Configure ta clé API Claude dans la sidebar")
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Afficher les priorités restantes sans bouton IA
        if len(results['top_priorities']) > 3:
            st.markdown("---")
            st.subheader("Autres priorités")
            
            for i, priority in enumerate(results['top_priorities'][3:], 4):
                # Couleur box selon sévérité (version simplifiée sans IA)
                if priority['severite'] == 'CRITIQUE':
                    box_class = "danger-box"
                    emoji = "🚨"
                elif priority['severite'] == 'ÉLEVÉ':
                    box_class = "warning-box"
                    emoji = "⚠️"
                else:
                    box_class = "success-box"
                    emoji = "✅"
                
                st.markdown(f"""
                <div class="{box_class}">
                    <h4>{emoji} #{i} - {priority['attribut']} × {priority['usage']}</h4>
                    <p><strong>Score :</strong> {priority['score']:.1%} ({priority['severite']})</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================================================
    # TAB 4 : LINEAGE AVEC SCÉNARIOS RÉALISTES
    # ========================================================================
    with tab5:
        st.header("🔄 Propagation Risque Lineage")
        
        st.markdown("""
        ### 🎯 Objectif : Simuler la dégradation qualité le long des pipelines
        
        Sélectionne un **scénario réaliste** pour voir comment le risque se propage et s'aggrave à travers les transformations.
        """)
        
        # Sélection scénario
        st.markdown("### 📋 Choisis un scénario")
        
        scenario = st.radio(
            "Incidents basés sur cas réels fréquents en entreprise",
            [
                "✅ Baseline (pas d'incident - qualité stable)",
                "🔧 Incident ETL Parser (bug déploiement - très fréquent)",
                "📊 Enrichissement Métier Défaillant (référentiel obsolète)",
                "📈 Reporting Défaillant (données incomplètes - deadline approche)",
                "⚠️ Dégradation Cumulative (micro-erreurs qui s'accumulent)",
                "✏️ Personnalisé (créer ton propre scénario avec Claude)"
            ],
            help="Scénarios benchmarkés sur incidents réels industriels + option personnalisée"
        )
        
        # Définir données selon scénario
        if "Baseline" in scenario:
            # Scénario stable (actuel)
            scenario_data = {
                "nom": "Baseline - Qualité Stable",
                "emoji": "✅",
                "contexte": """**Situation normale** : Aucun incident détecté.
                
Les pipelines ETL fonctionnent correctement, les transformations préservent la qualité.
C'est la situation de référence (baseline) pour comparer avec les incidents.""",
                "risk_source": 0.332,
                "risk_final": 0.337,
                "delta": 0.005,
                "timeline": [
                    {"etape": "Source SIRH", "P_DB": 0.367, "P_DP": 1.000, "P_BR": 0.050, "P_UP": 0.100},
                    {"etape": "ETL Extraction", "P_DB": 0.367, "P_DP": 1.000, "P_BR": 0.050, "P_UP": 0.100},
                    {"etape": "Enrichissement", "P_DB": 0.367, "P_DP": 1.000, "P_BR": 0.069, "P_UP": 0.100},
                    {"etape": "Agrégation Paie", "P_DB": 0.367, "P_DP": 1.000, "P_BR": 0.069, "P_UP": 0.100},
                    {"etape": "Calcul Final", "P_DB": 0.367, "P_DP": 1.000, "P_BR": 0.069, "P_UP": 0.100}
                ],
                "interpretation": "➡️ STABLE - Qualité préservée tout au long du pipeline",
                "cause_racine": "Aucun incident",
                "impact_records": 0,
                "impact_financier": 0,
                "temps_detection": "N/A",
                "actions": []
            }
        
        elif "Incident ETL" in scenario:
            # Scénario ETL cassé (lié à tab Surveillance)
            scenario_data = {
                "nom": "Incident ETL Parser",
                "emoji": "🔧",
                "contexte": """**Déploiement ETL v2.8.2** le 12/01/2025 à 23:15 (commit abc123def).

**Bug introduit** : Parser Ancienneté modifié, virgules décimales non gérées.
```python
# AVANT (v2.8.1) ✅
anciennete = float(value.replace(',', '.'))

# APRÈS (v2.8.2) ❌  
anciennete = float(value)  # Crash sur "7,21"
```

**Résultat** : 141/687 enregistrements cassés lors de l'extraction ETL.""",
                "risk_source": 0.463,
                "risk_final": 0.623,
                "delta": 0.160,
                "timeline": [
                    {"etape": "Source SIRH", "P_DB": 0.990, "P_DP": 0.020, "P_BR": 0.200, "P_UP": 0.100},
                    {"etape": "ETL Extraction", "P_DB": 0.990, "P_DP": 0.285, "P_BR": 0.200, "P_UP": 0.100},
                    {"etape": "Enrichissement", "P_DB": 0.990, "P_DP": 0.285, "P_BR": 0.220, "P_UP": 0.100},
                    {"etape": "Agrégation Paie", "P_DB": 0.990, "P_DP": 0.310, "P_BR": 0.220, "P_UP": 0.100},
                    {"etape": "Calcul Final", "P_DB": 0.990, "P_DP": 0.320, "P_BR": 0.220, "P_UP": 0.100}
                ],
                "interpretation": "🚨 CRITIQUE - Dégradation DP massive (+26.5 points) dès extraction ETL",
                "cause_racine": "Commit abc123def - Parser Ancienneté cassé (virgule non gérée)",
                "impact_records": 141,
                "impact_financier": 45080,
                "temps_detection": "9 heures (vs 3 semaines avec DAMA)",
                "actions": [
                    "🔄 Rollback immédiat vers ETL v2.8.1",
                    "🔧 Fix parser : value.replace(',', '.') avant float()",
                    "📊 Batch correction des 141 enregistrements",
                    "🔔 Activer monitoring continu DP sur Ancienneté",
                    "🧪 Ajouter test unitaire parser avec virgules"
                ]
            }
        
        elif "Enrichissement" in scenario:
            # Scénario référentiel obsolète
            scenario_data = {
                "nom": "Enrichissement Métier Défaillant",
                "emoji": "📊",
                "contexte": """**Fusion départements RH** : Nord + Sud → Grand Nord (01/12/2024).

**Problème** : Table référentiel `ref_departements` non mise à jour.

**Impact progressif** :
- Décembre : 15 employés mal rattachés (2%)
- Janvier : 45 employés mal rattachés (7%)
- Février : 89 employés mal rattachés (13%)

**Découverte** : Audit interne CSE détecte incohérences reporting social.""",
                "risk_source": 0.332,
                "risk_final": 0.485,
                "delta": 0.153,
                "timeline": [
                    {"etape": "Source SIRH", "P_DB": 0.367, "P_DP": 0.020, "P_BR": 0.050, "P_UP": 0.100},
                    {"etape": "ETL Extraction", "P_DB": 0.367, "P_DP": 0.020, "P_BR": 0.050, "P_UP": 0.100},
                    {"etape": "Enrichissement", "P_DB": 0.367, "P_DP": 0.020, "P_BR": 0.280, "P_UP": 0.100},
                    {"etape": "Agrégation Paie", "P_DB": 0.367, "P_DP": 0.025, "P_BR": 0.280, "P_UP": 0.100},
                    {"etape": "Calcul Final", "P_DB": 0.367, "P_DP": 0.030, "P_BR": 0.280, "P_UP": 0.100}
                ],
                "interpretation": "⚠️ ÉLEVÉ - Dégradation BR progressive (+23 points) lors enrichissement métier",
                "cause_racine": "Table ref_departements obsolète (fusion Nord+Sud non intégrée)",
                "impact_records": 89,
                "impact_financier": 12400,
                "temps_detection": "2 jours avec monitoring BR (vs 3 semaines manuellement)",
                "actions": [
                    "📋 Mise à jour table ref_departements (fusion Nord+Sud)",
                    "🔄 Recalcul batch des rattachements depuis 01/12",
                    "📊 Correction des 89 employés mal rattachés",
                    "🔔 Alerte automatique sur changements référentiels",
                    "📅 Workflow validation changements orga (DRH→IT)"
                ]
            }
        
        elif "Reporting" in scenario:
            # NOUVEAU : Scénario reporting défaillant
            scenario_data = {
                "nom": "Reporting CSE Défaillant",
                "emoji": "📈",
                "contexte": """**Rapport mensuel CSE** (Comité Social Économique) - Deadline : 05/02/2025.

**Découverte J-2** (03/02) lors revue DRH : 252/687 dates promotions manquantes (37%).

**Cause racine** : Workflow validation promotions non respecté.
- Managers ne saisissent pas les promotions dans SIRH
- Processus manuel, pas d'alerte automatique
- Dégradation progressive sur 6 mois (jamais détectée)

**Impact** : Reporting incomplet, crédibilité DRH auprès CSE compromise.""",
                "risk_source": 0.364,
                "risk_final": 0.520,
                "delta": 0.156,
                "timeline": [
                    {"etape": "Source SIRH", "P_DB": 0.364, "P_DP": 0.143, "P_BR": 0.252, "P_UP": 0.250},
                    {"etape": "ETL Extraction", "P_DB": 0.364, "P_DP": 0.150, "P_BR": 0.252, "P_UP": 0.250},
                    {"etape": "Enrichissement", "P_DB": 0.364, "P_DP": 0.160, "P_BR": 0.280, "P_UP": 0.250},
                    {"etape": "Agrégation CSE", "P_DB": 0.364, "P_DP": 0.170, "P_BR": 0.300, "P_UP": 0.380},
                    {"etape": "Export Reporting", "P_DB": 0.364, "P_DP": 0.180, "P_BR": 0.310, "P_UP": 0.420}
                ],
                "interpretation": "⚠️ ÉLEVÉ - Dégradation multi-dimensions (UP +17 pts, BR +6 pts) pour reporting CSE",
                "cause_racine": "Workflow promotions non respecté - 252 dates manquantes (37%)",
                "impact_records": 252,
                "impact_financier": 7500,
                "temps_detection": "J-2 avant deadline (détection manuelle tardive)",
                "actions": [
                    "🚨 URGENT : Relance managers pour saisie promotions (252 cas)",
                    "📧 Email automatique rappel mensuel + escalade N+1",
                    "🔔 Dashboard temps réel complétude données promotions",
                    "📊 Alerte seuil critique (<90%) J-15 avant deadline",
                    "🔄 Processus backup : extraction fichiers Direction (plan B)",
                    "💰 Coût opportunité : crédibilité DRH + risque contentieux CSE"
                ]
            }
        
        elif "Personnalisé" in scenario:
            # SCÉNARIO PERSONNALISABLE
            st.markdown("### ✏️ Créer ton Scénario Personnalisé")
            
            # Choix mode
            mode_custom = st.radio(
                "Comment veux-tu créer ton scénario ?",
                [
                    "🤖 Mode IA : Décris l'incident, Claude génère les chiffres",
                    "📊 Mode Manuel : Entre les chiffres toi-même"
                ],
                help="Mode IA = plus rapide, Mode Manuel = contrôle total"
            )
            
            if "Mode IA" in mode_custom:
                # MODE IA : Description textuelle → Claude génère les chiffres
                st.markdown("#### 🤖 Décris ton incident à Claude")
                
                with st.form("custom_scenario_ia_form"):
                    nom_incident = st.text_input(
                        "Nom de l'incident",
                        placeholder="Ex: Migration base de données ratée",
                        help="Titre court pour identifier l'incident"
                    )
                    
                    description_incident = st.text_area(
                        "Décris l'incident en détail",
                        placeholder="""Ex: Notre migration de SQL Server vers PostgreSQL a causé des pertes de données.
Les colonnes avec NULL ont été mal converties, créant des erreurs dans les calculs.
Les transformations ETL ont échoué sur 30% des records.
Le reporting mensuel était incomplet pendant 2 semaines.""",
                        height=150,
                        help="Plus tu donnes de détails, mieux Claude pourra générer les chiffres réalistes"
                    )
                    
                    pipeline_etapes = st.text_input(
                        "Étapes du pipeline (séparées par virgule)",
                        value="Source DB, Migration, ETL, Transformation, Reporting",
                        help="Ex: Source, Extraction, Enrichissement, Agrégation, Export"
                    )
                    
                    impact_estime = st.selectbox(
                        "Impact estimé",
                        ["Faible (5-15%)", "Moyen (15-30%)", "Élevé (30-50%)", "Critique (>50%)"],
                        help="Gravité globale de l'incident"
                    )
                    
                    submitted_ia = st.form_submit_button("🚀 Générer avec Claude", type="primary")
                
                if submitted_ia:
                    if not nom_incident or not description_incident:
                        st.error("⚠️ Le nom et la description sont obligatoires")
                    elif 'anthropic_api_key' not in st.session_state or not st.session_state.anthropic_api_key:
                        st.error("⚠️ Configure ta clé API Claude dans la sidebar")
                    else:
                        with st.spinner("🤖 Claude génère ton scénario personnalisé..."):
                            try:
                                client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
                                
                                # Prompt pour génération scénario
                                prompt_generation = f"""Tu es un expert Data Quality. Génère un scénario de lineage réaliste basé sur cette description d'incident.

**Incident** : {nom_incident}

**Description** : {description_incident}

**Étapes pipeline** : {pipeline_etapes}

**Impact estimé** : {impact_estime}

**Génère un JSON avec cette structure exacte** :

```json
{{
  "nom": "Nom incident",
  "contexte": "Description détaillée 3-4 phrases",
  "risk_source": 0.XX (probabilité 0-1),
  "risk_final": 0.XX (probabilité 0-1),
  "delta": 0.XX (différence),
  "timeline": [
    {{"etape": "Nom étape 1", "P_DB": 0.XX, "P_DP": 0.XX, "P_BR": 0.XX, "P_UP": 0.XX}},
    {{"etape": "Nom étape 2", "P_DB": 0.XX, "P_DP": 0.XX, "P_BR": 0.XX, "P_UP": 0.XX}},
    ...
  ],
  "interpretation": "Texte explication",
  "cause_racine": "Cause technique précise",
  "impact_records": nombre (entier),
  "impact_financier": montant euros/mois (entier),
  "temps_detection": "Durée",
  "actions": ["Action 1", "Action 2", ...]
}}
```

**RÈGLES CRITIQUES** :
1. Les probabilités P_DB, P_DP, P_BR, P_UP sont entre 0.0 et 1.0
2. Chaque étape doit montrer une évolution réaliste
3. Les dimensions affectées dépendent du type d'incident :
   - Problème structurel → P_DB élevé
   - Erreur transformation → P_DP élevé
   - Règle métier violée → P_BR élevé
   - Inadéquation usage → P_UP élevé
4. Le risque doit progresser ou rester stable (jamais diminuer sans correction)
5. Impact financier réaliste : 5k€-150k€/mois selon gravité
6. Temps détection : comparer avec approche DAMA (heures vs semaines)

**Réponds UNIQUEMENT avec le JSON, rien d'autre.**"""
                                
                                response = client.messages.create(
                                    model="claude-sonnet-4-20250514",
                                    max_tokens=2000,
                                    system="Tu es un expert Data Quality qui génère des scénarios de lineage réalistes au format JSON. Tu réponds UNIQUEMENT avec le JSON valide, sans markdown ni texte additionnel.",
                                    messages=[{"role": "user", "content": prompt_generation}]
                                )
                                
                                # Extraire JSON
                                response_text = response.content[0].text
                                
                                # Nettoyer markdown si présent
                                if "```json" in response_text:
                                    json_start = response_text.find("```json") + 7
                                    json_end = response_text.find("```", json_start)
                                    response_text = response_text[json_start:json_end].strip()
                                elif "```" in response_text:
                                    json_start = response_text.find("```") + 3
                                    json_end = response_text.find("```", json_start)
                                    response_text = response_text[json_start:json_end].strip()
                                
                                # Parser JSON
                                scenario_data = json.loads(response_text)
                                scenario_data['emoji'] = "✏️"
                                
                                # Stocker dans session state
                                st.session_state.custom_scenario_data = scenario_data
                                
                                st.success("✅ Scénario généré avec succès par Claude !")
                                st.balloons()
                                
                            except json.JSONDecodeError as e:
                                st.error(f"❌ Erreur parsing JSON : {str(e)}")
                                st.code(response_text)
                            except Exception as e:
                                st.error(f"❌ Erreur génération : {str(e)}")
                
                # Afficher scénario généré si disponible
                if 'custom_scenario_data' in st.session_state:
                    scenario_data = st.session_state.custom_scenario_data
                    st.success("✅ Scénario personnalisé généré par Claude")
                    
                    # Afficher résumé du scénario
                    with st.expander("📋 Résumé du scénario généré", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Risque initial", f"{scenario_data.get('risk_source', 0)*100:.1f}%")
                            st.metric("Impact records", f"{scenario_data.get('impact_records', 0):,}")
                        with col2:
                            st.metric("Risque final", f"{scenario_data.get('risk_final', 0)*100:.1f}%", 
                                     delta=f"+{scenario_data.get('delta', 0)*100:.1f}%")
                            st.metric("Impact financier", f"{scenario_data.get('impact_financier', 0):,}€/mois")
                        
                        st.markdown("**📊 Probabilités par étape du pipeline :**")
                        
                        # Tableau des probabilités (sans heatmap)
                        timeline_df = pd.DataFrame(scenario_data.get('timeline', []))
                        if not timeline_df.empty:
                            # Formatter en pourcentages
                            display_df = timeline_df.copy()
                            for col in ['P_DB', 'P_DP', 'P_BR', 'P_UP']:
                                if col in display_df.columns:
                                    display_df[col] = display_df[col].apply(lambda x: f"{x*100:.1f}%")
                            
                            st.dataframe(display_df, use_container_width=True)
                        
                        st.markdown(f"**🔍 Cause racine :** {scenario_data.get('cause_racine', 'N/A')}")
                        st.markdown(f"**⏱️ Temps détection :** {scenario_data.get('temps_detection', 'N/A')}")
                        
                        if scenario_data.get('actions'):
                            st.markdown("**✅ Actions recommandées :**")
                            for action in scenario_data['actions']:
                                st.markdown(f"- {action}")
                    
                else:
                    st.info("💡 Remplis le formulaire ci-dessus et clique 'Générer' pour créer ton scénario")
                    st.stop()
            
            else:
                # MODE MANUEL : Saisie des chiffres
                st.markdown("#### 📊 Entre les chiffres manuellement")
                
                with st.form("custom_scenario_manual_form"):
                    nom_incident_manual = st.text_input(
                        "Nom de l'incident",
                        value="Mon Incident Personnalisé"
                    )
                    
                    contexte_manual = st.text_area(
                        "Contexte / Description",
                        value="Description de l'incident...",
                        height=100
                    )
                    
                    st.markdown("**Nombre d'étapes du pipeline**")
                    nb_etapes = st.slider("Nombre d'étapes", 3, 8, 5)
                    
                    timeline_manual = []
                    
                    for i in range(nb_etapes):
                        st.markdown(f"##### 🔹 Étape {i+1}")
                        
                        col_nom, col_db, col_dp, col_br, col_up = st.columns([2,1,1,1,1])
                        
                        with col_nom:
                            nom_etape = st.text_input(
                                f"Nom étape {i+1}",
                                value=f"Étape {i+1}",
                                key=f"nom_etape_{i}"
                            )
                        
                        with col_db:
                            p_db = st.number_input(
                                "DB (%)",
                                0, 100,
                                value=min(10 + i*5, 90),
                                key=f"p_db_{i}"
                            )
                        
                        with col_dp:
                            p_dp = st.number_input(
                                "DP (%)",
                                0, 100,
                                value=min(5 + i*8, 85),
                                key=f"p_dp_{i}"
                            )
                        
                        with col_br:
                            p_br = st.number_input(
                                "BR (%)",
                                0, 100,
                                value=min(8 + i*3, 75),
                                key=f"p_br_{i}"
                            )
                        
                        with col_up:
                            p_up = st.number_input(
                                "UP (%)",
                                0, 100,
                                value=min(12 + i*2, 70),
                                key=f"p_up_{i}"
                            )
                        
                        timeline_manual.append({
                            "etape": nom_etape,
                            "P_DB": p_db / 100,
                            "P_DP": p_dp / 100,
                            "P_BR": p_br / 100,
                            "P_UP": p_up / 100
                        })
                    
                    st.markdown("**Impact business**")
                    col_rec, col_fin = st.columns(2)
                    
                    with col_rec:
                        impact_records_manual = st.number_input(
                            "Records affectés",
                            0, 10000,
                            value=100
                        )
                    
                    with col_fin:
                        impact_financier_manual = st.number_input(
                            "Impact €/mois",
                            0, 500000,
                            value=15000,
                            step=1000
                        )
                    
                    submitted_manual = st.form_submit_button("✅ Créer Scénario", type="primary")
                
                if submitted_manual:
                    # Calculer risques
                    risk_source = (timeline_manual[0]['P_DB'] + timeline_manual[0]['P_DP'] + 
                                 timeline_manual[0]['P_BR'] + timeline_manual[0]['P_UP']) / 4
                    risk_final = (timeline_manual[-1]['P_DB'] + timeline_manual[-1]['P_DP'] + 
                                timeline_manual[-1]['P_BR'] + timeline_manual[-1]['P_UP']) / 4
                    
                    scenario_data = {
                        "nom": nom_incident_manual,
                        "emoji": "✏️",
                        "contexte": contexte_manual,
                        "risk_source": risk_source,
                        "risk_final": risk_final,
                        "delta": risk_final - risk_source,
                        "timeline": timeline_manual,
                        "interpretation": f"{'🚨 CRITIQUE' if risk_final > 0.5 else '⚠️ ÉLEVÉ' if risk_final > 0.3 else '➡️ MOYEN'} - Scénario personnalisé",
                        "cause_racine": "Incident personnalisé (détails dans contexte)",
                        "impact_records": impact_records_manual,
                        "impact_financier": impact_financier_manual,
                        "temps_detection": "À définir selon monitoring",
                        "actions": [
                            "Action 1 : À définir selon contexte",
                            "Action 2 : Implémenter monitoring spécifique",
                            "Action 3 : Corriger cause racine identifiée"
                        ]
                    }
                    
                    st.session_state.custom_scenario_data = scenario_data
                    st.success("✅ Scénario manuel créé !")
                    st.balloons()
                
                # Afficher scénario manuel si disponible
                if 'custom_scenario_data' in st.session_state:
                    scenario_data = st.session_state.custom_scenario_data
                    st.success("✅ Utilisation du scénario manuel")
                else:
                    st.info("💡 Remplis le formulaire ci-dessus et clique 'Créer' pour définir ton scénario")
                    st.stop()
        
        else:  # Dégradation cumulative
            scenario_data = {
                "nom": "Dégradation Cumulative Multi-Étapes",
                "emoji": "⚠️",
                "contexte": """**Absence monitoring intermédiaire** : Chaque étape dégrade légèrement la qualité.

**Problème** : Aucune micro-dégradation n'est critique individuellement, mais l'accumulation devient critique.

**Étapes** :
1. Extraction : +3% erreurs parsing (tolérée)
2. Enrichissement : +5% incohérences référentiels (tolérée)
3. Transformation : +4% erreurs calculs (tolérée)
4. Agrégation : +6% doublons (tolérée)
5. **Cumul : +18% = CRITIQUE** ❌

**Découverte** : Réclamations utilisateurs après 1 semaine production.""",
                "risk_source": 0.332,
                "risk_final": 0.518,
                "delta": 0.186,
                "timeline": [
                    {"etape": "Source SIRH", "P_DB": 0.367, "P_DP": 0.020, "P_BR": 0.050, "P_UP": 0.100},
                    {"etape": "ETL Extraction", "P_DB": 0.367, "P_DP": 0.050, "P_BR": 0.050, "P_UP": 0.100},
                    {"etape": "Enrichissement", "P_DB": 0.367, "P_DP": 0.085, "P_BR": 0.100, "P_UP": 0.100},
                    {"etape": "Transformation", "P_DB": 0.367, "P_DP": 0.125, "P_BR": 0.140, "P_UP": 0.120},
                    {"etape": "Agrégation", "P_DB": 0.367, "P_DP": 0.180, "P_BR": 0.180, "P_UP": 0.150},
                    {"etape": "Calcul Final", "P_DB": 0.367, "P_DP": 0.245, "P_BR": 0.230, "P_UP": 0.180}
                ],
                "interpretation": "⚠️ ÉLEVÉ - Accumulation progressive (+18.6 pts) passée inaperçue sans monitoring",
                "cause_racine": "Absence monitoring intermédiaire granulaire (only input/output)",
                "impact_records": 127,
                "impact_financier": 18200,
                "temps_detection": "1 semaine (réclamations users vs détection proactive impossible)",
                "actions": [
                    "🔔 Implémenter monitoring INTER-ÉTAPES (pas juste I/O)",
                    "📊 Seuils tolérance par étape (ex: +2% max)",
                    "🚨 Alerte cumulative si somme dégradations >10%",
                    "📈 Dashboard lineage temps réel (visualiser accumulation)",
                    "🧪 Tests automatisés après chaque transformation"
                ]
            }
        
        # Afficher contexte scénario
        st.markdown("---")
        st.markdown(f"### {scenario_data['emoji']} {scenario_data['nom']}")
        
        with st.expander("📋 Contexte détaillé", expanded=True):
            st.markdown(scenario_data['contexte'])
        
        # Métriques impact
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Risque source",
                f"{scenario_data['risk_source']:.1%}"
            )
        
        with col2:
            delta_val = scenario_data['delta']
            st.metric(
                "Risque final",
                f"{scenario_data['risk_final']:.1%}",
                delta=f"+{delta_val:.1%}",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Enregistrements affectés",
                f"{scenario_data['impact_records']}"
            )
        
        with col4:
            if scenario_data['impact_financier'] > 0:
                st.metric(
                    "Impact financier/mois",
                    f"{scenario_data['impact_financier']:,}€"
                )
            else:
                st.metric("Impact financier", "0€")
        
        st.markdown("---")
        
        # Timeline propagation
        st.subheader("📅 Timeline Propagation Détaillée")
        
        for idx, step in enumerate(scenario_data['timeline']):
            etape = step['etape']
            
            # Afficher nom étape
            st.markdown(f"### 🔹 Étape {idx+1} : {etape}")
            
            # Métriques 4D
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("DB", f"{step['P_DB']:.1%}", 
                       delta=f"{(step['P_DB'] - scenario_data['timeline'][max(0,idx-1)]['P_DB']):.1%}" if idx > 0 else None,
                       delta_color="inverse")
            col2.metric("DP", f"{step['P_DP']:.1%}",
                       delta=f"{(step['P_DP'] - scenario_data['timeline'][max(0,idx-1)]['P_DP']):.1%}" if idx > 0 else None,
                       delta_color="inverse")
            col3.metric("BR", f"{step['P_BR']:.1%}",
                       delta=f"{(step['P_BR'] - scenario_data['timeline'][max(0,idx-1)]['P_BR']):.1%}" if idx > 0 else None,
                       delta_color="inverse")
            col4.metric("UP", f"{step['P_UP']:.1%}",
                       delta=f"{(step['P_UP'] - scenario_data['timeline'][max(0,idx-1)]['P_UP']):.1%}" if idx > 0 else None,
                       delta_color="inverse")
            
            # Bouton explication par étape
            if st.button(f"💬 Expliquer cette étape", key=f"explain_lineage_step_{idx}", help=f"Que se passe-t-il dans '{etape}' ?"):
                if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                    with st.spinner(f"Claude analyse l'étape '{etape}'..."):
                        # Préparer contexte pour IA
                        step_context = f"""Tu es un expert Data Quality. Explique ce qui se passe dans cette étape de lineage en 3-4 phrases maximum.

**Scénario global** : {scenario_data['nom']}
**Étape actuelle** : {etape} (étape {idx+1}/{len(scenario_data['timeline'])})

**Probabilités actuelles** :
- P_DB = {step['P_DB']:.1%} (Database)
- P_DP = {step['P_DP']:.1%} (Data Processing)
- P_BR = {step['P_BR']:.1%} (Business Rules)
- P_UP = {step['P_UP']:.1%} (Usage-fit)

**Évolution depuis étape précédente** :
{f"- Delta DB : {(step['P_DB'] - scenario_data['timeline'][idx-1]['P_DB'])*100:+.1f} points" if idx > 0 else "- Étape source (baseline)"}
{f"- Delta DP : {(step['P_DP'] - scenario_data['timeline'][idx-1]['P_DP'])*100:+.1f} points" if idx > 0 else ""}
{f"- Delta BR : {(step['P_BR'] - scenario_data['timeline'][idx-1]['P_BR'])*100:+.1f} points" if idx > 0 else ""}
{f"- Delta UP : {(step['P_UP'] - scenario_data['timeline'][idx-1]['P_UP'])*100:+.1f} points" if idx > 0 else ""}

**Contexte incident** : {scenario_data['contexte'][:200]}...

Explique :
1. Ce que fait cette étape techniquement (extraction, transformation, agrégation, etc.)
2. Pourquoi telle(s) dimension(s) sont affectées à cette étape
3. L'impact opérationnel concret de cette dégradation

Style : Technique mais accessible, pédagogique, avec exemples concrets."""
                        
                        try:
                            client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
                            
                            response = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=500,
                                system="Tu es un expert Data Quality qui explique les transformations de données avec un style direct, pédagogique et technique. Toujours 3-4 phrases maximum.",
                                messages=[{"role": "user", "content": step_context}]
                            )
                            
                            comment = response.content[0].text
                            st.info(f"💬 **Explication Claude - {etape}** :\n\n{comment}")
                            
                        except Exception as e:
                            st.error(f"⚠️ Erreur génération commentaire : {str(e)}")
                else:
                    st.warning("⚠️ Configure ta clé API Claude dans la sidebar")
            
            st.markdown("---")
        
        # Interprétation
        st.info(f"**Interprétation :** {scenario_data['interpretation']}")
        
        # Cause racine + Impact
        st.markdown("### 🔍 Analyse Incident")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Cause Racine**")
            st.write(scenario_data['cause_racine'])
            
            if scenario_data['temps_detection'] != "N/A":
                st.success(f"⏱️ **Temps détection** : {scenario_data['temps_detection']}")
        
        with col2:
            st.markdown("**📊 Impact Mesuré**")
            st.write(f"• Records affectés : **{scenario_data['impact_records']}** / 687")
            if scenario_data['impact_financier'] > 0:
                st.write(f"• Impact financier : **{scenario_data['impact_financier']:,}€/mois**")
            st.write(f"• Delta risque : **+{scenario_data['delta']:.1%}** points")
        
        # Actions recommandées
        if scenario_data['actions']:
            st.markdown("### 🛠️ Actions Recommandées")
            
            for action in scenario_data['actions']:
                st.write(f"• {action}")
        
        # Bouton commentaire IA
        st.markdown("---")
        if st.button("💬 Analyser avec Claude", key="explain_lineage", help="Analyse détaillée de la propagation"):
            if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                with st.spinner("Claude analyse la propagation..."):
                    data_for_ai = {
                        "scenario": scenario_data['nom'],
                        "risk_source": scenario_data['risk_source'],
                        "risk_final": scenario_data['risk_final'],
                        "delta_absolute": scenario_data['delta'],
                        "cause_racine": scenario_data['cause_racine'],
                        "impact_records": scenario_data['impact_records'],
                        "impact_financier": scenario_data['impact_financier'],
                        "temps_detection": scenario_data['temps_detection'],
                        "history": scenario_data['timeline']
                    }
                    
                    comment = generate_ai_comment("lineage", data_for_ai, st.session_state.anthropic_api_key)
                    st.info(f"💬 **Analyse Claude** :\n\n{comment}")
            else:
                st.warning("⚠️ Configure ta clé API Claude dans la sidebar")
    
    # ========================================================================
    # TAB 5 : COMPARAISON DAMA
    # ========================================================================
    with tab6:
        st.header("📈 Comparaison DAMA vs Probabiliste")
        
        # SECTION EXPLICATIVE EN HAUT
        with st.expander("📚 Définition des Indicateurs DAMA (6 dimensions)", expanded=False):
            st.markdown("""
            Le **DAMA-DMBOK** (Data Management Body of Knowledge) définit **6 dimensions classiques** de qualité :
            
            | Dimension | Définition | Comment calculé dans cette démo |
            |-----------|------------|--------------------------------|
            | **Complétude** (Completeness) | % de données présentes vs attendues | `1 - (nb_null / nb_total)` |
            | **Exactitude** (Accuracy) | % de données correctes vs valeurs réelles | Détection erreurs typage + formats |
            | **Cohérence** (Consistency) | % respect règles métier et contraintes | Vérif règles business définies |
            | **Fraîcheur** (Timeliness) | % données à jour selon fraîcheur attendue | Analyse champs date/timestamp |
            | **Validité** (Validity) | % données conformes formats/domaines | Validation domaines valeurs |
            | **Unicité** (Uniqueness) | % absence doublons | Détection doublons exacts |
            
            **📊 Score Global DAMA** = Moyenne simple des 6 dimensions (poids égaux)
            
            ⚠️ **Limites approche DAMA** :
            - Toutes dimensions comptent pareil (pas de pondération usage)
            - Seuils binaires (OK/KO) au lieu de probabilités continues
            - Ne capture pas l'incertitude ni la confiance dans les mesures
            - Pas de contexte d'usage métier intégré
            """)
        
        with st.expander("🎯 Approche Probabiliste (Framework 4D)", expanded=False):
            st.markdown("""
            Notre framework utilise **4 dimensions avec pondérations contextuelles** :
            
            | Dimension | Formule Beta | Pondération usage |
            |-----------|--------------|-------------------|
            | **P_DB** (Structure) | Beta(α, β) depuis nb_null, errors | w_DB selon usage |
            | **P_DP** (Traitements) | Beta depuis erreurs transformation | w_DP selon usage |
            | **P_BR** (Règles Métier) | Beta depuis violations business | w_BR selon usage |
            | **P_UP** (Utilisabilité) | Beta depuis inadéquation usage | w_UP selon usage |
            
            **🎯 Score Risque Contextualisé** = Σ (P_dim × w_dim)
            
            ✅ **Avantages** :
            - Probabilités continues (0-100%) avec incertitude capturée
            - Pondérations adaptées à l'usage métier spécifique
            - Distributions Beta permettent agrégation mathématique rigoureuse
            - Détection proactive vs réactive
            """)
        
        st.markdown("---")
        
        comparaison = results['comparaison']
        
        # Scores DAMA
        st.subheader("📊 Scores DAMA Traditionnels")
        st.caption("💡 Survolez les métriques pour voir comment chaque score est calculé")
        
        for attr, dama_score in comparaison['dama_scores'].items():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Calculer formule affichée
                dims = ['completeness', 'consistency', 'accuracy', 'timeliness', 'validity', 'uniqueness']
                # Gérer valeurs None (dimensions incalculables)
                dim_values = []
                dim_labels = []
                for d in dims:
                    val = dama_score.get(d)
                    if val is not None:
                        dim_values.append(val)
                        dim_labels.append(f"{val:.1%}")
                    else:
                        dim_values.append(None)
                        dim_labels.append("N/A")
                
                # Compter dimensions calculables
                nb_calculables = dama_score.get('dimensions_calculables', len([v for v in dim_values if v is not None]))
                nb_total = dama_score.get('dimensions_total', 6)
                
                # Formule avec N/A
                formule_parts = []
                for v, label in zip(dim_values, dim_labels):
                    formule_parts.append(label if v is not None else "N/A")
                formule = " + ".join(formule_parts)
                
                score_global = dama_score['score_global']
                
                st.metric(
                    attr,
                    f"{score_global:.1%}",
                    help=f"""**Calcul** : ({formule}) / {nb_calculables} = {score_global:.1%}

Dimensions DAMA : {nb_calculables}/{nb_total} calculables

✅ Completeness, Uniqueness
❌ Consistency, Accuracy, Timeliness, Validity (métadonnées manquantes)
"""
                )
            
            with col2:
                # TOUJOURS afficher les 6 dimensions DAMA (même si non calculables)
                vals = []
                colors = []
                texts = []
                hovertexts = []
                patterns = []  # Pour barres hachurées
                
                for d in dims:
                    val = dama_score.get(d)
                    if val is not None:
                        # Dimension calculée ✅
                        vals.append(val * 100)
                        colors.append('rgba(100, 200, 255, 0.8)')  # Bleu
                        texts.append(f"{val*100:.1f}%")
                        hovertexts.append(f"<b>{d}</b><br>✅ Calculé<br>Score: {val*100:.1f}%")
                        patterns.append("")
                    else:
                        # Dimension non calculable ❌
                        vals.append(15)  # Petite barre pour voir la croix
                        colors.append('rgba(200, 50, 50, 0.3)')  # Rouge transparent
                        texts.append("❌")
                        hovertexts.append(f"<b>{d}</b><br>❌ Non calculable<br>Métadonnées manquantes")
                        patterns.append("/")  # Hachures
                
                # Graphique avec les 6 barres
                fig = go.Figure(data=[
                    go.Bar(
                        x=dims, 
                        y=vals, 
                        marker=dict(
                            color=colors,
                            line=dict(color='white', width=1)
                        ),
                        text=texts,
                        textposition='outside',
                        textfont=dict(size=14),
                        hovertext=hovertexts,
                        hoverinfo='text'
                    )
                ])
                
                # Ajouter des croix rouges pour les N/A
                annotations = []
                for i, (val, d) in enumerate(zip(vals, dims)):
                    if dama_score.get(d) is None:
                        annotations.append(
                            dict(
                                x=i,
                                y=val + 5,
                                text="<b>❌</b>",
                                showarrow=False,
                                font=dict(size=20, color='red')
                            )
                        )
                
                fig.update_layout(
                    height=220, 
                    template="plotly_dark", 
                    showlegend=False,
                    yaxis=dict(
                        title="Score (%)",
                        range=[0, 110]
                    ),
                    xaxis_title="Dimensions DAMA (6 dimensions ISO 8000)",
                    annotations=annotations
                )
                st.plotly_chart(fig, use_container_width=True, key=f"dama_chart_{attr}")
                
                # Légende explicative CLAIRE
                col_legend1, col_legend2 = st.columns(2)
                with col_legend1:
                    st.caption("🔵 **Calculé** : Formule appliquée sur données")
                with col_legend2:
                    st.caption("❌ **Non calculable** : Métadonnées manquantes")
                
                # Afficher formule détaillée
                with st.expander(f"🔍 Détail calcul {attr}", expanded=False):
                    st.markdown("**Formule score global :**")
                    st.code(f"""
Score DAMA = Moyenne des dimensions CALCULABLES uniquement

Complétude     : {"✅ " + f"{dama_score.get('completeness', 0)*100:.1f}%" if dama_score.get('completeness') is not None else "❌ N/A"}
Cohérence      : {"✅ " + f"{dama_score.get('consistency', 0)*100:.1f}%" if dama_score.get('consistency') is not None else "❌ N/A (règles manquantes)"}
Exactitude     : {"✅ " + f"{dama_score.get('accuracy', 0)*100:.1f}%" if dama_score.get('accuracy') is not None else "❌ N/A (ground truth manquant)"}
Fraîcheur      : {"✅ " + f"{dama_score.get('timeliness', 0)*100:.1f}%" if dama_score.get('timeliness') is not None else "❌ N/A (règle fraîcheur manquante)"}
Validité       : {"✅ " + f"{dama_score.get('validity', 0)*100:.1f}%" if dama_score.get('validity') is not None else "❌ N/A (domaine manquant)"}
Unicité        : {"✅ " + f"{dama_score.get('uniqueness', 0)*100:.1f}%" if dama_score.get('uniqueness') is not None else "❌ N/A"}

= ({formule}) / {nb_calculables} = {score_global:.1%}
                    """, language="text")
        
        st.markdown("---")
        
        # Problèmes masqués
        if comparaison['problemes_masques']:
            st.subheader("🔍 Problèmes Masqués par DAMA")
            
            for pb in comparaison['problemes_masques']:
                st.warning(f"**{pb['attribut']}** : {pb['explication']}")
        
        st.markdown("---")
        
        # Gains méthodologiques
        st.subheader("🎯 Gains Méthodologiques")
        
        for gain in comparaison['gains'][:5]:  # Top 5
            with st.expander(f"✨ {gain['categorie']}"):
                st.write(f"**DAMA :** {gain.get('methode_dama', 'N/A')}")
                st.write(f"**Probabiliste :** {gain.get('methode_probabiliste', gain.get('gain', 'N/A'))}")
                st.success(f"**Impact :** {gain.get('impact_operationnel', gain.get('impact', 'N/A'))}")
        
        # Bouton commentaire IA synthèse
        if st.button("💬 Synthétiser avec Claude", key="explain_dama", help="Synthèse comparative DAMA vs Probabiliste"):
            if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                with st.spinner("Claude synthétise la comparaison..."):
                    # Calculer DAMA moyen
                    dama_scores = [score['score_global'] for score in comparaison['dama_scores'].values()]
                    dama_avg = sum(dama_scores) / len(dama_scores) if dama_scores else 0
                    
                    data_for_ai = {
                        "dama_avg": dama_avg,
                        "masked_count": len(comparaison.get('problemes_masques', [])),
                        "gains": comparaison['gains'][:5],
                        "attributs_analyzed": len(comparaison['dama_scores'])
                    }
                    
                    comment = generate_ai_comment("dama", data_for_ai, st.session_state.anthropic_api_key)
                    st.info(f"💬 **Synthèse Claude** :\n\n{comment}")
            else:
                st.warning("⚠️ Configure ta clé API Claude dans la sidebar")
    
    # ========================================================================
    # TAB 6 : ÉLICITATION IA (VRAIE LLM)
    # ========================================================================
    with tab7:
        st.header("💬 Élicitation Assistée par IA")
        
        st.markdown("""
        ### 🎯 Objectif : Réduire 240h d'élicitation à 12 minutes
        
        Le **Compagnon IA Claude** dialogue avec toi pour affiner les pondérations AHP de manière progressive.
        Au lieu de deviner les poids, l'IA pose des questions ciblées et ajuste automatiquement.
        
        ⚡ **Cette démo utilise l'API Claude d'Anthropic pour un dialogue réel et adaptatif.**
        """)
        
        # Vérifier clé API
        if 'anthropic_api_key' not in st.session_state or not st.session_state.anthropic_api_key:
            st.error("🔑 **Clé API Claude manquante**")
            st.info("Configure ta clé API Claude dans la sidebar pour activer cette fonctionnalité.")
            st.stop()
        
        # Initialiser client Anthropic
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
        except Exception as e:
            st.error(f"❌ Erreur initialisation API : {str(e)}")
            st.stop()
        
        # Initialiser chat history
        if 'elicitation_messages' not in st.session_state:
            st.session_state.elicitation_messages = []
            st.session_state.current_usage = "Paie réglementaire"
            st.session_state.elicited_weights = {}
            st.session_state.elicitation_context = {
                "usage": "Paie réglementaire",
                "dimensions_discutees": [],
                "etape": "initiale"
            }
        
        # Système prompt pour Claude
        SYSTEM_PROMPT = """Tu es un expert en Data Quality et élicitation de préférences AHP (Analytic Hierarchy Process).

Ton rôle est d'aider l'utilisateur à définir les pondérations optimales pour 4 dimensions de qualité données :

**4 Dimensions** :
- [DB] Database : Contraintes structurelles (types, formats, schéma)
- [DP] Data Processing : Transformations ETL, calculs dérivés
- [BR] Business Rules : Règles métier, cohérence sémantique
- [UP] Usage-fit : Adéquation au contexte d'utilisation

**Contexte actuel** :
- Usage métier : "{usage}"
- Objectif : Définir w_DB, w_DP, w_BR, w_UP tels que leur somme = 100%

**Ton approche** :
1. Pose des questions par comparaisons pairées (A vs B : lequel est plus important ?)
2. Propose des justifications concrètes liées au contexte métier
3. Ajuste progressivement les pondérations selon les réponses
4. Suggère des valeurs Beta concrètes quand pertinent
5. Reste concis (2-3 phrases max par message)
6. Utilise des emojis pour clarté (🎯, ✅, ⚖️, etc.)

**Règles** :
- Ne jamais proposer de pondérations qui ne somment pas à 100%
- Toujours expliquer POURQUOI une dimension est importante dans ce contexte
- Si l'utilisateur hésite, proposer des exemples concrets
- Quand les 4 pondérations sont définies, résumer et demander validation

**Format réponse** :
- Questions courtes et directes
- Maximum 3 phrases
- Éviter le jargon technique sauf si nécessaire
"""
        
        # Afficher historique chat
        st.markdown("### 💭 Conversation avec Claude")
        
        chat_container = st.container()
        
        with chat_container:
            for msg in st.session_state.elicitation_messages:
                if msg["role"] == "assistant":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(msg["content"])
                        st.caption(f"_{msg['timestamp'].strftime('%H:%M:%S')}_")
                else:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(msg["content"])
                        st.caption(f"_{msg['timestamp'].strftime('%H:%M:%S')}_")
        
        # Zone input utilisateur
        st.markdown("---")
        
        # Si pas encore de conversation, démarrer
        if len(st.session_state.elicitation_messages) == 0:
            if st.button("🚀 Démarrer l'élicitation", type="primary", use_container_width=True):
                with st.spinner("Claude réfléchit..."):
                    try:
                        # Premier message de Claude
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=500,
                            system=SYSTEM_PROMPT.format(usage=st.session_state.current_usage),
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"Bonjour ! Je veux définir les pondérations AHP pour l'usage '{st.session_state.current_usage}'. Peux-tu m'aider en me posant des questions ?"
                                }
                            ]
                        )
                        
                        assistant_response = message.content[0].text
                        
                        st.session_state.elicitation_messages.append({
                            "role": "assistant",
                            "content": assistant_response,
                            "timestamp": datetime.now()
                        })
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur API Claude : {str(e)}")
        
        # Zone réponse utilisateur
        if len(st.session_state.elicitation_messages) > 0:
            user_input = st.text_input(
                "Ta réponse :",
                key="elicitation_input",
                placeholder="Ex: Je pense que [DB] est plus important car la paie nécessite une structure stricte..."
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                send_button = st.button("📤 Envoyer", type="primary", use_container_width=True)
            
            with col2:
                reset_button = st.button("🔄 Reset", use_container_width=True)
            
            if reset_button:
                st.session_state.elicitation_messages = []
                st.session_state.elicited_weights = {}
                st.rerun()
            
            if send_button and user_input:
                # Ajouter message utilisateur
                st.session_state.elicitation_messages.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now()
                })
                
                with st.spinner("Claude réfléchit..."):
                    try:
                        # Construire historique conversation
                        messages = []
                        for msg in st.session_state.elicitation_messages:
                            messages.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
                        
                        # Appeler API Claude
                        response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=500,
                            system=SYSTEM_PROMPT.format(usage=st.session_state.current_usage),
                            messages=messages
                        )
                        
                        assistant_response = response.content[0].text
                        
                        # Ajouter réponse Claude
                        st.session_state.elicitation_messages.append({
                            "role": "assistant",
                            "content": assistant_response,
                            "timestamp": datetime.now()
                        })
                        
                        # Tenter d'extraire pondérations du texte
                        import re
                        
                        # Pattern pour détecter pondérations
                        patterns = [
                            r'w_DB[:\s=]+(\d+)%',
                            r'w_DP[:\s=]+(\d+)%',
                            r'w_BR[:\s=]+(\d+)%',
                            r'w_UP[:\s=]+(\d+)%',
                            r'\[?DB\]?[:\s]+(\d+)%',
                            r'\[?DP\]?[:\s]+(\d+)%',
                            r'\[?BR\]?[:\s]+(\d+)%',
                            r'\[?UP\]?[:\s]+(\d+)%'
                        ]
                        
                        weights_found = {}
                        for pattern in patterns:
                            matches = re.findall(pattern, assistant_response, re.IGNORECASE)
                            if matches:
                                if 'DB' in pattern.upper():
                                    weights_found['w_DB'] = int(matches[0]) / 100
                                elif 'DP' in pattern.upper():
                                    weights_found['w_DP'] = int(matches[0]) / 100
                                elif 'BR' in pattern.upper():
                                    weights_found['w_BR'] = int(matches[0]) / 100
                                elif 'UP' in pattern.upper():
                                    weights_found['w_UP'] = int(matches[0]) / 100
                        
                        # Si 4 pondérations trouvées, sauvegarder
                        if len(weights_found) == 4:
                            st.session_state.elicited_weights[st.session_state.current_usage] = weights_found
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erreur API Claude : {str(e)}")
        
        # Afficher pondérations élicitées
        if st.session_state.elicited_weights:
            st.markdown("---")
            st.markdown("### 📊 Pondérations élicitées")
            
            for usage, weights in st.session_state.elicited_weights.items():
                st.markdown(f"**{usage}**")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("DB", f"{weights.get('w_DB', 0):.0%}")
                col2.metric("DP", f"{weights.get('w_DP', 0):.0%}")
                col3.metric("BR", f"{weights.get('w_BR', 0):.0%}")
                col4.metric("UP", f"{weights.get('w_UP', 0):.0%}")
                
                total = sum(weights.values())
                if abs(total - 1.0) < 0.01:
                    col5.success(f"✅ {total:.0%}")
                else:
                    col5.warning(f"⚠️ {total:.0%}")
                
                # Bouton appliquer
                if st.button(f"✅ Appliquer ces pondérations", key=f"apply_{usage}"):
                    # Ajouter à custom_usages ou custom_weights
                    if 'custom_weights' not in st.session_state:
                        st.session_state.custom_weights = {}
                    
                    st.session_state.custom_weights[usage] = weights
                    st.success(f"✅ Pondérations appliquées ! Tu peux maintenant relancer l'analyse.")
        
        # Stats conversation
        if st.session_state.elicitation_messages:
            st.markdown("---")
            nb_messages = len(st.session_state.elicitation_messages)
            duree = (st.session_state.elicitation_messages[-1]['timestamp'] - 
                    st.session_state.elicitation_messages[0]['timestamp']).seconds // 60
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Messages échangés", nb_messages)
            col2.metric("Durée conversation", f"{duree} min" if duree > 0 else "< 1 min")
            col3.metric("Gain vs manuel", f"{240 // max(duree, 1)}×" if duree > 0 else "480×")
    
    # ========================================================================
    # TAB 7 : SURVEILLANCE
    # ========================================================================
    with tab8:
        st.header("🔔 Surveillance Proactive")
        
        st.markdown("""
        ### 🎯 Objectif : Détecter incidents en 9h au lieu de 3 semaines
        
        Le système surveille en continu les vecteurs 4D et **alerte dès qu'une dégradation est détectée**.
        """)
        
        # Simulation alerte
        st.markdown("---")
        st.markdown("### 📧 Simulation Alerte Email")
        
        # Email mockup - version épurée
        st.markdown("""
        <div style="background: #ffffff; padding: 1.5rem; border-radius: 8px; border: 2px solid #E57373; border-left: 4px solid #ef4444;">
            <p style="color: #000000; margin: 0; font-size: 0.9rem;"><strong>De:</strong> monitoring@framework-dq.ai</p>
            <p style="color: #000000; margin: 0; font-size: 0.9rem;"><strong>À:</strong> data-steward@entreprise.fr</p>
            <p style="color: #000000; margin: 0; font-size: 0.9rem;"><strong>Date:</strong> 13/01/2025 08:30</p>
            <p style="color: #000000; margin: 0; font-size: 0.9rem;"><strong>Objet:</strong> 🚨 ALERTE CRITIQUE - Dégradation qualité détectée</p>
            <hr style="border-color: #d2d2d7; margin: 1rem 0;">
            <h3 style="color: #ef4444; margin-top: 0.5rem; font-size: 1.3rem;">⚠️ ALERTE CRITIQUE</h3>
            <p style="color: #000000; margin: 0.3rem 0;"><strong>Attribut:</strong> Ancienneté</p>
            <p style="color: #000000; margin: 0.3rem 0;"><strong>Usage:</strong> Paie réglementaire</p>
            <p style="color: #000000; margin: 0.3rem 0;"><strong>Dimension affectée:</strong> [DP] Data Processing</p>
            <p style="color: #000000; margin: 0.3rem 0;"><strong>Risque:</strong> <span style="color: #ef4444; font-weight: 600;">46.3% → 62.3%</span> (+16 points)</p>
            <p style="color: #000000; margin: 0.3rem 0;"><strong>Sévérité:</strong> <span style="background: #FFEBEE; color: #ef4444; padding: 4px 12px; border-radius: 4px; border: 1px solid #E57373; font-weight: 600;">CRITIQUE</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📅 Timeline Incident")
        
        # Timeline avec étapes
        timeline_data = [
            {
                "time": "12/01/2025 23:15",
                "event": "🔧 Déploiement ETL v2.8.2",
                "details": "Commit abc123def - Modification parser Ancienneté",
                "status": "info"
            },
            {
                "time": "13/01/2025 00:30",
                "event": "📊 Calcul batch quotidien",
                "details": "141/687 erreurs parsing détectées (+12% vs baseline)",
                "status": "warning"
            },
            {
                "time": "13/01/2025 03:00",
                "event": "🤖 Analyse propagation risque",
                "details": "P_DP: 2.0% → 28.5% | Score Paie: 46.3% → 62.3%",
                "status": "warning"
            },
            {
                "time": "13/01/2025 08:30",
                "event": "🚨 Alerte envoyée",
                "details": "Email + Slack #data-quality | Priorité: CRITIQUE",
                "status": "error"
            },
            {
                "time": "13/01/2025 09:06",
                "event": "✅ Action corrective",
                "details": "Rollback ETL v2.8.2 → v2.8.1 | Score revenu 46.3%",
                "status": "success"
            }
        ]
        
        for item in timeline_data:
            if item["status"] == "error":
                st.error(f"**{item['time']}** - {item['event']}\n\n{item['details']}")
            elif item["status"] == "warning":
                st.warning(f"**{item['time']}** - {item['event']}\n\n{item['details']}")
            elif item["status"] == "success":
                st.success(f"**{item['time']}** - {item['event']}\n\n{item['details']}")
            else:
                st.info(f"**{item['time']}** - {item['event']}\n\n{item['details']}")
        
        st.markdown("---")
        st.markdown("### 🔍 Analyse Causale")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Cause racine identifiée**")
            st.code("""
# ETL v2.8.2 - parser.py
# Commit abc123def

# AVANT (v2.8.1) ✅
anciennete = float(value.replace(',', '.'))

# APRÈS (v2.8.2) ❌
anciennete = float(value)  # Bug: virgule non gérée
            """, language="python")
        
        with col2:
            st.markdown("**Impact mesuré**")
            st.metric("Erreurs parsing", "141 / 687", delta="+12%", delta_color="inverse")
            st.metric("P_DP dégradé", "28.5%", delta="+26.5 points", delta_color="inverse")
            st.metric("Score Paie", "62.3%", delta="+16 points", delta_color="inverse")
            st.metric("Temps détection", "9h", delta="-3 sem vs DAMA", delta_color="normal")
        
        st.markdown("---")
        st.markdown("### 🛠️ Actions disponibles")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Rollback ETL v2.8.1", type="primary", use_container_width=True):
                with st.spinner("Rollback en cours..."):
                    time.sleep(2)
                st.success("✅ Rollback effectué ! Score revenu à 46.3%")
        
        with col2:
            if st.button("📊 Voir logs complets", use_container_width=True):
                st.code("""
[2025-01-13 00:30:15] INFO: Batch ETL started
[2025-01-13 00:30:16] ERROR: ValueError in parse_anciennete()
  Line 342: could not convert string to float: '7,21'
[2025-01-13 00:30:16] ERROR: 141 records failed
[2025-01-13 00:30:17] WARNING: P_DP degraded: 0.020 → 0.285
[2025-01-13 00:30:18] CRITICAL: Risk threshold exceeded (>60%)
                """, language="log")
        
        with col3:
            if st.button("📧 Notifier équipe", use_container_width=True):
                st.info("📧 Email envoyé à l'équipe data + développeurs ETL")
        
        st.markdown("---")
        st.markdown("### 📈 Graphique Évolution Risque")
        
        # Graphique simulation
        dates = pd.date_range(start='2025-01-10', end='2025-01-14', freq='6H')
        risk_before = [46.3] * 10
        risk_spike = [46.3, 48.2, 52.1, 58.7, 62.3, 62.1, 61.8, 46.5, 46.3]
        risk_all = risk_before + risk_spike
        
        fig_surveillance = go.Figure()
        
        fig_surveillance.add_trace(go.Scatter(
            x=dates[:len(risk_all)],
            y=risk_all,
            mode='lines+markers',
            name='Score Risque Paie',
            line=dict(color='#ff4444', width=3),
            marker=dict(size=8)
        ))
        
        # Ligne seuil critique
        fig_surveillance.add_hline(
            y=60,
            line_dash="dash",
            line_color="red",
            annotation_text="Seuil CRITIQUE (60%)"
        )
        
        # Zone incident
        fig_surveillance.add_vrect(
            x0="2025-01-12 23:00",
            x1="2025-01-13 09:00",
            fillcolor="red",
            opacity=0.1,
            annotation_text="Incident ETL",
            annotation_position="top left"
        )
        
        fig_surveillance.update_layout(
            title="Surveillance Continue - Score Risque 'Ancienneté × Paie'",
            xaxis_title="Date",
            yaxis_title="Score Risque (%)",
            height=400,
            template="plotly_dark"
        )
        
        st.plotly_chart(fig_surveillance, use_container_width=True, key="surveillance_chart")
        
        st.markdown("---")
        st.success("Détection 9h vs 3 semaines | -79% faux positifs")
    
    # ========================================================================
    # TAB 8 : RESTITUTION ADAPTATIVE
    # ========================================================================
    with tab9:
        st.header("📋 Restitution Adaptative")
        
        st.markdown("""
        ### 🎯 Rapport personnalisé selon TON profil
        
        Que tu sois **CFO**, **Data Engineer**, **DRH**, **Auditeur** ou autre, 
        **Claude génère un rapport adapté** à tes besoins spécifiques.
        """)
        
        # Initialiser état session
        if 'restitution_phase' not in st.session_state:
            st.session_state.restitution_phase = "discovery"
        if 'restitution_history' not in st.session_state:
            st.session_state.restitution_history = []
        if 'profil_utilisateur' not in st.session_state:
            st.session_state.profil_utilisateur = None
        if 'rapport_genere' not in st.session_state:
            st.session_state.rapport_genere = None
        
        # RÉCUPÉRER VRAIES DONNÉES DEPUIS L'ANALYSE
        if 'results' not in st.session_state or st.session_state.results is None:
            st.warning("⚠️ Aucune analyse disponible. Lance d'abord une analyse dans l'onglet Dashboard.")
            st.stop()
        
        results = st.session_state.results
        
        # Utiliser les top_priorities qui contient déjà tout calculé
        if not results.get('top_priorities') or len(results['top_priorities']) == 0:
            st.warning("⚠️ Aucune priorité détectée dans l'analyse.")
            st.stop()
        
        # Prendre la priorité #1 (plus haut risque)
        top_priority = results['top_priorities'][0]
        
        attribut_critique = top_priority['attribut']
        usage_critique = top_priority['usage']
        risque_pourcent = top_priority['score'] * 100
        impact_records = top_priority['records_affected']
        impact_financier_mois = top_priority['impact_mensuel']
        
        # Récupérer vecteurs 4D de cet attribut
        vecteurs_bruts = results['vecteurs_4d'].get(attribut_critique, {})
        
        # SÉCURITÉ : Filtrer UNIQUEMENT les 4 dimensions et convertir en float
        vecteurs_critique = {}
        for dim in ['P_DB', 'P_DP', 'P_BR', 'P_UP']:
            val = vecteurs_bruts.get(dim, 0.0)
            try:
                vecteurs_critique[dim] = float(val)
            except (ValueError, TypeError):
                # Si conversion échoue (ex: 'HIGH'), mettre 0.0
                vecteurs_critique[dim] = 0.0
        
        # Identifier dimension la plus critique (celle avec le plus haut %)
        if vecteurs_critique and any(v > 0 for v in vecteurs_critique.values()):
            dim_max = max(vecteurs_critique.keys(), key=lambda k: vecteurs_critique[k])
        else:
            dim_max = 'P_DB'  # Défaut si toutes valeurs nulles
        
        # Récupérer total records
        total_records = len(st.session_state.df) if 'df' in st.session_state else 0
        
        # Récupérer les pondérations pour cet usage
        weights_usage = results['weights'].get(usage_critique, {
            'w_DB': 0.25,
            'w_DP': 0.25,
            'w_BR': 0.25,
            'w_UP': 0.25
        })
        
        # Construire données incident RÉELLES
        incident_data = {
            "attribut_critique": attribut_critique,
            "usage_critique": usage_critique,
            "risque_pourcent": round(risque_pourcent, 1),
            "severite": top_priority['severite'],
            "impact_records": impact_records,
            "total_records": total_records,
            "impact_financier_mois": impact_financier_mois,
            "vecteurs": vecteurs_critique,
            "dimension_critique": dim_max,
            "pondérations": weights_usage,
            "actions_recommandees": top_priority.get('actions', [])
        }
        
        # ========================================================================
        # PHASE 1 : DÉCOUVERTE (Dialogue intelligent)
        # ========================================================================
        if st.session_state.restitution_phase == "discovery":
            
            st.markdown("---")
            st.markdown("### 💬 Dialogue avec Claude")
            
            # Message initial si historique vide
            if len(st.session_state.restitution_history) == 0:
                initial_msg = f"""**Attribut** : {incident_data['attribut_critique']}
**Risque** : {incident_data['risque_pourcent']}% - {incident_data['severite']}
**Records** : {incident_data['impact_records']}/{incident_data['total_records']}

Ton rôle et besoins ?"""
                
                st.session_state.restitution_history.append({
                    "role": "assistant",
                    "content": initial_msg
                })
            
            # Afficher historique dialogue
            for msg in st.session_state.restitution_history:
                if msg["role"] == "assistant":
                    st.info(f"**🤖 Claude** : {msg['content']}")
                else:
                    st.success(f"**👤 Toi** : {msg['content']}")
            
            # Input utilisateur
            user_input = st.text_area(
                "Ta réponse :",
                placeholder="Ex: Je suis CFO, je veux savoir l'impact P&L et si je dois valider le budget de correction...",
                height=100,
                key="restitution_input"
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("➡️ Envoyer", type="primary", use_container_width=True):
                    if user_input and user_input.strip():
                        # Ajouter à historique
                        st.session_state.restitution_history.append({
                            "role": "user",
                            "content": user_input
                        })
                        
                        # Appeler Claude pour analyser besoin
                        if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                            with st.spinner("🤖 Claude analyse ton besoin..."):
                                try:
                                    client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
                                    
                                    # Prompt analyse besoin
                                    prompt_analyse = f"""Analyse l'échange avec un utilisateur qui veut un rapport Data Quality personnalisé.

**HISTORIQUE DIALOGUE** :
{json.dumps(st.session_state.restitution_history, indent=2, ensure_ascii=False)}

**INCIDENT À REPORTER** :
{json.dumps(incident_data, indent=2)}

**DÉTECTE ET RETOURNE JSON** :

{{
  "role": "Rôle précis (CFO, Data Engineer, DRH, Auditeur, Manager...)",
  "confiance": 0.0-1.0,
  "besoins_specifiques": [
    "Liste des éléments spécifiques que l'utilisateur veut voir",
    "Ex: Impact P&L mensuel, Root cause technique, Communication CSE..."
  ],
  "format": "email|rapport|dashboard|presentation|autre",
  "ton": "executif|technique|pedagogique|formel|autre",
  "contraintes": "Deadline, longueur, autres contraintes mentionnées",
  "question_manquante": "Question à poser si confiance < 0.8 (ou null si confiance OK)"
}}

**RÈGLES** :
- Si confiance >= 0.8 : question_manquante = null
- Si confiance < 0.8 : poser UNE question précise pour clarifier
- Besoins spécifiques = liste concrète d'éléments à inclure dans le rapport
- Format = type de document attendu
- Ton = style rédactionnel adapté

Réponds UNIQUEMENT avec le JSON, rien d'autre."""

                                    response = client.messages.create(
                                        model="claude-sonnet-4-20250514",
                                        max_tokens=1000,
                                        messages=[{"role": "user", "content": prompt_analyse}]
                                    )
                                    
                                    # Parser JSON
                                    json_text = response.content[0].text.strip()
                                    if "```json" in json_text:
                                        json_text = json_text.split("```json")[1].split("```")[0].strip()
                                    elif "```" in json_text:
                                        json_text = json_text.split("```")[1].split("```")[0].strip()
                                    
                                    profil_detecte = json.loads(json_text)
                                    
                                    # Vérifier confiance
                                    if profil_detecte.get('confiance', 0) >= 0.8:
                                        # Besoin clarifié → Passer à génération
                                        st.session_state.profil_utilisateur = profil_detecte
                                        st.session_state.restitution_phase = "confirmation"
                                        st.rerun()
                                    else:
                                        # Poser question de suivi
                                        question_suivi = profil_detecte.get('question_manquante', 
                                            "Peux-tu préciser un peu plus ce qui t'intéresse ?")
                                        st.session_state.restitution_history.append({
                                            "role": "assistant",
                                            "content": question_suivi
                                        })
                                        st.rerun()
                                
                                except Exception as e:
                                    st.error(f"⚠️ Erreur analyse : {str(e)}")
                        else:
                            st.error("⚠️ Configure ta clé API Claude dans la sidebar pour utiliser cette fonctionnalité")
                    else:
                        st.warning("⚠️ Écris quelque chose d'abord !")
            
            with col2:
                if st.button("🔄 Recommencer", use_container_width=True):
                    st.session_state.restitution_phase = "discovery"
                    st.session_state.restitution_history = []
                    st.session_state.profil_utilisateur = None
                    st.session_state.rapport_genere = None
                    st.rerun()
        
        # ========================================================================
        # PHASE 2 : CONFIRMATION
        # ========================================================================
        elif st.session_state.restitution_phase == "confirmation":
            
            profil = st.session_state.profil_utilisateur
            
            st.markdown("---")
            st.success(f"✅ **Profil détecté** : {profil.get('role', 'Non défini')}")
            st.info(f"🎯 **Confiance** : {int(profil.get('confiance', 0) * 100)}%")
            
            st.markdown("### 📋 Contenu du rapport personnalisé")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**📊 Base commune (tous profils)** :")
                st.markdown(f"""
                - **Incident** : {incident_data['attribut_critique']}
                - **Risque** : {incident_data['risque_pourcent']}% 🚨 CRITIQUE
                - **Records affectés** : {incident_data['impact_records']}
                - **Impact** : {incident_data['impact_financier_mois']:,}€/mois
                """)
            
            with col2:
                st.markdown(f"**✨ Spécifique {profil.get('role')}** :")
                for item in profil.get('besoins_specifiques', []):
                    st.markdown(f"- {item}")
            
            st.markdown("---")
            
            # Afficher format et ton
            col_f, col_t = st.columns(2)
            with col_f:
                st.metric("Format", profil.get('format', 'Rapport').capitalize())
            with col_t:
                st.metric("Ton", profil.get('ton', 'Professionnel').capitalize())
            
            if profil.get('contraintes'):
                st.warning(f"⚠️ **Contraintes** : {profil['contraintes']}")
            
            st.markdown("---")
            
            # Boutons action
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🚀 Générer Rapport Personnalisé", type="primary", use_container_width=True):
                    if 'anthropic_api_key' in st.session_state and st.session_state.anthropic_api_key:
                        with st.spinner("🤖 Claude génère ton rapport sur-mesure... (10-20 sec)"):
                            try:
                                client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
                                
                                # Prompt génération rapport avec structure graphique
                                prompt_rapport = f"""Tu es un expert Data Quality qui génère un rapport personnalisé **en français simple et accessible**.

**PROFIL UTILISATEUR** :
- Rôle : {profil['role']}
- Besoins spécifiques : {', '.join(profil['besoins_specifiques'])}
- Format : {profil['format']}
- Ton : {profil['ton']}
- Contraintes : {profil.get('contraintes', 'Aucune')}

**DONNÉES RÉELLES À UTILISER** :
{json.dumps(incident_data, indent=2, ensure_ascii=False)}

**RÈGLES CRITIQUES** :
⚠️ FRANÇAIS SIMPLE (niveau lycéen)
⚠️ Explications AVANT chiffres
⚠️ VRAIES données uniquement (pas de simulation)
⚠️ PAS de timeline dans le rapport
⚠️ Identifier la cause racine depuis les données (pas d'invention)

════════════════════════════════════════════════════════════════════════
STRUCTURE OBLIGATOIRE DU RAPPORT
════════════════════════════════════════════════════════════════════════

# RAPPORT QUALITÉ DONNÉES
Incident : {incident_data['attribut_critique']} - {incident_data['risque_pourcent']}%
Date : [Date du jour]
Destinataire : {profil['role']}

╔═══════════════════════════════════════════════════════╗
║  PARTIE 1 : SYNTHÈSE EXÉCUTIVE                        ║
║  Pour décideurs pressés - Lecture : 2 minutes         ║
╚═══════════════════════════════════════════════════════╝

## 🚨 SITUATION EN UN COUP D'ŒIL

[GRAPHIQUE 1 : Jauge de risque - ASCII art]
Génère une jauge visuelle ASCII avec {incident_data['risque_pourcent']}%

Exemple :
```
NIVEAU DE RISQUE
████████████░░░░░░░░ 62.3%

🟢────────🟡────────🔴────────⚫
OK     Surveillé  Critique  Bloquant
                    ↑
                  VOUS ÊTES ICI
```

## 💡 L'ESSENTIEL EN 3 POINTS

1️⃣ **QU'EST-CE QUI S'EST PASSÉ ?**
[Explique l'incident en 2-3 phrases simples avec les vraies données]
- Bug identifié
- {incident_data['impact_records']} enregistrements affectés

2️⃣ **QUEL IMPACT ?**
[Explique l'impact avec les vraies données]
- {incident_data['vecteurs']['P_DP']*100:.0f}% des transformations défaillantes
- {incident_data['impact_financier_mois']:,}€/mois si non corrigé
- Process bloqués

3️⃣ **QUE FAIRE MAINTENANT ?**
[Action immédiate claire]
- Action : [Décris l'action prioritaire]
- Durée : [Temps estimé]
- Gain : Évite pertes financières

## 📊 QUALITÉ PAR DIMENSION

[GRAPHIQUE 2 : Radar 4D - ASCII art]
Génère un radar avec les vraies valeurs :
- DB : {incident_data['vecteurs']['P_DB']*100:.1f}%
- DP : {incident_data['vecteurs']['P_DP']*100:.1f}%
- BR : {incident_data['vecteurs']['P_BR']*100:.1f}%
- UP : {incident_data['vecteurs']['P_UP']*100:.1f}%

Exemple format :
```
        Traitements
           XX% 🔴
             ▲
             │
Structure ───┼─── Règles
  XX%        │     XX%
             │
             ▼
        Utilisabilité
           XX%
```

[GRAPHIQUE 3 : Barres horizontales]
Génère barres pour chaque dimension avec % de qualité (100 - P_dimension)

Exemple :
```
Structure (Base de données)
████████░░ XX.X% ✅ BON NIVEAU
[Explication 1 phrase]

Traitements (Transformations)  
███████░░░ XX.X% 🚨 ACTION URGENTE
[Explication 1 phrase]

Règles Métier (Cohérence)
█████████░ XX.X% ✅ EXCELLENT
[Explication 1 phrase]

Utilisabilité (Exploitabilité)
█████████░ XX.X% ✅ BON NIVEAU
[Explication 1 phrase]
```

🎯 DIMENSION CRITIQUE : [Identifier dimension avec plus haut risque]

## 💰 IMPACT FINANCIER

[GRAPHIQUE 4 : Comparaison coûts]
Génère comparaison visuelle ASCII :

```
Si on ne fait rien :
┌──────────────────────┐
│  XX,XXX € / mois     │ ← Pertes continues
│  XXX,XXX € / an      │
└──────────────────────┘

Solution proposée :
┌──────────┐
│ X,XXX €  │ ← Coût unique
└──────────┘

💡 ROI : Économie de XXX× le coût
```

## ✅ PLAN D'ACTION (3 PRIORITÉS)

Génère tableau structuré :

```
┌───────────┬──────────┬──────────────┬─────────────────┬──────────────┐
│ Priorité  │ Durée    │ Impact       │ Gain            │ Responsable  │
├───────────┼──────────┼──────────────┼─────────────────┼──────────────┤
│ 🔥 #1     │ XX       │ [Impact]     │ [Gain €]        │ [Équipe]     │
│ [Action]  │ URGENT   │              │                 │              │
├───────────┼──────────┼──────────────┼─────────────────┼──────────────┤
│ ⚙️ #2     │ XX       │ [Impact]     │ [Gain]          │ [Équipe]     │
│ [Action]  │          │              │                 │              │
├───────────┼──────────┼──────────────┼─────────────────┼──────────────┤
│ 🛡️ #3     │ XX       │ [Impact]     │ [Gain]          │ [Équipe]     │
│ [Action]  │          │              │                 │              │
└───────────┴──────────┴──────────────┴─────────────────┴──────────────┘
```

Puis détaille chaque action :

**🔥 ACTION 1 - CRITIQUE IMMÉDIATE**
Ce qu'il faut faire : [Description simple]
Temps nécessaire : [Durée]
Impact : [Impact concret]
Gain : [Gain chiffré ou qualitatif]
Responsable : [Équipe]

[Idem pour actions 2 et 3]

════════════════════════════════════════════════════════════════════════
   FIN SYNTHÈSE EXÉCUTIVE - Lecture : 2 minutes
   👇 Suite = Détails techniques (optionnel)
════════════════════════════════════════════════════════════════════════

╔═══════════════════════════════════════════════════════╗
║  PARTIE 2 : SOCLE DE BASE DÉTAILLÉ                   ║
║  (Commun à tous les profils)                          ║
║  Lecture : 5 minutes                                  ║
╚═══════════════════════════════════════════════════════╝

## 📊 SECTION 1 : PROBLÈMES QUALITÉ DÉTECTÉS

Pour chaque dimension, **TEXTE D'ABORD**, chiffres après.

**🗄️ BASE DE DONNÉES (Structure)**

[Explication en français simple - 2-3 phrases]
"[Décris ce qui se passe avec les vraies données]"

Chiffres techniques : {incident_data['vecteurs']['P_DB']*100:.1f}% de problèmes (marge ±3%)

**⚙️ TRANSFORMATIONS INFORMATIQUES (Traitements)**

[Si dimension critique, ajouter 🚨 ALERTE MAJEURE]
[Explication en français simple - 2-3 phrases]
"[Décris avec les vraies données]"

Chiffres techniques : {incident_data['vecteurs']['P_DP']*100:.1f}% de problèmes (marge ±3%)

[Optionnel : Schéma propagation si pertinent]

**📋 RÈGLES MÉTIER (Cohérence)**

[Explication en français simple]
"[Décris avec les vraies données]"

Chiffres techniques : {incident_data['vecteurs']['P_BR']*100:.1f}% de problèmes (marge ±3%)

**🎯 ADÉQUATION À L'USAGE (Utilisabilité)**

[Explication en français simple]
"[Décris avec les vraies données]"

Chiffres techniques : {incident_data['vecteurs']['P_UP']*100:.1f}% de problèmes (marge ±4%)

---

## ⚖️ SECTION 2 : IMPORTANCE DES DIMENSIONS

Usage analysé : [Nom usage métier]

[GRAPHIQUE 5 : Camembert pondérations - ASCII art]
Génère camembert avec vraies pondérations (à déduire du contexte ou demander)

Exemple :
```
       XX%
   Traitements
   ╱        ╲
  ╱          ╲
XX%            XX%
Structure   Règles
  ╲          ╱
   ╲        ╱
     XX%
Utilisabilité
```

**Pour cet usage, voici l'importance de chaque dimension :**

• **STRUCTURE (XX% d'importance)**
  [Explique pourquoi ce % avec usage métier]

• **TRAITEMENTS (XX% d'importance)**
  [Explique pourquoi - identifier si dimension critique]

• **RÈGLES MÉTIER (XX% d'importance)**
  [Explique pourquoi]

• **UTILISABILITÉ (XX% d'importance)**
  [Explique pourquoi]

**Justification :** [2-3 phrases expliquant la logique des pondérations]

---

## 🎯 SECTION 3 : PLAN D'ACTION DÉTAILLÉ

[Reprendre le tableau de la synthèse, puis détailler]

**🔥 ACTION 1 - CRITIQUE IMMÉDIATE**
[Détails comme dans synthèse]

**⚙️ ACTION 2 - CORRECTIF TECHNIQUE**
[Détails]

**🛡️ ACTION 3 - PRÉVENTION LONG TERME**
[Détails]

---

## 📈 SECTION 4 : QUALITÉ PAR DIMENSION (SANS AGRÉGATION)

⚠️ **ATTENTION** : Chaque dimension a son importance propre
❌ **PAS DE MOYENNE GLOBALE** calculée

[Génère 4 cartes visuelles séparées]

**🗄️ STRUCTURE BASE DE DONNÉES**
```
████████░░ XX.X%  ✅
```
[Explication accessible 2-3 phrases]
Chiffres : XX.X% de qualité (marge ±3%)

**⚙️ TRAITEMENTS INFORMATIQUES**
```
███████░░░ XX.X%  🚨
```
[Si critique : 🔴 ZONE ROUGE : ...]
[Explication + ACTION IMMÉDIATE REQUISE si pertinent]
Chiffres : XX.X% de qualité (marge ±3%)

**📋 RÈGLES MÉTIER**
```
█████████░ XX.X%  ✅
```
[Explication accessible]
Chiffres : XX.X% de qualité (marge ±3%)

**🎯 UTILISABILITÉ**
```
█████████░ XX.X%  ✅
```
[Explication accessible]
Chiffres : XX.X% de qualité (marge ±4%)

🎯 **DIMENSION NÉCESSITANT ACTION IMMÉDIATE** : [Identifier dimension critique]

╔═══════════════════════════════════════════════════════╗
║  PARTIE 3 : ÉLÉMENTS SPÉCIFIQUES PROFIL              ║
║  "{profil['role']}"                                   ║
║  Lecture : 3 minutes                                  ║
╚═══════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════
    ↓ SECTION PERSONNALISÉE POUR TON PROFIL ↓
════════════════════════════════════════════════════════

**Besoins spécifiques à traiter :**
{chr(10).join(['- ' + b for b in profil['besoins_specifiques']])}

**Instructions partie spécifique :**
- Français simple et accessible (comme parties 1 et 2)
- Adapter au profil : {profil['role']}
- Utiliser vraies données incident
- Créer sections pertinentes selon besoins
- Garder ton pédagogique

Exemples de sections possibles selon profil :
- Si process/opérationnel : Vue domaines, Process défaillants, Métriques suivi
- Si CFO/financier : Analyse ROI, Business case, Recommandation Go/NoGo
- Si technique : Root cause détaillée, Code défaillant, Scripts correction
- Si DRH/communication : Impact collaborateurs, Communication équipe, Timeline humaine

[Génère 3-5 sections pertinentes avec vraies données]

════════════════════════════════════════════════════════

**CONSIGNES FINALES** :
✅ Structure EXACTE ci-dessus
✅ Français niveau lycéen
✅ Graphiques ASCII art
✅ Explications AVANT chiffres
✅ Vraies données uniquement
✅ PAS de timeline
✅ PAS de moyenne globale
✅ Ton : {profil['ton']}
✅ Longueur : 1000-1500 mots

**GÉNÈRE LE RAPPORT MAINTENANT** en Markdown."""

                                response = client.messages.create(
                                    model="claude-sonnet-4-20250514",
                                    max_tokens=4000,
                                    messages=[{"role": "user", "content": prompt_rapport}]
                                )
                                
                                rapport = response.content[0].text
                                
                                st.session_state.rapport_genere = rapport
                                st.session_state.restitution_phase = "export"
                                st.rerun()
                            
                            except Exception as e:
                                st.error(f"⚠️ Erreur génération : {str(e)}")
                    else:
                        st.error("⚠️ Configure ta clé API Claude dans la sidebar")
            
            with col2:
                if st.button("↩️ Modifier profil", use_container_width=True):
                    st.session_state.restitution_phase = "discovery"
                    st.rerun()
        
        # ========================================================================
        # PHASE 3 : EXPORT
        # ========================================================================
        elif st.session_state.restitution_phase == "export":
            
            profil = st.session_state.profil_utilisateur
            rapport = st.session_state.rapport_genere
            
            st.markdown("---")
            st.success(f"✅ **Rapport généré pour** : {profil.get('role')}")
            
            st.markdown("### 📄 Ton Rapport Personnalisé")
            
            # Afficher rapport
            st.markdown(rapport)
            
            st.markdown("---")
            st.markdown("### 📥 Télécharger")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export Markdown
                md_bytes = rapport.encode('utf-8')
                st.download_button(
                    "📝 Markdown",
                    md_bytes,
                    f"rapport_{profil.get('role', 'custom').replace(' ', '_')}.md",
                    "text/markdown",
                    use_container_width=True
                )
            
            with col2:
                # Export TXT simple
                txt_bytes = rapport.encode('utf-8')
                st.download_button(
                    "📄 Texte",
                    txt_bytes,
                    f"rapport_{profil.get('role', 'custom').replace(' ', '_')}.txt",
                    "text/plain",
                    use_container_width=True
                )
            
            with col3:
                if st.button("🔄 Nouveau Rapport", use_container_width=True):
                    st.session_state.restitution_phase = "discovery"
                    st.session_state.restitution_history = []
                    st.session_state.profil_utilisateur = None
                    st.session_state.rapport_genere = None
                    st.rerun()
            
            st.markdown("---")
    
    # ========================================================================
    # TAB 9 : DÉTECTION ANOMALIES
    # ========================================================================
else:
    # MESSAGE ACCUEIL
    st.info("👈 **Upload TON dataset CSV/Excel dans la barre latérale pour commencer l'analyse !**")
    
    
    # Supprimer vidéo placeholder
    # st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
