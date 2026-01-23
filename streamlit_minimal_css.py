"""
streamlit_minimal_css.py
CSS minimaliste style Apple pour Framework Data Quality

Caractéristiques:
- Menus/Tabs : Fond NOIR avec texte BLANC
- Boutons : Fond bleu très clair (#E3F2FD) avec texte NOIR
- Fond général : BLANC
- Texte normal : NOIR (#000000)
- Texte secondaire : Gris (#6e6e73)
- Pas de dégradés, pas de couleurs fancy
- Style minimaliste et épuré

Usage:
    from streamlit_minimal_css import apply_minimal_css
    apply_minimal_css()
"""

import streamlit as st

def apply_minimal_css():
    """
    Applique un CSS minimaliste style Apple
    Sans dégradés, sans animations, épuré et propre
    """

    st.markdown('''
    <style>
    /* Import Police Apple-like */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Variables CSS */
    :root {
        /* Couleurs principales */
        --bg-white: #ffffff;
        --bg-light: #f5f5f7;
        --black: #000000;
        --text-black: #000000;
        --text-gray: #6e6e73;
        --button-blue: #E3F2FD;
        --border-gray: #d2d2d7;
        --hover-gray: #f5f5f7;
    }

    /* Base - Police et lissage */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Fond général BLANC */
    .stApp {
        background: var(--bg-white);
        color: var(--text-black);
    }

    /* Cacher éléments Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Titres - Texte NOIR */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-black);
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 2.5rem;
        font-weight: 700;
    }

    h2 {
        font-size: 2rem;
    }

    h3 {
        font-size: 1.5rem;
    }

    /* Paragraphes - Texte NOIR et GRIS */
    p, span, div {
        color: var(--text-black);
    }

    /* Texte secondaire - GRIS */
    [data-testid="stMarkdownContainer"] p:not(:first-child),
    .stMarkdown small {
        color: var(--text-gray);
    }

    /* ============================================
       TABS - Fond NOIR avec texte BLANC
       ============================================ */

    [data-testid="stTabs"] {
        background: var(--black);
        border-radius: 12px;
        padding: 0.5rem;
        margin-bottom: 2rem;
        border: none;
    }

    [data-testid="stTabs"] button {
        background: transparent;
        color: var(--bg-white);
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.9375rem;
        border-radius: 8px;
        transition: background 0.2s ease;
    }

    [data-testid="stTabs"] button:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        background: var(--bg-white);
        color: var(--black);
        font-weight: 600;
    }

    /* ============================================
       BOUTONS - Fond bleu clair avec texte NOIR
       ============================================ */

    .stButton > button {
        background: var(--button-blue);
        color: var(--text-black);
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.9375rem;
        transition: all 0.2s ease;
        box-shadow: none;
    }

    .stButton > button:hover {
        background: #BBDEFB;
        border-color: #90CAF9;
    }

    .stButton > button:active {
        transform: scale(0.98);
    }

    /* ============================================
       METRICS CARDS
       ============================================ */

    [data-testid="stMetric"] {
        background: var(--bg-white);
        border: 1px solid var(--border-gray);
        border-radius: 12px;
        padding: 1.25rem;
        transition: border-color 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--text-gray);
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-gray);
        font-size: 0.8125rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="stMetricValue"] {
        color: var(--text-black);
        font-size: 2rem;
        font-weight: 600;
    }

    /* ============================================
       DATAFRAMES
       ============================================ */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        overflow: hidden;
    }

    [data-testid="stDataFrame"] thead tr {
        background: var(--bg-light);
    }

    [data-testid="stDataFrame"] thead th {
        color: var(--text-black) !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.875rem 1rem !important;
        border-bottom: 1px solid var(--border-gray) !important;
    }

    [data-testid="stDataFrame"] tbody tr {
        border-bottom: 1px solid var(--border-gray);
        transition: background 0.15s ease;
    }

    [data-testid="stDataFrame"] tbody tr:hover {
        background: var(--hover-gray);
    }

    [data-testid="stDataFrame"] tbody td {
        color: var(--text-black) !important;
        padding: 0.75rem 1rem !important;
    }

    /* ============================================
       EXPANDERS
       ============================================ */

    [data-testid="stExpander"] {
        background: var(--bg-white);
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        transition: border-color 0.2s ease;
    }

    [data-testid="stExpander"]:hover {
        border-color: var(--text-gray);
    }

    [data-testid="stExpander"] summary {
        color: var(--text-black);
        font-weight: 500;
        padding: 1rem 1.25rem;
    }

    [data-testid="stExpander"] summary:hover {
        background: var(--hover-gray);
    }

    /* ============================================
       ALERTS
       ============================================ */

    [data-testid="stAlert"] {
        border-radius: 8px;
        border: 1px solid;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }

    /* Info - Bleu */
    [data-testid="stAlert"][data-baseweb="notification-info"] {
        background: #E3F2FD;
        border-color: #90CAF9;
        color: var(--text-black);
    }

    /* Success - Vert */
    [data-testid="stAlert"][data-baseweb="notification-success"] {
        background: #E8F5E9;
        border-color: #81C784;
        color: var(--text-black);
    }

    /* Warning - Orange */
    [data-testid="stAlert"][data-baseweb="notification-warning"] {
        background: #FFF3E0;
        border-color: #FFB74D;
        color: var(--text-black);
    }

    /* Error - Rouge */
    [data-testid="stAlert"][data-baseweb="notification-error"] {
        background: #FFEBEE;
        border-color: #E57373;
        color: var(--text-black);
    }

    /* ============================================
       FILE UPLOADER
       ============================================ */

    [data-testid="stFileUploader"] {
        background: var(--bg-light);
        border: 2px dashed var(--border-gray);
        border-radius: 12px;
        padding: 2rem;
        transition: border-color 0.2s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--text-gray);
    }

    /* ============================================
       SELECT BOXES & INPUTS
       ============================================ */

    [data-baseweb="select"],
    [data-baseweb="input"] {
        background: var(--bg-white) !important;
        border: 1px solid var(--border-gray) !important;
        border-radius: 8px !important;
        transition: border-color 0.2s ease !important;
    }

    [data-baseweb="select"]:hover,
    [data-baseweb="input"]:hover,
    [data-baseweb="select"]:focus,
    [data-baseweb="input"]:focus {
        border-color: var(--text-gray) !important;
    }

    /* ============================================
       SIDEBAR
       ============================================ */

    [data-testid="stSidebar"] {
        background: var(--bg-light);
        border-right: 1px solid var(--border-gray);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--text-black);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-black);
    }

    /* ============================================
       CODE BLOCKS
       ============================================ */

    code {
        background: var(--bg-light) !important;
        color: var(--text-black) !important;
        border: 1px solid var(--border-gray) !important;
        border-radius: 4px !important;
        padding: 0.2rem 0.4rem !important;
        font-size: 0.875rem !important;
        font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace !important;
    }

    pre {
        background: var(--bg-light) !important;
        border: 1px solid var(--border-gray) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    /* ============================================
       PROGRESS BAR
       ============================================ */

    .stProgress > div > div {
        background: var(--text-black);
        border-radius: 8px;
        height: 8px;
    }

    /* ============================================
       SCROLLBAR
       ============================================ */

    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-light);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-gray);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-gray);
    }

    /* ============================================
       PLOTLY CHARTS
       ============================================ */

    .js-plotly-plot {
        border: 1px solid var(--border-gray);
        border-radius: 8px;
        overflow: hidden;
    }

    /* ============================================
       CHECKBOX & RADIO
       ============================================ */

    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label {
        color: var(--text-black);
        font-weight: 500;
    }

    /* ============================================
       SLIDERS
       ============================================ */

    [data-testid="stSlider"] {
        color: var(--text-black);
    }

    /* ============================================
       SPINNER
       ============================================ */

    .stSpinner > div {
        border-top-color: var(--text-black) !important;
    }

    /* ============================================
       RESPONSIVE
       ============================================ */

    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
        }

        h2 {
            font-size: 1.5rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    }

    </style>
    ''', unsafe_allow_html=True)
