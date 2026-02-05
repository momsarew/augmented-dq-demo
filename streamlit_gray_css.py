"""
streamlit_gray_css.py
CSS MODERNE : Design glassmorphism + gradients subtils
Interface élégante et professionnelle
"""

def get_gray_css():
    """CSS moderne avec glassmorphism et design épuré"""

    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ================================================================
       VARIABLES CSS GLOBALES
    ================================================================ */

    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        --warning-gradient: linear-gradient(135deg, #F2994A 0%, #F2C94C 100%);
        --danger-gradient: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);

        --bg-primary: #0f0f23;
        --bg-secondary: #1a1a2e;
        --bg-card: rgba(255, 255, 255, 0.03);
        --bg-glass: rgba(255, 255, 255, 0.05);

        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.7);
        --text-muted: rgba(255, 255, 255, 0.5);

        --border-color: rgba(255, 255, 255, 0.1);
        --border-glow: rgba(102, 126, 234, 0.3);

        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
        --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.4);
        --shadow-glow: 0 0 30px rgba(102, 126, 234, 0.2);
    }

    /* ================================================================
       RESET & BASE
    ================================================================ */

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        transition: all 0.2s ease-in-out;
    }

    /* ================================================================
       FOND PRINCIPAL - Gradient sombre élégant
    ================================================================ */

    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%) !important;
        min-height: 100vh;
    }

    .main {
        background: transparent !important;
    }

    .main .block-container {
        background: transparent !important;
        padding: 2rem 3rem !important;
        max-width: 1600px !important;
    }

    /* ================================================================
       SIDEBAR - Glassmorphism
    ================================================================ */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(15, 15, 35, 0.98) 100%) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 2rem 1.5rem !important;
    }

    /* ================================================================
       TEXTE - Palette claire sur fond sombre
    ================================================================ */

    body, body *,
    .main, .main *,
    p, span, div, label {
        color: var(--text-primary) !important;
    }

    /* Texte secondaire pour labels */
    [data-testid="stMetricLabel"],
    .stSelectbox label,
    .stSlider label,
    .stTextInput label,
    .stFileUploader label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* ================================================================
       TITRES - Gradient text ou blanc pur
    ================================================================ */

    h1 {
        background: var(--primary-gradient) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.5px !important;
    }

    h2 {
        color: var(--text-primary) !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid transparent !important;
        border-image: var(--primary-gradient) 1 !important;
    }

    h3 {
        color: var(--text-primary) !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* ================================================================
       TABS - Design moderne avec pills
    ================================================================ */

    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 16px !important;
        padding: 0.5rem !important;
        gap: 0.5rem !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        background: transparent !important;
        padding: 0.75rem 1.25rem !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        border-radius: 12px !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        -webkit-text-fill-color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }

    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background: rgba(255, 255, 255, 0.08) !important;
        color: var(--text-primary) !important;
    }

    /* ================================================================
       BOUTONS - Gradients et effets hover
    ================================================================ */

    .stButton > button {
        background: var(--bg-glass) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: var(--border-glow) !important;
        box-shadow: var(--shadow-glow) !important;
        transform: translateY(-2px) !important;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--primary-gradient) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5) !important;
        transform: translateY(-3px) !important;
    }

    /* ================================================================
       CARDS / METRICS - Glassmorphism
    ================================================================ */

    [data-testid="stMetric"] {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: var(--shadow-md) !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--border-glow) !important;
        box-shadow: var(--shadow-glow) !important;
        transform: translateY(-4px) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    [data-testid="stMetricValue"] {
        background: var(--primary-gradient) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ================================================================
       INPUTS - Style moderne avec bon contraste
    ================================================================ */

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
        border: 1px solid rgba(102, 126, 234, 0.4) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stNumberInput > div > div > input::placeholder,
    .stTextArea textarea::placeholder {
        color: rgba(255, 255, 255, 0.5) !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3) !important;
        outline: none !important;
        background: rgba(40, 40, 70, 0.95) !important;
    }

    /* Password input */
    .stTextInput input[type="password"] {
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
    }

    /* ================================================================
       SELECTBOX & MULTISELECT - Fond sombre avec texte clair
    ================================================================ */

    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: rgba(30, 30, 50, 0.95) !important;
        border: 1px solid rgba(102, 126, 234, 0.4) !important;
        border-radius: 12px !important;
    }

    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background: transparent !important;
        color: #ffffff !important;
    }

    /* Le texte sélectionné dans le selectbox */
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div[data-testid] {
        color: #ffffff !important;
    }

    /* ================================================================
       DROPDOWN MENU - Liste déroulante (CORRECTION CONTRASTE)
    ================================================================ */

    /* Conteneur principal du popover/dropdown */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div,
    [data-baseweb="popover"] [data-baseweb="menu"],
    div[data-baseweb="popover"] {
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
        border: 1px solid rgba(102, 126, 234, 0.5) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7) !important;
    }

    /* Menu list container */
    [data-baseweb="menu"],
    [data-baseweb="menu"] ul,
    ul[role="listbox"],
    div[role="listbox"],
    [data-baseweb="list"],
    [data-baseweb="menu-list"] {
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
    }

    /* Chaque option dans le dropdown */
    [role="option"],
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] [role="option"],
    li[role="option"],
    div[role="option"],
    ul[role="listbox"] li,
    [data-baseweb="list"] li,
    [data-baseweb="menu-list"] li {
        color: #ffffff !important;
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
    }

    /* Hover sur les options */
    [role="option"]:hover,
    [data-baseweb="menu"] li:hover,
    li[role="option"]:hover,
    div[role="option"]:hover,
    ul[role="listbox"] li:hover {
        background: rgba(102, 126, 234, 0.4) !important;
        background-color: rgba(102, 126, 234, 0.4) !important;
        color: #ffffff !important;
    }

    /* Option sélectionnée / highlighted */
    [aria-selected="true"],
    [data-baseweb="menu"] [aria-selected="true"],
    [data-highlighted="true"],
    li[aria-selected="true"],
    div[aria-selected="true"] {
        background: rgba(102, 126, 234, 0.5) !important;
        background-color: rgba(102, 126, 234, 0.5) !important;
        color: #ffffff !important;
    }

    /* Texte dans les options */
    [role="option"] *,
    [data-baseweb="menu"] li *,
    ul[role="listbox"] li * {
        color: #ffffff !important;
    }

    /* Icône de dropdown (flèche) */
    .stSelectbox svg,
    .stMultiSelect svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }

    /* Input dans le multiselect */
    .stMultiSelect input,
    [data-baseweb="select"] input {
        color: #ffffff !important;
        background: transparent !important;
    }

    /* Placeholder dans select */
    [data-baseweb="select"] [data-baseweb="input"] {
        color: #ffffff !important;
    }

    /* Le conteneur du select lui-même */
    [data-baseweb="select"],
    [data-baseweb="select"] > div {
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
    }

    /* ================================================================
       SLIDERS - Style moderne
    ================================================================ */

    .stSlider > div > div > div > div {
        background: var(--border-color) !important;
    }

    .stSlider > div > div > div > div > div {
        background: var(--primary-gradient) !important;
    }

    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: white !important;
        border: 3px solid #667eea !important;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4) !important;
    }

    /* ================================================================
       DATAFRAMES - Style moderne
    ================================================================ */

    [data-testid="stDataFrame"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        backdrop-filter: blur(10px) !important;
    }

    [data-testid="stDataFrame"] th {
        background: rgba(102, 126, 234, 0.2) !important;
        color: var(--text-primary) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    [data-testid="stDataFrame"] td {
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
        border-bottom: 1px solid var(--border-color) !important;
    }

    /* ================================================================
       ALERTS - Gradients subtils
    ================================================================ */

    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
    }

    .stAlert > div {
        color: var(--text-primary) !important;
    }

    [data-testid="stInfo"],
    div[data-baseweb="notification"][kind="info"] {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%) !important;
        border-left: 4px solid #667eea !important;
    }

    [data-testid="stSuccess"],
    div[data-baseweb="notification"][kind="positive"] {
        background: linear-gradient(135deg, rgba(17, 153, 142, 0.15) 0%, rgba(56, 239, 125, 0.15) 100%) !important;
        border-left: 4px solid #38ef7d !important;
    }

    [data-testid="stWarning"],
    div[data-baseweb="notification"][kind="warning"] {
        background: linear-gradient(135deg, rgba(242, 153, 74, 0.15) 0%, rgba(242, 201, 76, 0.15) 100%) !important;
        border-left: 4px solid #F2994A !important;
    }

    [data-testid="stError"],
    div[data-baseweb="notification"][kind="negative"] {
        background: linear-gradient(135deg, rgba(235, 51, 73, 0.15) 0%, rgba(244, 92, 67, 0.15) 100%) !important;
        border-left: 4px solid #eb3349 !important;
    }

    /* ================================================================
       EXPANDER - Style moderne
    ================================================================ */

    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem 1.25rem !important;
        font-weight: 500 !important;
        backdrop-filter: blur(10px) !important;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: var(--border-glow) !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 1.25rem !important;
        backdrop-filter: blur(10px) !important;
    }

    /* ================================================================
       FILE UPLOADER - Style moderne
    ================================================================ */

    [data-testid="stFileUploader"] {
        background: var(--bg-glass) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #667eea !important;
        background: rgba(102, 126, 234, 0.05) !important;
    }

    [data-testid="stFileUploader"] * {
        color: var(--text-secondary) !important;
    }

    [data-testid="stFileUploader"] button {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }

    /* ================================================================
       DIVIDER / SEPARATOR
    ================================================================ */

    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--border-color), transparent) !important;
        margin: 2rem 0 !important;
    }

    /* ================================================================
       SCROLLBAR - Style moderne
    ================================================================ */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea, #764ba2);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #5a6fd6, #6a4190);
    }

    /* ================================================================
       CODE BLOCKS
    ================================================================ */

    code {
        background: rgba(102, 126, 234, 0.15) !important;
        color: #a78bfa !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
    }

    pre {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* ================================================================
       JSON DISPLAY
    ================================================================ */

    .stJson {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* ================================================================
       DOWNLOAD BUTTON
    ================================================================ */

    .stDownloadButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.3) !important;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 6px 25px rgba(56, 239, 125, 0.4) !important;
        transform: translateY(-2px) !important;
    }

    /* ================================================================
       SPINNER
    ================================================================ */

    .stSpinner > div {
        border-top-color: #667eea !important;
    }

    /* ================================================================
       PLOTLY CHARTS - Fond transparent
    ================================================================ */

    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }

    /* ================================================================
       MULTISELECT TAGS
    ================================================================ */

    [data-baseweb="tag"] {
        background: var(--primary-gradient) !important;
        border-radius: 8px !important;
    }

    [data-baseweb="tag"] span {
        color: white !important;
    }

    /* ================================================================
       TOOLTIP
    ================================================================ */

    [data-testid="stTooltipIcon"] {
        color: var(--text-muted) !important;
    }

    /* ================================================================
       PROGRESS BAR
    ================================================================ */

    .stProgress > div > div {
        background: var(--border-color) !important;
        border-radius: 10px !important;
    }

    .stProgress > div > div > div {
        background: var(--primary-gradient) !important;
        border-radius: 10px !important;
    }

    /* ================================================================
       CHECKBOX & RADIO
    ================================================================ */

    .stCheckbox label span,
    .stRadio label span {
        color: var(--text-primary) !important;
    }

    /* ================================================================
       FIX CONTRASTE GÉNÉRAL - Textes sur fond clair/sombre
    ================================================================ */

    /* Labels des inputs */
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stMultiSelect label,
    .stTextArea label,
    .stFileUploader label,
    .stSlider label,
    .stCheckbox label,
    .stRadio label {
        color: #e0e0e0 !important;
        font-weight: 500 !important;
    }

    /* Petit texte d'aide sous les inputs */
    .stTextInput small,
    .stSelectbox small,
    .stNumberInput small,
    div[data-testid="stFormSubmitButton"] + small,
    .stHelp,
    [data-testid="stWidgetHelp"] {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    /* Messages d'info dans les widgets */
    .stTextInput .stAlert,
    .stSelectbox .stAlert {
        background: rgba(102, 126, 234, 0.15) !important;
        color: #ffffff !important;
    }

    /* Texte dans les expandeurs de sidebar */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* Liens */
    a, a:visited {
        color: #8b9fff !important;
    }

    a:hover {
        color: #a5b4ff !important;
    }

    /* Markdown text */
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown span {
        color: #e8e8e8 !important;
    }

    /* Caption et small text */
    .stCaption, caption, figcaption {
        color: rgba(255, 255, 255, 0.7) !important;
    }

    /* Tables HTML */
    table, th, td {
        color: #ffffff !important;
    }

    th {
        background: rgba(102, 126, 234, 0.3) !important;
    }

    td {
        background: rgba(30, 30, 50, 0.5) !important;
    }

    tr:hover td {
        background: rgba(102, 126, 234, 0.15) !important;
    }

    /* Number input buttons */
    .stNumberInput button {
        background: rgba(102, 126, 234, 0.3) !important;
        color: #ffffff !important;
        border: none !important;
    }

    .stNumberInput button:hover {
        background: rgba(102, 126, 234, 0.5) !important;
    }

    /* Date input */
    .stDateInput > div > div > input {
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
        border: 1px solid rgba(102, 126, 234, 0.4) !important;
        border-radius: 12px !important;
    }

    /* Time input */
    .stTimeInput > div > div > input {
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
        border: 1px solid rgba(102, 126, 234, 0.4) !important;
        border-radius: 12px !important;
    }

    /* Color picker */
    .stColorPicker label {
        color: #e0e0e0 !important;
    }

    /* Camera input */
    .stCameraInput label {
        color: #e0e0e0 !important;
    }

    /* Text area */
    .stTextArea > div > div > textarea {
        background: rgba(30, 30, 50, 0.95) !important;
        color: #ffffff !important;
        border: 1px solid rgba(102, 126, 234, 0.4) !important;
        border-radius: 12px !important;
    }

    /* ================================================================
       FIX GLOBAL - Forcer fond sombre sur tous les widgets interactifs
    ================================================================ */

    /* Tous les inputs de type select/combobox */
    [data-baseweb="select"] *,
    [data-baseweb="combobox"] *,
    [data-baseweb="input"] * {
        color: #ffffff !important;
    }

    /* Les conteneurs de liste */
    [data-baseweb="base-popover"],
    [data-baseweb="popover-content"],
    [data-baseweb="block"] {
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
    }

    /* Override pour tous les éléments avec fond blanc */
    .st-emotion-cache-1inwz65,
    .st-emotion-cache-16idsys,
    .st-emotion-cache-1v7f65g,
    .st-emotion-cache-10trblm,
    .st-emotion-cache-1dp5vir,
    .st-emotion-cache-ocqkz7,
    .st-emotion-cache-1y4p8pa {
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
        color: #ffffff !important;
    }

    /* Dropdown/Select option container - approche plus globale */
    div[data-testid="stSelectbox"] ul,
    div[data-testid="stSelectbox"] li,
    div[data-testid="stMultiSelect"] ul,
    div[data-testid="stMultiSelect"] li {
        background: #1a1a2e !important;
        color: #ffffff !important;
    }

    /* Pour les éléments internes des selectbox */
    [class*="st-emotion-cache"] ul[role="listbox"],
    [class*="st-emotion-cache"] li[role="option"] {
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
        color: #ffffff !important;
    }

    [class*="st-emotion-cache"] li[role="option"]:hover {
        background: rgba(102, 126, 234, 0.4) !important;
    }

    /* Supprimer tout fond blanc résiduel */
    .stApp div[style*="background: white"],
    .stApp div[style*="background-color: white"],
    .stApp div[style*="background: rgb(255"],
    .stApp div[style*="background-color: rgb(255"] {
        background: #1a1a2e !important;
        background-color: #1a1a2e !important;
    }

    /* Conteneurs génériques Streamlit */
    .element-container,
    .row-widget,
    .stSelectbox > div,
    .stMultiSelect > div {
        background: transparent !important;
    }

    /* Zone de saisie dans multiselect */
    .stMultiSelect [data-baseweb="tag"] {
        background: rgba(102, 126, 234, 0.6) !important;
        color: #ffffff !important;
    }

    .stMultiSelect [data-baseweb="tag"] span {
        color: #ffffff !important;
    }

    /* Search input dans les dropdowns */
    [data-baseweb="input"] input,
    [data-baseweb="select"] input[type="text"] {
        background: transparent !important;
        color: #ffffff !important;
    }

    /* Clear button dans select */
    [data-baseweb="clear-icon"],
    [data-baseweb="select"] button {
        color: #ffffff !important;
    }

    /* ================================================================
       SIDEBAR SPECIFIC OVERRIDES
    ================================================================ */

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        -webkit-text-fill-color: var(--text-primary) !important;
        background: none !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
    }

    /* ================================================================
       ANIMATION KEYFRAMES
    ================================================================ */

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.3); }
        50% { box-shadow: 0 0 40px rgba(102, 126, 234, 0.5); }
    }

    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    </style>
    """
