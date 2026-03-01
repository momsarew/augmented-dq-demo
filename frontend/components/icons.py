"""
Icones centralisees pour l'application.

Utilise les Material Symbols de Streamlit (syntaxe :material/icon_name:)
pour un rendu professionnel et coherent.

Reference des icones : https://fonts.google.com/icons
"""

# ---------------------------------------------------------------------------
# Onglets de navigation
# ---------------------------------------------------------------------------
TAB_ICONS = {
    "home": ":material/home:",
    "scan": ":material/search:",
    "dashboard": ":material/dashboard:",
    "vectors": ":material/target:",
    "priorities": ":material/priority_high:",
    "elicitation": ":material/tune:",
    "risk_profile": ":material/shield:",
    "lineage": ":material/account_tree:",
    "dama": ":material/compare:",
    "reporting": ":material/description:",
    "contracts": ":material/handshake:",
    "history": ":material/history:",
    "settings": ":material/settings:",
    "help": ":material/help:",
}

# Labels d'onglets (icone Material + texte)
TAB_LABELS = {
    "home": f"{TAB_ICONS['home']} Accueil",
    "scan": f"{TAB_ICONS['scan']} Scan",
    "dashboard": f"{TAB_ICONS['dashboard']} Dashboard",
    "vectors": f"{TAB_ICONS['vectors']} Vecteurs",
    "priorities": f"{TAB_ICONS['priorities']} Priorites",
    "elicitation": f"{TAB_ICONS['elicitation']} Elicitation",
    "risk_profile": f"{TAB_ICONS['risk_profile']} Profil Risque",
    "lineage": f"{TAB_ICONS['lineage']} Lineage",
    "dama": f"{TAB_ICONS['dama']} DAMA",
    "reporting": f"{TAB_ICONS['reporting']} Reporting",
    "contracts": f"{TAB_ICONS['contracts']} Contracts",
    "history": f"{TAB_ICONS['history']} Historique",
    "settings": f"{TAB_ICONS['settings']} Parametres",
    "help": f"{TAB_ICONS['help']} Aide",
}

# ---------------------------------------------------------------------------
# Statuts et indicateurs
# ---------------------------------------------------------------------------
STATUS = {
    "success": ":material/check_circle:",
    "error": ":material/error:",
    "warning": ":material/warning:",
    "info": ":material/info:",
    "critical": ":material/dangerous:",
}

# Indicateurs de severite pour les textes inline (caracteres simples)
SEVERITY_DOTS = {
    "CRITIQUE": "●",  # Rouge (a colorer via CSS/HTML)
    "ELEVE": "●",
    "MOYEN": "●",
    "FAIBLE": "●",
    "VARIABLE": "○",
}

# ---------------------------------------------------------------------------
# Dimensions 4D
# ---------------------------------------------------------------------------
DIM_ICONS = {
    "DB": ":material/database:",
    "DP": ":material/sync_alt:",
    "BR": ":material/gavel:",
    "UP": ":material/visibility:",
}

# ---------------------------------------------------------------------------
# Dimensions DAMA / ISO 8000
# ---------------------------------------------------------------------------
DAMA_ICONS = {
    "completeness": ":material/pie_chart:",
    "consistency": ":material/link:",
    "accuracy": ":material/target:",
    "timeliness": ":material/schedule:",
    "validity": ":material/verified:",
    "uniqueness": ":material/fingerprint:",
}

# ---------------------------------------------------------------------------
# Profils metier
# ---------------------------------------------------------------------------
PROFIL_ICONS = {
    "cfo": ":material/payments:",
    "data_engineer": ":material/engineering:",
    "drh": ":material/groups:",
    "auditeur": ":material/policy:",
    "gouvernance": ":material/monitoring:",
    "manager_ops": ":material/bolt:",
    "custom": ":material/edit:",
}

# ---------------------------------------------------------------------------
# Profils de risque
# ---------------------------------------------------------------------------
RISK_PROFIL_ICONS = {
    "tres_prudent": ":material/security:",
    "prudent": ":material/lock:",
    "equilibre": ":material/balance:",
    "tolerant": ":material/target:",
    "tres_tolerant": ":material/rocket_launch:",
}

# ---------------------------------------------------------------------------
# Actions et operations
# ---------------------------------------------------------------------------
ACTION_ICONS = {
    "upload": ":material/upload_file:",
    "download": ":material/download:",
    "export": ":material/ios_share:",
    "analyze": ":material/analytics:",
    "generate": ":material/auto_fix_high:",
    "save": ":material/save:",
    "delete": ":material/delete:",
    "refresh": ":material/refresh:",
    "expand": ":material/expand_more:",
    "filter": ":material/filter_list:",
    "ai": ":material/smart_toy:",
}

# ---------------------------------------------------------------------------
# Detection (Auto / Semi / Manuel)
# ---------------------------------------------------------------------------
DETECTION_ICONS = {
    "Auto": ":material/auto_mode:",
    "Semi": ":material/touch_app:",
    "Manuel": ":material/edit_note:",
}

# Versions texte pour les tableaux inline
DETECTION_DOTS = {
    "Auto": "● Auto",
    "Semi": "◐ Semi",
    "Manuel": "○ Manuel",
}

# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
AUDIT_ICONS = {
    "FILE_UPLOAD": ":material/upload_file:",
    "FILE_EXPORT": ":material/ios_share:",
    "ANALYSIS": ":material/analytics:",
    "CALCULATION": ":material/calculate:",
    "SCORE": ":material/score:",
    "DAMA": ":material/compare:",
    "AHP": ":material/balance:",
    "PROFILE": ":material/person:",
    "LINEAGE": ":material/account_tree:",
    "AI_REQUEST": ":material/smart_toy:",
    "REPORT": ":material/description:",
    "CONFIG": ":material/settings:",
    "ADMIN": ":material/admin_panel_settings:",
    "ERROR": ":material/error:",
    "SESSION": ":material/play_circle:",
}

SEVERITY_ICONS = {
    "INFO": ":material/info:",
    "SUCCESS": ":material/check_circle:",
    "WARNING": ":material/warning:",
    "ERROR": ":material/error:",
    "CRITICAL": ":material/dangerous:",
}
