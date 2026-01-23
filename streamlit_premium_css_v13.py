{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 """\
streamlit_premium_css_v13.py\
CSS ultra-moderne pour Framework Data Quality Probabiliste\
"""\
\
import streamlit as st\
\
def apply_ultra_modern_css_with_theme(theme='dark'):\
    """Applique CSS premium avec support theme clair/sombre"""\
    \
    if theme == 'light':\
        theme_vars = '''\
        :root \{\
            --bg-primary: #ffffff;\
            --bg-surface: #f8f9fa;\
            --bg-elevated: #ffffff;\
            --text-primary: #1a1a1a;\
            --text-secondary: #6b7280;\
            --border: rgba(0, 0, 0, 0.08);\
            --primary: #6366f1;\
            --primary-light: #818cf8;\
        \}\
        '''\
    else:\
        theme_vars = '''\
        :root \{\
            --bg-primary: #0a0a0a;\
            --bg-surface: #0f0f0f;\
            --bg-elevated: #1a1a1a;\
            --text-primary: #ffffff;\
            --text-secondary: #a0a0a0;\
            --border: rgba(255, 255, 255, 0.08);\
            --primary: #6366f1;\
            --primary-light: #818cf8;\
        \}\
        '''\
    \
    st.markdown(f'''\
    <style>\
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');\
    \
    \{theme_vars\}\
    \
    * \{\{\
        font-family: 'Inter', -apple-system, sans-serif;\
        -webkit-font-smoothing: antialiased;\
    \}\}\
    \
    .stApp \{\{\
        background: var(--bg-primary);\
        color: var(--text-primary);\
        transition: background 0.3s ease;\
    \}\}\
    \
    #MainMenu \{\{visibility: hidden;\}\}\
    footer \{\{visibility: hidden;\}\}\
    header \{\{visibility: hidden;\}\}\
    \
    .main-header \{\{\
        font-size: 3rem;\
        font-weight: 800;\
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);\
        -webkit-background-clip: text;\
        -webkit-text-fill-color: transparent;\
        text-align: center;\
        margin-bottom: 2rem;\
        animation: gradient-shift 3s ease infinite;\
        background-size: 200% 200%;\
    \}\}\
    \
    @keyframes gradient-shift \{\{\
        0%, 100% \{\{ background-position: 0% 50%; \}\}\
        50% \{\{ background-position: 100% 50%; \}\}\
    \}\}\
    \
    [data-testid="stExpander"],\
    .element-container > div > div \{\{\
        background: var(--bg-elevated);\
        border: 1px solid var(--border);\
        border-radius: 16px;\
        transition: all 0.3s ease;\
    \}\}\
    \
    [data-testid="stExpander"]:hover \{\{\
        border-color: rgba(99, 102, 241, 0.3);\
        box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.3), 0 12px 48px rgba(99, 102, 241, 0.15);\
        transform: translateY(-2px);\
    \}\}\
    \
    .stButton > button \{\{\
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);\
        color: white;\
        border: none;\
        border-radius: 12px;\
        padding: 0.875rem 2rem;\
        font-weight: 600;\
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);\
        transition: all 0.3s ease;\
    \}\}\
    \
    .stButton > button:hover \{\{\
        transform: translateY(-2px);\
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);\
    \}\}\
    \
    [data-testid="stTabs"] \{\{\
        border-bottom: 1px solid var(--border);\
        margin-bottom: 2rem;\
    \}\}\
    \
    [data-testid="stTabs"] button \{\{\
        background: transparent;\
        border-bottom: 2px solid transparent;\
        color: var(--text-secondary);\
        font-weight: 500;\
        padding: 1rem 1.5rem;\
        transition: all 0.2s ease;\
    \}\}\
    \
    [data-testid="stTabs"] button:hover \{\{\
        color: var(--text-primary);\
        background: rgba(99, 102, 241, 0.05);\
    \}\}\
    \
    [data-testid="stTabs"] button[aria-selected="true"] \{\{\
        color: var(--primary-light);\
        border-bottom-color: var(--primary);\
        background: rgba(99, 102, 241, 0.08);\
    \}\}\
    \
    [data-testid="stMetric"] \{\{\
        background: var(--bg-elevated);\
        border: 1px solid var(--border);\
        border-radius: 16px;\
        padding: 1.5rem;\
        transition: all 0.3s ease;\
    \}\}\
    \
    [data-testid="stMetricLabel"] \{\{\
        font-size: 0.8125rem;\
        font-weight: 600;\
        text-transform: uppercase;\
        letter-spacing: 0.08em;\
        color: var(--text-secondary);\
    \}\}\
    \
    [data-testid="stMetricValue"] \{\{\
        font-size: 2.25rem;\
        font-weight: 700;\
        color: var(--text-primary);\
    \}\}\
    \
    [data-testid="stDataFrame"] \{\{\
        border-radius: 12px;\
        border: 1px solid var(--border);\
    \}\}\
    \
    [data-testid="stDataFrame"] thead tr \{\{\
        background: var(--bg-elevated);\
    \}\}\
    \
    [data-testid="stDataFrame"] thead th \{\{\
        color: var(--text-primary) !important;\
        font-weight: 600 !important;\
        text-transform: uppercase;\
        font-size: 0.75rem;\
        padding: 1rem !important;\
    \}\}\
    \
    [data-testid="stDataFrame"] tbody tr \{\{\
        transition: background 0.2s ease;\
    \}\}\
    \
    [data-testid="stDataFrame"] tbody tr:hover \{\{\
        background: rgba(99, 102, 241, 0.05);\
    \}\}\
    \
    [data-testid="stFileUploader"] \{\{\
        background: linear-gradient(135deg, \
            rgba(99, 102, 241, 0.05) 0%, \
            rgba(139, 92, 246, 0.05) 100%\
        );\
        border: 2px dashed var(--border);\
        border-radius: 20px;\
        padding: 3rem 2rem;\
        transition: all 0.3s ease;\
    \}\}\
    \
    [data-testid="stFileUploader"]:hover \{\{\
        border-color: var(--primary);\
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);\
    \}\}\
    \
    .stProgress > div > div \{\{\
        background: linear-gradient(90deg, #10b981 0%, #f59e0b 50%, #ef4444 100%);\
        border-radius: 8px;\
        height: 10px;\
    \}\}\
    \
    [data-testid="stAlert"] \{\{\
        border-radius: 12px;\
        padding: 1.25rem 1.5rem;\
    \}\}\
    \
    .js-plotly-plot \{\{\
        border-radius: 12px;\
        border: 1px solid var(--border);\
    \}\}\
    \
    [data-testid="stSidebar"] \{\{\
        background: var(--bg-surface);\
        border-right: 1px solid var(--border);\
    \}\}\
    \
    .metric-card \{\{\
        background: var(--bg-elevated);\
        padding: 1.5rem;\
        border-radius: 16px;\
        border: 1px solid var(--border);\
        border-left: 4px solid var(--primary);\
        margin: 1rem 0;\
        transition: all 0.3s ease;\
    \}\}\
    \
    .success-box \{\{\
        background: rgba(16, 185, 129, 0.08);\
        padding: 1rem;\
        border-radius: 12px;\
        border-left: 4px solid #10b981;\
    \}\}\
    \
    .warning-box \{\{\
        background: rgba(245, 158, 11, 0.08);\
        padding: 1rem;\
        border-radius: 12px;\
        border-left: 4px solid #f59e0b;\
    \}\}\
    \
    .danger-box \{\{\
        background: rgba(239, 68, 68, 0.08);\
        padding: 1rem;\
        border-radius: 12px;\
        border-left: 4px solid #ef4444;\
    \}\}\
    \
    ::-webkit-scrollbar \{\{\
        width: 12px;\
        height: 12px;\
    \}\}\
    \
    ::-webkit-scrollbar-track \{\{\
        background: var(--bg-surface);\
    \}\}\
    \
    ::-webkit-scrollbar-thumb \{\{\
        background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);\
        border-radius: 6px;\
    \}\}\
    \
    </style>\
    ''', unsafe_allow_html=True)}