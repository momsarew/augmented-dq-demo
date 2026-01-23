#!/usr/bin/env python3
"""
Script pour patcher app.py avec CSS V13
Usage: python patch_app_v13.py
"""

import re

# Lire le fichier app.py actuel (ou app_old.py)
try:
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
except:
    print("❌ Fichier app.py non trouvé")
    exit(1)

print("✅ Fichier app.py chargé")

# ============================================================================
# MODIFICATION 1 : Ajouter imports CSS après les imports existants
# ============================================================================

# Trouver la section imports
import_section = """
# Import CSS premium V13
from streamlit_premium_css_v13 import apply_ultra_modern_css_with_theme

# Theme session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
"""

# Chercher après "import json" ou après "import anthropic"
if "import json" in content:
    content = content.replace(
        "import json",
        f"import json\n{import_section}"
    )
    print("✅ Imports CSS ajoutés après 'import json'")
elif "import anthropic" in content:
    # Trouver la dernière occurrence d'import anthropic
    content = re.sub(
        r'(import anthropic\n)',
        f'\\1{import_section}\n',
        content,
        count=1
    )
    print("✅ Imports CSS ajoutés après 'import anthropic'")

# ============================================================================
# MODIFICATION 2 : Appliquer CSS après st.set_page_config()
# ============================================================================

css_apply = """
# Appliquer CSS ultra-moderne
apply_ultra_modern_css_with_theme(st.session_state.theme)
"""

# Chercher st.set_page_config et ajouter après
pattern = r'(st\.set_page_config\([^)]+\))'
replacement = f'\\1\n{css_apply}'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)
print("✅ CSS appliqué après st.set_page_config()")

# ============================================================================
# MODIFICATION 3 : Supprimer l'ancien CSS inline
# ============================================================================

# Supprimer le bloc CSS Custom
old_css_pattern = r'# CSS Custom\s*st\.markdown\(""".*?""",\s*unsafe_allow_html=True\)'
content = re.sub(old_css_pattern, '', content, flags=re.DOTALL)
print("✅ Ancien CSS inline supprimé")

# ============================================================================
# MODIFICATION 4 : Ajouter toggle theme avant le header
# ============================================================================

toggle_code = """
# ============================================================================
# TOGGLE THEME
# ============================================================================

col_theme, col_main = st.columns([1, 11])
with col_theme:
    theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
    if st.button(theme_icon, key="theme_toggle", help="Changer thème"):
        st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
        st.rerun()

"""

# Chercher le header et ajouter toggle avant
header_pattern = r"(st\.markdown\('<div class=\"main-header\")"
content = re.sub(
    header_pattern,
    f'{toggle_code}\\1',
    content
)
print("✅ Toggle theme ajouté")

# ============================================================================
# SAUVEGARDER
# ============================================================================

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*60)
print("🎉 PATCHING TERMINÉ !")
print("="*60)
print("\n📋 Modifications appliquées :")
print("  1. ✅ Imports CSS V13 ajoutés")
print("  2. ✅ CSS appliqué après set_page_config")
print("  3. ✅ Ancien CSS inline supprimé")
print("  4. ✅ Toggle theme ajouté")
print("\n🚀 Prochaines étapes :")
print("  git add app.py")
print("  git commit -m 'V13: CSS premium intégré automatiquement'")
print("  git push")
