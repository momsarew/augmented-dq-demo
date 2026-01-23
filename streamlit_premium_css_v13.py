"""
streamlit_premium_css_v13.py
CSS ultra-moderne pour Framework Data Quality Probabiliste

Usage:
    from streamlit_premium_css_v13 import apply_ultra_modern_css_with_theme
    apply_ultra_modern_css_with_theme(st.session_state.theme)
"""

import streamlit as st

def apply_ultra_modern_css_with_theme(theme='dark'):
    """
    Applique CSS premium avec support theme clair/sombre
    Compatible avec app V10 existante
    
    Args:
        theme: 'dark' ou 'light'
    """
    
    # Variables CSS selon theme
    if theme == 'light':
        theme_vars = '''
        :root {
            /* Backgrounds */
            --bg-primary: #ffffff;
            --bg-surface: #f8f9fa;
            --bg-elevated: #ffffff;
            --bg-card: #ffffff;
            
            /* Colors */
            --primary: #6366f1;
            --primary-light: #818cf8;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            
            /* Text */
            --text-primary: #1a1a1a;
            --text-secondary: #6b7280;
            --text-muted: #9ca3af;
            
            /* Borders & Shadows */
            --border: rgba(0, 0, 0, 0.08);
            --border-hover: rgba(99, 102, 241, 0.3);
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.08);
            --shadow-glow: 0 0 0 1px rgba(99, 102, 241, 0.1), 0 8px 32px rgba(99, 102, 241, 0.15);
        }
        '''
    else:  # dark
        theme_vars = '''
        :root {
            /* Backgrounds */
            --bg-primary: #0a0a0a;
            --bg-surface: #0f0f0f;
            --bg-elevated: #1a1a1a;
            --bg-card: #141414;
            
            /* Colors */
            --primary: #6366f1;
            --primary-light: #818cf8;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            
            /* Text */
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --text-muted: #666666;
            
            /* Borders & Shadows */
            --border: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(99, 102, 241, 0.3);
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
            --shadow-glow: 0 0 0 1px rgba(99, 102, 241, 0.1), 0 8px 32px rgba(99, 102, 241, 0.15);
        }
        '''
    
    st.markdown(f'''
    <style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Theme Variables */
    {theme_vars}
    
    /* Base Styles */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    
    .stApp {{
        background: var(--bg-primary);
        color: var(--text-primary);
        transition: background 0.3s ease, color 0.3s ease;
    }}
    
    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Titles with Gradient */
    .main-header {{
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
        animation: gradient-shift 3s ease infinite;
        background-size: 200% 200%;
    }}
    
    @keyframes gradient-shift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    h1, h2, h3 {{
        color: var(--text-primary);
    }}
    
    /* Glass Cards & Containers */
    [data-testid="stExpander"],
    .element-container > div > div {{
        background: var(--bg-elevated);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border);
        border-radius: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-sm);
    }}
    
    [data-testid="stExpander"]:hover {{
        border-color: var(--border-hover);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }}
    
    /* Expander Header */
    [data-testid="stExpander"] summary {{
        padding: 1.25rem 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        transition: background 0.2s ease;
    }}
    
    [data-testid="stExpander"] summary:hover {{
        background: rgba(99, 102, 241, 0.05);
    }}
    
    /* Buttons Premium */
    .stButton > button {{
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.875rem 2rem;
        font-weight: 600;
        font-size: 0.9375rem;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .stButton > button::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.4);
    }}
    
    .stButton > button:hover::before {{
        left: 100%;
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Tabs Ultra-Modernes */
    [data-testid="stTabs"] {{
        gap: 0.5rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }}
    
    [data-testid="stTabs"] button {{
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 1rem 1.5rem;
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.9375rem;
        transition: all 0.2s ease;
        border-radius: 8px 8px 0 0;
    }}
    
    [data-testid="stTabs"] button:hover {{
        color: var(--text-primary);
        background: rgba(99, 102, 241, 0.05);
    }}
    
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--primary-light);
        border-bottom-color: var(--primary);
        background: rgba(99, 102, 241, 0.08);
    }}
    
    /* Metrics Cards */
    [data-testid="stMetric"] {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }}
    
    [data-testid="stMetric"]:hover {{
        border-color: var(--border-hover);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 0.8125rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }}
    
    [data-testid="stMetricValue"] {{
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }}
    
    /* DataFrames Premium */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }}
    
    [data-testid="stDataFrame"] thead tr {{
        background: var(--bg-elevated);
    }}
    
    [data-testid="stDataFrame"] thead th {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        padding: 1rem !important;
        border-bottom: 1px solid var(--border) !important;
    }}
    
    [data-testid="stDataFrame"] tbody tr {{
        transition: background 0.2s ease;
        border-bottom: 1px solid var(--border);
    }}
    
    [data-testid="stDataFrame"] tbody tr:hover {{
        background: rgba(99, 102, 241, 0.05);
    }}
    
    [data-testid="stDataFrame"] tbody td {{
        padding: 0.875rem 1rem !important;
        color: var(--text-secondary);
    }}
    
    /* Upload Zone Premium */
    [data-testid="stFileUploader"] {{
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.05) 0%, 
            rgba(139, 92, 246, 0.05) 100%
        );
        border: 2px dashed var(--border);
        border-radius: 20px;
        padding: 3rem 2rem;
        transition: all 0.3s ease;
        position: relative;
    }}
    
    [data-testid="stFileUploader"]:hover {{
        border-color: var(--primary);
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.08) 0%, 
            rgba(139, 92, 246, 0.08) 100%
        );
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1), 0 12px 48px rgba(99, 102, 241, 0.15);
    }}
    
    /* Progress Bar Gradient */
    .stProgress > div > div {{
        background: linear-gradient(90deg,
            var(--accent-green) 0%,
            var(--accent-orange) 50%,
            var(--accent-red) 100%
        );
        border-radius: 8px;
        height: 10px;
        position: relative;
        overflow: hidden;
    }}
    
    .stProgress > div > div::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        animation: shimmer 2s infinite;
    }}
    
    @keyframes shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}
    
    /* Plotly Charts */
    .js-plotly-plot {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
    }}
    
    /* Alerts & Info Boxes */
    [data-testid="stAlert"] {{
        border-radius: 12px;
        border: 1px solid;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }}
    
    [data-testid="stAlert"][data-baseweb="notification-info"] {{
        background: rgba(59, 130, 246, 0.08);
        border-color: rgba(59, 130, 246, 0.3);
    }}
    
    [data-testid="stAlert"][data-baseweb="notification-warning"] {{
        background: rgba(245, 158, 11, 0.08);
        border-color: rgba(245, 158, 11, 0.3);
    }}
    
    [data-testid="stAlert"][data-baseweb="notification-success"] {{
        background: rgba(16, 185, 129, 0.08);
        border-color: rgba(16, 185, 129, 0.3);
    }}
    
    /* Code Blocks */
    code {{
        font-family: 'JetBrains Mono', monospace !important;
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.875rem !important;
        color: var(--primary-light) !important;
    }}
    
    pre {{
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
    }}
    
    /* Scrollbar Custom */
    ::-webkit-scrollbar {{
        width: 12px;
        height: 12px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg-surface);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
        border-radius: 6px;
        border: 2px solid var(--bg-surface);
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(135deg, var(--primary-light) 0%, #8b5cf6 100%);
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .element-container {{
        animation: fadeIn 0.4s ease-out;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: var(--bg-surface);
        border-right: 1px solid var(--border);
    }}
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: var(--text-secondary);
    }}
    
    /* Select Boxes */
    [data-baseweb="select"],
    [data-baseweb="input"] {{
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }}
    
    [data-baseweb="select"]:hover,
    [data-baseweb="input"]:hover {{
        border-color: var(--border-hover) !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
    }}
    
    /* Custom metric boxes (from V10) */
    .metric-card {{
        background: var(--bg-elevated);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid var(--border);
        border-left: 4px solid var(--primary);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}
    
    .success-box {{
        background: rgba(16, 185, 129, 0.08);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid var(--accent-green);
    }}
    
    .warning-box {{
        background: rgba(245, 158, 11, 0.08);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid var(--accent-orange);
    }}
    
    .danger-box {{
        background: rgba(239, 68, 68, 0.08);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid var(--accent-red);
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .main-header {{
            font-size: 2rem;
        }}
        
        [data-testid="stMetricValue"] {{
            font-size: 1.75rem;
        }}
    }}
    
    </style>
    ''', unsafe_allow_html=True)
