"""
streamlit_minimal_css.py
CSS inspiré du site Apple - Style épuré et élégant

Caractéristiques Apple:
- Typographie SF Pro / -apple-system
- Fond blanc pur (#ffffff) ou gris très clair (#f5f5f7)
- Texte noir (#1d1d1f) et gris (#6e6e73)
- Boutons bleu Apple (#0071e3)
- Espacements généreux
- Ombres très subtiles
- Minimalisme extrême

Usage:
    from streamlit_minimal_css import apply_minimal_css
    apply_minimal_css()
"""

import streamlit as st

def apply_minimal_css():
    """
    Applique un CSS vraiment inspiré d'Apple.com
    Épuré, aéré, élégant
    """

    st.markdown('''
    <style>
    /* Import Police Apple */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Variables Apple */
    :root {
        /* Couleurs Apple officielles */
        --apple-white: #ffffff;
        --apple-gray-light: #f5f5f7;
        --apple-gray-medium: #d2d2d7;
        --apple-black: #1d1d1f;
        --apple-gray: #6e6e73;
        --apple-blue: #0071e3;
        --apple-blue-hover: #0077ed;

        /* Espacements Apple (généreux) */
        --spacing-xs: 0.5rem;
        --spacing-sm: 1rem;
        --spacing-md: 2rem;
        --spacing-lg: 3rem;
        --spacing-xl: 4rem;

        /* Ombres subtiles */
        --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.04);
        --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.08);
    }

    /* ============================================
       BASE - TYPOGRAPHIE APPLE
       ============================================ */

    * {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }

    /* Fond général blanc pur */
    .stApp {
        background: var(--apple-white) !important;
        color: var(--apple-black) !important;
    }

    /* Cache éléments Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ============================================
       TYPOGRAPHIE - STYLE APPLE
       ============================================ */

    h1 {
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: -0.015em;
        color: var(--apple-black) !important;
        margin-bottom: var(--spacing-md);
        line-height: 1.1;
    }

    h2 {
        font-size: 2.25rem;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--apple-black) !important;
        margin-bottom: var(--spacing-sm);
        line-height: 1.2;
    }

    h3 {
        font-size: 1.75rem;
        font-weight: 600;
        letter-spacing: -0.005em;
        color: var(--apple-black) !important;
        margin-bottom: var(--spacing-sm);
        line-height: 1.3;
    }

    h4, h5, h6 {
        font-weight: 600;
        color: var(--apple-black) !important;
        letter-spacing: -0.003em;
    }

    p, span, div, label {
        color: var(--apple-black) !important;
        line-height: 1.6;
        font-size: 1.0625rem;
    }

    /* Texte secondaire */
    .secondary-text {
        color: var(--apple-gray) !important;
        font-size: 1rem;
    }

    /* ============================================
       TABS - STYLE APPLE (PAS DE FOND NOIR !)
       ============================================ */

    [data-testid="stTabs"] {
        background: transparent !important;
        border-bottom: 1px solid var(--apple-gray-medium);
        padding: 0;
        margin-bottom: var(--spacing-md);
    }

    [data-testid="stTabs"] button {
        background: transparent !important;
        color: var(--apple-gray) !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        padding: var(--spacing-sm) var(--spacing-md) !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        border-radius: 0 !important;
    }

    [data-testid="stTabs"] button:hover {
        color: var(--apple-black) !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--apple-black) !important;
        border-bottom-color: var(--apple-blue) !important;
        font-weight: 600 !important;
    }

    /* ============================================
       BOUTONS - BLEU APPLE
       ============================================ */

    .stButton > button {
        background: var(--apple-blue) !important;
        color: var(--apple-white) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        transition: background 0.2s ease !important;
        box-shadow: none !important;
        letter-spacing: -0.01em;
    }

    .stButton > button:hover {
        background: var(--apple-blue-hover) !important;
        transform: none !important;
    }

    .stButton > button:active {
        transform: scale(0.98) !important;
    }

    /* ============================================
       METRICS - STYLE APPLE ÉPURÉ
       ============================================ */

    [data-testid="stMetric"] {
        background: var(--apple-white) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: var(--spacing-md) !important;
        box-shadow: var(--shadow-soft) !important;
        transition: box-shadow 0.3s ease !important;
    }

    [data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-medium) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--apple-gray) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--apple-black) !important;
        font-size: 2.5rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    [data-testid="stMetricDelta"] {
        color: var(--apple-gray) !important;
        font-size: 0.9375rem !important;
    }

    /* ============================================
       DATAFRAMES - ÉPURÉ
       ============================================ */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--apple-gray-medium) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-soft) !important;
    }

    [data-testid="stDataFrame"] thead tr {
        background: var(--apple-gray-light) !important;
    }

    [data-testid="stDataFrame"] thead th {
        color: var(--apple-black) !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: none !important;
        letter-spacing: 0 !important;
        padding: 1rem !important;
        border-bottom: 1px solid var(--apple-gray-medium) !important;
    }

    [data-testid="stDataFrame"] tbody tr {
        border-bottom: 1px solid var(--apple-gray-medium) !important;
        transition: background 0.2s ease !important;
    }

    [data-testid="stDataFrame"] tbody tr:hover {
        background: var(--apple-gray-light) !important;
    }

    [data-testid="stDataFrame"] tbody td {
        color: var(--apple-black) !important;
        padding: 0.875rem 1rem !important;
        font-size: 1rem !important;
    }

    /* ============================================
       EXPANDERS - STYLE APPLE
       ============================================ */

    [data-testid="stExpander"] {
        background: var(--apple-white) !important;
        border: 1px solid var(--apple-gray-medium) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-soft) !important;
        margin-bottom: var(--spacing-sm) !important;
        overflow: hidden !important;
    }

    [data-testid="stExpander"] summary {
        color: var(--apple-black) !important;
        font-weight: 500 !important;
        padding: var(--spacing-sm) var(--spacing-md) !important;
        background: var(--apple-white) !important;
    }

    [data-testid="stExpander"] summary:hover {
        background: var(--apple-gray-light) !important;
    }

    [data-testid="stExpander"] *,
    [data-testid="stExpander"] p,
    [data-testid="stExpander"] span {
        color: var(--apple-black) !important;
    }

    /* ============================================
       ALERTS - STYLE APPLE DISCRET
       ============================================ */

    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border: 1px solid var(--apple-gray-medium) !important;
        padding: var(--spacing-sm) var(--spacing-md) !important;
        margin-bottom: var(--spacing-sm) !important;
        box-shadow: var(--shadow-soft) !important;
    }

    [data-testid="stAlert"],
    [data-testid="stAlert"] *,
    [data-testid="stAlert"] p {
        color: var(--apple-black) !important;
    }

    /* Info - Bleu très léger */
    [data-testid="stAlert"][data-baseweb="notification-info"] {
        background: #f0f8ff !important;
        border-color: #cfe4ff !important;
    }

    /* Success - Vert très léger */
    [data-testid="stAlert"][data-baseweb="notification-success"] {
        background: #f0fdf4 !important;
        border-color: #d1fae5 !important;
    }

    /* Warning - Jaune très léger */
    [data-testid="stAlert"][data-baseweb="notification-warning"] {
        background: #fffbeb !important;
        border-color: #fde68a !important;
    }

    /* Error - Rouge très léger */
    [data-testid="stAlert"][data-baseweb="notification-error"] {
        background: #fef2f2 !important;
        border-color: #fecaca !important;
    }

    /* ============================================
       FILE UPLOADER - STYLE APPLE
       ============================================ */

    [data-testid="stFileUploader"] {
        background: var(--apple-gray-light) !important;
        border: 2px dashed var(--apple-gray-medium) !important;
        border-radius: 16px !important;
        padding: var(--spacing-lg) !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--apple-blue) !important;
        background: var(--apple-white) !important;
    }

    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] * {
        color: var(--apple-black) !important;
    }

    [data-testid="stFileUploader"] small {
        color: var(--apple-gray) !important;
    }

    /* ============================================
       INPUTS & SELECT - STYLE APPLE
       ============================================ */

    [data-baseweb="select"],
    [data-baseweb="input"] {
        background: var(--apple-white) !important;
        border: 1px solid var(--apple-gray-medium) !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    [data-baseweb="select"] *,
    [data-baseweb="input"] *,
    [data-baseweb="select"] input,
    [data-baseweb="input"] input {
        color: var(--apple-black) !important;
    }

    [data-baseweb="select"]:hover,
    [data-baseweb="input"]:hover {
        border-color: var(--apple-blue) !important;
    }

    [data-baseweb="select"]:focus,
    [data-baseweb="input"]:focus {
        border-color: var(--apple-blue) !important;
        box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.1) !important;
    }

    /* Labels */
    [data-testid="stWidgetLabel"],
    .stTextInput label,
    .stSelectbox label,
    .stMultiselect label {
        color: var(--apple-black) !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* ============================================
       SIDEBAR - FOND GRIS LÉGER APPLE
       ============================================ */

    [data-testid="stSidebar"] {
        background: var(--apple-gray-light) !important;
        border-right: 1px solid var(--apple-gray-medium) !important;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: var(--apple-black) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        color: var(--apple-black) !important;
    }

    /* ============================================
       CODE BLOCKS
       ============================================ */

    code {
        background: var(--apple-gray-light) !important;
        color: var(--apple-black) !important;
        border: 1px solid var(--apple-gray-medium) !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.9375rem !important;
        font-family: 'SF Mono', 'Monaco', 'Menlo', monospace !important;
    }

    pre {
        background: var(--apple-gray-light) !important;
        border: 1px solid var(--apple-gray-medium) !important;
        border-radius: 12px !important;
        padding: var(--spacing-sm) !important;
    }

    /* ============================================
       PROGRESS BAR
       ============================================ */

    .stProgress > div > div {
        background: var(--apple-blue) !important;
        border-radius: 8px !important;
        height: 6px !important;
    }

    /* ============================================
       CUSTOM BOXES - VERSION APPLE SUBTILE
       ============================================ */

    .success-box {
        background: var(--apple-white) !important;
        padding: var(--spacing-md) !important;
        border-radius: 12px !important;
        border-left: 4px solid #34c759 !important;
        box-shadow: var(--shadow-soft) !important;
        margin: var(--spacing-sm) 0 !important;
    }

    .success-box,
    .success-box * {
        color: var(--apple-black) !important;
    }

    .warning-box {
        background: var(--apple-white) !important;
        padding: var(--spacing-md) !important;
        border-radius: 12px !important;
        border-left: 4px solid #ff9500 !important;
        box-shadow: var(--shadow-soft) !important;
        margin: var(--spacing-sm) 0 !important;
    }

    .warning-box,
    .warning-box * {
        color: var(--apple-black) !important;
    }

    .danger-box {
        background: var(--apple-white) !important;
        padding: var(--spacing-md) !important;
        border-radius: 12px !important;
        border-left: 4px solid #ff3b30 !important;
        box-shadow: var(--shadow-soft) !important;
        margin: var(--spacing-sm) 0 !important;
    }

    .danger-box,
    .danger-box * {
        color: var(--apple-black) !important;
    }

    /* ============================================
       SCROLLBAR - STYLE APPLE
       ============================================ */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--apple-gray-medium);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--apple-gray);
    }

    /* ============================================
       PLOTLY CHARTS
       ============================================ */

    .js-plotly-plot {
        border: 1px solid var(--apple-gray-medium) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-soft) !important;
    }

    /* ============================================
       CHECKBOX & RADIO
       ============================================ */

    [data-testid="stCheckbox"],
    [data-testid="stCheckbox"] *,
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"],
    [data-testid="stRadio"] *,
    [data-testid="stRadio"] label {
        color: var(--apple-black) !important;
        font-weight: 400 !important;
    }

    /* ============================================
       SLIDERS
       ============================================ */

    [data-testid="stSlider"],
    [data-testid="stSlider"] *,
    [data-testid="stSlider"] label {
        color: var(--apple-black) !important;
    }

    /* ============================================
       SPINNER
       ============================================ */

    .stSpinner > div {
        border-top-color: var(--apple-blue) !important;
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
            font-size: 2rem;
        }
    }

    /* ============================================
       RÈGLE GLOBALE - TEXTE NOIR PARTOUT
       ============================================ */

    body, body * {
        color: var(--apple-black) !important;
    }

    /* Exceptions pour texte secondaire */
    small,
    [data-baseweb="caption"],
    .caption {
        color: var(--apple-gray) !important;
    }

    </style>
    ''', unsafe_allow_html=True)
