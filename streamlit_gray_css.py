"""
streamlit_gray_css.py
CSS PROFESSIONNEL : Design Jaune/Bleu — DataQualityLab
Interface claire, structurée et lisible
"""

def get_gray_css():
    """CSS professionnel thème jaune clair / bleu foncé"""

    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ================================================================
       VARIABLES CSS GLOBALES — Thème Jaune/Bleu
    ================================================================ */

    :root {
        --primary: #2c5282;
        --primary-light: #3182ce;
        --primary-dark: #1a365d;
        --accent: #d69e2e;
        --accent-light: #ecc94b;
        --accent-bg: #FEF3C7;

        --bg-primary: #FFF9E6;
        --bg-secondary: #FEF3C7;
        --bg-card: #ffffff;
        --bg-glass: rgba(255, 255, 255, 0.85);

        --text-primary: #1a365d;
        --text-secondary: #2d3748;
        --text-muted: #718096;

        --border-color: #e2e8f0;
        --border-accent: rgba(44, 82, 130, 0.3);

        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);

        --success: #38a169;
        --warning: #d69e2e;
        --danger: #e53e3e;
        --info: #3182ce;
    }

    /* ================================================================
       RESET & BASE
    ================================================================ */

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* ================================================================
       FOND PRINCIPAL
    ================================================================ */

    .stApp {
        background: var(--bg-primary) !important;
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
       SIDEBAR
    ================================================================ */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a365d 0%, #2c5282 100%) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 2rem 1.5rem !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.25) !important;
    }

    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 2px dashed rgba(255, 255, 255, 0.3) !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] * {
        color: rgba(255, 255, 255, 0.8) !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background: var(--accent) !important;
        color: #1a365d !important;
        border: none !important;
    }

    /* ================================================================
       TEXTE
    ================================================================ */

    body, body *,
    .main, .main *,
    p, span, div, label {
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"],
    .stSelectbox label,
    .stSlider label,
    .stTextInput label,
    .stFileUploader label {
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* ================================================================
       TITRES
    ================================================================ */

    h1 {
        color: var(--primary-dark) !important;
        -webkit-text-fill-color: var(--primary-dark) !important;
        background: none !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.5px !important;
    }

    h2 {
        color: var(--primary) !important;
        -webkit-text-fill-color: var(--primary) !important;
        background: none !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid var(--accent) !important;
        border-image: none !important;
    }

    h3 {
        color: var(--primary) !important;
        -webkit-text-fill-color: var(--primary) !important;
        background: none !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* ================================================================
       TABS
    ================================================================ */

    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: 12px !important;
        padding: 0.4rem !important;
        gap: 0.4rem !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted) !important;
        background: transparent !important;
        padding: 0.6rem 1rem !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: white !important;
        -webkit-text-fill-color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(44, 82, 130, 0.3) !important;
    }

    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background: var(--accent-bg) !important;
        color: var(--primary) !important;
    }

    /* ================================================================
       BOUTONS
    ================================================================ */

    .stButton > button {
        background: var(--bg-card) !important;
        color: var(--primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.4rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button:hover {
        background: var(--accent-bg) !important;
        border-color: var(--primary) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--primary) !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(44, 82, 130, 0.3) !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: var(--primary-light) !important;
        box-shadow: 0 4px 16px rgba(44, 82, 130, 0.4) !important;
    }

    /* ================================================================
       CARDS / METRICS
    ================================================================ */

    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: var(--shadow-sm) !important;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--border-accent) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--primary) !important;
        -webkit-text-fill-color: var(--primary) !important;
        background: none !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ================================================================
       INPUTS
    ================================================================ */

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.95rem !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(44, 82, 130, 0.15) !important;
        outline: none !important;
    }

    /* ================================================================
       SELECTBOX & MULTISELECT
    ================================================================ */

    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
    }

    .stSelectbox [data-baseweb="select"] > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background: transparent !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div[data-testid] {
        color: var(--text-primary) !important;
    }

    /* ================================================================
       DROPDOWN MENU
    ================================================================ */

    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div,
    [data-baseweb="popover"] [data-baseweb="menu"],
    div[data-baseweb="popover"] {
        background: var(--bg-card) !important;
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-lg) !important;
    }

    [data-baseweb="menu"],
    [data-baseweb="menu"] ul,
    ul[role="listbox"],
    div[role="listbox"],
    [data-baseweb="list"],
    [data-baseweb="menu-list"] {
        background: var(--bg-card) !important;
        background-color: var(--bg-card) !important;
    }

    [role="option"],
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] [role="option"],
    li[role="option"],
    div[role="option"],
    ul[role="listbox"] li {
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        background-color: var(--bg-card) !important;
    }

    [role="option"]:hover,
    [data-baseweb="menu"] li:hover,
    li[role="option"]:hover,
    div[role="option"]:hover,
    ul[role="listbox"] li:hover {
        background: var(--accent-bg) !important;
        background-color: var(--accent-bg) !important;
        color: var(--primary) !important;
    }

    [aria-selected="true"],
    [data-baseweb="menu"] [aria-selected="true"],
    [data-highlighted="true"],
    li[aria-selected="true"],
    div[aria-selected="true"] {
        background: rgba(44, 82, 130, 0.1) !important;
        background-color: rgba(44, 82, 130, 0.1) !important;
        color: var(--primary) !important;
    }

    [role="option"] *,
    [data-baseweb="menu"] li *,
    ul[role="listbox"] li * {
        color: var(--text-primary) !important;
    }

    .stSelectbox svg,
    .stMultiSelect svg {
        fill: var(--text-muted) !important;
        color: var(--text-muted) !important;
    }

    /* ================================================================
       DATAFRAMES
    ================================================================ */

    [data-testid="stDataFrame"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    [data-testid="stDataFrame"] th {
        background: var(--primary) !important;
        color: #ffffff !important;
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
       ALERTS
    ================================================================ */

    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border: none !important;
    }

    .stAlert > div {
        color: var(--text-primary) !important;
    }

    [data-testid="stInfo"],
    div[data-baseweb="notification"][kind="info"] {
        background: rgba(49, 130, 206, 0.08) !important;
        border-left: 4px solid var(--info) !important;
    }

    [data-testid="stSuccess"],
    div[data-baseweb="notification"][kind="positive"] {
        background: rgba(56, 161, 105, 0.08) !important;
        border-left: 4px solid var(--success) !important;
    }

    [data-testid="stWarning"],
    div[data-baseweb="notification"][kind="warning"] {
        background: rgba(214, 158, 46, 0.1) !important;
        border-left: 4px solid var(--warning) !important;
    }

    [data-testid="stError"],
    div[data-baseweb="notification"][kind="negative"] {
        background: rgba(229, 62, 62, 0.08) !important;
        border-left: 4px solid var(--danger) !important;
    }

    /* ================================================================
       EXPANDER
    ================================================================ */

    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 1rem 1.25rem !important;
        font-weight: 500 !important;
    }

    .streamlit-expanderHeader:hover {
        background: var(--accent-bg) !important;
        border-color: var(--border-accent) !important;
    }

    .streamlit-expanderContent {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 1.25rem !important;
    }

    /* ================================================================
       FILE UPLOADER
    ================================================================ */

    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary) !important;
        background: rgba(44, 82, 130, 0.03) !important;
    }

    [data-testid="stFileUploader"] * {
        color: var(--text-muted) !important;
    }

    [data-testid="stFileUploader"] button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }

    /* ================================================================
       DIVIDER
    ================================================================ */

    hr {
        border: none !important;
        height: 1px !important;
        background: var(--border-color) !important;
        margin: 2rem 0 !important;
    }

    /* ================================================================
       SCROLLBAR
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
        background: var(--primary);
        border-radius: 4px;
        opacity: 0.5;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-light);
    }

    /* ================================================================
       CODE BLOCKS
    ================================================================ */

    code {
        background: rgba(44, 82, 130, 0.08) !important;
        color: var(--primary) !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
    }

    pre {
        background: #f7fafc !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }

    /* ================================================================
       DOWNLOAD BUTTON
    ================================================================ */

    .stDownloadButton > button {
        background: var(--success) !important;
        border: none !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 8px rgba(56, 161, 105, 0.25) !important;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 4px 16px rgba(56, 161, 105, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* ================================================================
       PLOTLY CHARTS
    ================================================================ */

    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }

    /* ================================================================
       SLIDERS
    ================================================================ */

    .stSlider > div > div > div > div {
        background: var(--border-color) !important;
    }

    .stSlider > div > div > div > div > div {
        background: var(--primary) !important;
    }

    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: white !important;
        border: 3px solid var(--primary) !important;
        box-shadow: 0 2px 6px rgba(44, 82, 130, 0.3) !important;
    }

    /* ================================================================
       MULTISELECT TAGS
    ================================================================ */

    [data-baseweb="tag"] {
        background: var(--primary) !important;
        border-radius: 6px !important;
    }

    [data-baseweb="tag"] span {
        color: white !important;
    }

    /* ================================================================
       PROGRESS BAR
    ================================================================ */

    .stProgress > div > div {
        background: var(--border-color) !important;
        border-radius: 10px !important;
    }

    .stProgress > div > div > div {
        background: var(--primary) !important;
        border-radius: 10px !important;
    }

    /* ================================================================
       TABLES HTML
    ================================================================ */

    table, th, td {
        color: var(--text-primary) !important;
    }

    th {
        background: var(--primary) !important;
        color: #ffffff !important;
    }

    td {
        background: var(--bg-card) !important;
    }

    tr:hover td {
        background: var(--accent-bg) !important;
    }

    /* ================================================================
       MARKDOWN
    ================================================================ */

    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown span {
        color: var(--text-secondary) !important;
    }

    /* ================================================================
       LINKS
    ================================================================ */

    a, a:visited {
        color: var(--primary-light) !important;
    }

    a:hover {
        color: var(--primary) !important;
    }

    /* ================================================================
       LABELS
    ================================================================ */

    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stMultiSelect label,
    .stTextArea label,
    .stFileUploader label,
    .stSlider label,
    .stCheckbox label,
    .stRadio label {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    /* ================================================================
       JSON DISPLAY
    ================================================================ */

    .stJson {
        background: #f7fafc !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }

    /* ================================================================
       NUMBER INPUT BUTTONS
    ================================================================ */

    .stNumberInput button {
        background: rgba(44, 82, 130, 0.1) !important;
        color: var(--primary) !important;
        border: none !important;
    }

    .stNumberInput button:hover {
        background: rgba(44, 82, 130, 0.2) !important;
    }

    /* ================================================================
       GENERIC OVERRIDES — Remove dark residues
    ================================================================ */

    [data-baseweb="select"] *,
    [data-baseweb="combobox"] *,
    [data-baseweb="input"] * {
        color: var(--text-primary) !important;
    }

    [data-baseweb="base-popover"],
    [data-baseweb="popover-content"],
    [data-baseweb="block"] {
        background: var(--bg-card) !important;
        background-color: var(--bg-card) !important;
    }

    .element-container,
    .row-widget,
    .stSelectbox > div,
    .stMultiSelect > div {
        background: transparent !important;
    }

    .stMultiSelect [data-baseweb="tag"] {
        background: var(--primary) !important;
        color: #ffffff !important;
    }

    [data-baseweb="input"] input,
    [data-baseweb="select"] input[type="text"] {
        background: transparent !important;
        color: var(--text-primary) !important;
    }

    [data-baseweb="clear-icon"],
    [data-baseweb="select"] button {
        color: var(--text-muted) !important;
    }

    </style>
    """
