"""
streamlit_premium_css_v13.py
CSS ultra-moderne
"""

import streamlit as st

def apply_ultra_modern_css_with_theme(theme='dark'):
    if theme == 'light':
        theme_vars = '''
        :root {
            --bg-primary: #ffffff;
            --bg-surface: #f8f9fa;
            --bg-elevated: #ffffff;
            --text-primary: #1a1a1a;
            --text-secondary: #6b7280;
            --border: rgba(0, 0, 0, 0.08);
            --primary: #6366f1;
        }
        '''
    else:
        theme_vars = '''
        :root {
            --bg-primary: #0a0a0a;
            --bg-surface: #0f0f0f;
            --bg-elevated: #1a1a1a;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
        }
        '''
    
    st.markdown(f'''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    {theme_vars}
    
    * {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: var(--bg-primary); color: var(--text-primary); }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    .main-header {{
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    [data-testid="stExpander"] {{
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 16px;
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.875rem 2rem;
        font-weight: 600;
    }}
    
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: #818cf8;
        border-bottom: 2px solid #6366f1;
    }}
    
    [data-testid="stMetric"] {{
        background: var(--bg-elevated);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
    }}
    
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        border: 1px solid var(--border);
    }}
    
    .metric-card {{
        background: var(--bg-elevated);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid var(--border);
        border-left: 4px solid var(--primary);
    }}
    
    .success-box {{
        background: rgba(16, 185, 129, 0.08);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #10b981;
    }}
    
    .warning-box {{
        background: rgba(245, 158, 11, 0.08);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #f59e0b;
    }}
    
    .danger-box {{
        background: rgba(239, 68, 68, 0.08);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #ef4444;
    }}
    </style>
    ''', unsafe_allow_html=True)