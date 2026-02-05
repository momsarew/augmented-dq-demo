"""
=============================================================================
MODULE DE SÉCURITÉ - Framework Probabiliste DQ
=============================================================================

Ce module centralise toutes les fonctions de sécurité pour l'application :
- Sanitisation HTML/XSS
- Validation des uploads
- Validation des entrées utilisateur
- Gestion sécurisée des erreurs

=============================================================================
"""

import re
import html
import hashlib
from typing import Optional, Tuple, Any
import pandas as pd
from io import BytesIO

# =============================================================================
# CONSTANTES DE SÉCURITÉ
# =============================================================================

# Taille maximale des fichiers uploadés (50 MB)
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Extensions autorisées
ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

# MIME types autorisés
ALLOWED_MIME_TYPES = {
    'text/csv',
    'application/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'application/octet-stream',  # Parfois utilisé par les navigateurs
}

# Longueurs maximales pour les inputs
MAX_INPUT_LENGTH = 500
MAX_COLUMN_NAME_LENGTH = 100
MAX_CELL_VALUE_LENGTH = 10000

# Patterns dangereux à bloquer
DANGEROUS_PATTERNS = [
    r'<script',
    r'javascript:',
    r'on\w+\s*=',  # onclick, onload, etc.
    r'<iframe',
    r'<object',
    r'<embed',
    r'<link',
    r'<meta',
    r'expression\s*\(',
    r'vbscript:',
    r'data:text/html',
]

DANGEROUS_REGEX = re.compile('|'.join(DANGEROUS_PATTERNS), re.IGNORECASE)


# =============================================================================
# SANITISATION HTML/XSS
# =============================================================================

def escape_html(text: Any) -> str:
    """
    Échappe les caractères HTML dangereux pour prévenir les attaques XSS.

    Args:
        text: Texte à échapper (peut être n'importe quel type)

    Returns:
        Texte échappé sécurisé pour l'affichage HTML
    """
    if text is None:
        return ""

    # Convertir en string
    text_str = str(text)

    # Échapper les caractères HTML
    escaped = html.escape(text_str, quote=True)

    return escaped


def sanitize_for_html(text: Any, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Sanitise un texte pour une utilisation sûre dans du HTML.

    Args:
        text: Texte à sanitiser
        max_length: Longueur maximale autorisée

    Returns:
        Texte sanitisé
    """
    if text is None:
        return ""

    text_str = str(text)

    # Tronquer si trop long
    if len(text_str) > max_length:
        text_str = text_str[:max_length] + "..."

    # Supprimer les patterns dangereux
    text_str = DANGEROUS_REGEX.sub('', text_str)

    # Échapper HTML
    return escape_html(text_str)


def sanitize_column_name(name: Any) -> str:
    """
    Sanitise un nom de colonne pour un affichage sûr.

    Args:
        name: Nom de colonne

    Returns:
        Nom de colonne sanitisé
    """
    if name is None:
        return "Colonne_Inconnue"

    name_str = str(name)

    # Tronquer
    if len(name_str) > MAX_COLUMN_NAME_LENGTH:
        name_str = name_str[:MAX_COLUMN_NAME_LENGTH]

    # Supprimer caractères dangereux pour HTML
    name_str = DANGEROUS_REGEX.sub('', name_str)

    # Échapper HTML
    return escape_html(name_str)


def sanitize_dict_for_html(data: dict) -> dict:
    """
    Sanitise toutes les clés et valeurs string d'un dictionnaire.

    Args:
        data: Dictionnaire à sanitiser

    Returns:
        Dictionnaire sanitisé
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        safe_key = sanitize_column_name(key)

        if isinstance(value, str):
            safe_value = sanitize_for_html(value)
        elif isinstance(value, dict):
            safe_value = sanitize_dict_for_html(value)
        elif isinstance(value, list):
            safe_value = [sanitize_for_html(v) if isinstance(v, str) else v for v in value]
        else:
            safe_value = value

        sanitized[safe_key] = safe_value

    return sanitized


# =============================================================================
# VALIDATION DES FICHIERS UPLOADÉS
# =============================================================================

def validate_uploaded_file(uploaded_file) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Valide un fichier uploadé avant traitement.

    Args:
        uploaded_file: Fichier Streamlit uploadé

    Returns:
        Tuple (is_valid, error_message, dataframe)
    """
    if uploaded_file is None:
        return False, "Aucun fichier fourni", None

    # 1. Vérifier la taille
    file_size = uploaded_file.size
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"Fichier trop volumineux ({file_size / 1024 / 1024:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB", None

    if file_size == 0:
        return False, "Le fichier est vide", None

    # 2. Vérifier l'extension
    filename = uploaded_file.name.lower()
    extension = None
    for ext in ALLOWED_EXTENSIONS:
        if filename.endswith(ext):
            extension = ext
            break

    if extension is None:
        return False, f"Extension non autorisée. Extensions acceptées: {', '.join(ALLOWED_EXTENSIONS)}", None

    # 3. Vérifier le MIME type (si disponible)
    if hasattr(uploaded_file, 'type') and uploaded_file.type:
        if uploaded_file.type not in ALLOWED_MIME_TYPES:
            # Warning mais on continue (certains navigateurs envoient des MIME types incorrects)
            pass

    # 4. Tenter de lire le fichier pour vérifier son intégrité
    try:
        # Réinitialiser le curseur
        uploaded_file.seek(0)

        if extension == '.csv':
            # Lire avec des limites de sécurité
            df = pd.read_csv(
                uploaded_file,
                nrows=100000,  # Limite de lignes
                low_memory=True,
                on_bad_lines='skip'  # Ignorer les lignes mal formées
            )
        else:  # Excel
            df = pd.read_excel(
                uploaded_file,
                nrows=100000,
                engine='openpyxl'
            )

        # 5. Vérifier que le DataFrame n'est pas vide
        if df.empty:
            return False, "Le fichier ne contient aucune donnée", None

        # 6. Vérifier le nombre de colonnes (limite raisonnable)
        if len(df.columns) > 500:
            return False, f"Trop de colonnes ({len(df.columns)}). Maximum: 500", None

        # 7. Sanitiser les noms de colonnes
        df.columns = [sanitize_column_name(col) for col in df.columns]

        # 8. Vérifier les noms de colonnes pour patterns dangereux
        for col in df.columns:
            if DANGEROUS_REGEX.search(str(col)):
                # Le nom a déjà été sanitisé, mais on log l'événement
                pass

        return True, "", df

    except pd.errors.EmptyDataError:
        return False, "Le fichier est vide ou mal formaté", None
    except pd.errors.ParserError as e:
        return False, f"Erreur de parsing: le fichier est corrompu ou mal formaté", None
    except Exception as e:
        # Ne pas exposer les détails de l'erreur
        return False, "Impossible de lire le fichier. Vérifiez son format.", None


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitise un DataFrame pour un traitement sûr.

    Args:
        df: DataFrame à sanitiser

    Returns:
        DataFrame sanitisé
    """
    # Sanitiser les noms de colonnes
    df.columns = [sanitize_column_name(col) for col in df.columns]

    # Pour les colonnes object (strings), vérifier les patterns dangereux
    for col in df.select_dtypes(include=['object']).columns:
        # Tronquer les valeurs trop longues
        df[col] = df[col].apply(
            lambda x: str(x)[:MAX_CELL_VALUE_LENGTH] if pd.notna(x) and len(str(x)) > MAX_CELL_VALUE_LENGTH else x
        )

    return df


# =============================================================================
# VALIDATION DES ENTRÉES UTILISATEUR
# =============================================================================

def sanitize_user_input(text: str, max_length: int = MAX_INPUT_LENGTH,
                        allow_newlines: bool = False) -> str:
    """
    Sanitise une entrée utilisateur.

    Args:
        text: Texte saisi par l'utilisateur
        max_length: Longueur maximale
        allow_newlines: Autoriser les sauts de ligne

    Returns:
        Texte sanitisé
    """
    if not text:
        return ""

    text = str(text)

    # Tronquer
    if len(text) > max_length:
        text = text[:max_length]

    # Supprimer les patterns dangereux
    text = DANGEROUS_REGEX.sub('', text)

    # Supprimer les caractères de contrôle (sauf newlines si autorisés)
    if allow_newlines:
        text = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]', '', text)
    else:
        text = re.sub(r'[\x00-\x1f\x7f]', '', text)

    return text.strip()


def sanitize_filename(filename: str) -> str:
    """
    Sanitise un nom de fichier pour éviter le path traversal.

    Args:
        filename: Nom de fichier

    Returns:
        Nom de fichier sécurisé
    """
    if not filename:
        return "fichier"

    # Supprimer le chemin (path traversal)
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = filename.replace('..', '_')

    # Garder uniquement les caractères alphanumériques, tirets, underscores et points
    filename = re.sub(r'[^a-zA-Z0-9_\-.]', '_', filename)

    # Limiter la longueur
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:90]
        filename = f"{name}.{ext}" if ext else name

    return filename


def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Valide le format d'une clé API Anthropic.

    Args:
        api_key: Clé API à valider

    Returns:
        Tuple (is_valid, error_message)
    """
    if not api_key:
        return False, "Clé API non fournie"

    api_key = api_key.strip()

    # Vérifier le préfixe
    if not api_key.startswith('sk-ant-'):
        return False, "Format de clé API invalide (doit commencer par 'sk-ant-')"

    # Vérifier la longueur minimale
    if len(api_key) < 40:
        return False, "Clé API trop courte"

    # Vérifier qu'elle ne contient que des caractères valides
    if not re.match(r'^sk-ant-[a-zA-Z0-9_-]+$', api_key):
        return False, "Clé API contient des caractères invalides"

    return True, ""


# =============================================================================
# GESTION SÉCURISÉE DES ERREURS
# =============================================================================

def safe_error_message(error: Exception, context: str = "") -> str:
    """
    Génère un message d'erreur sécurisé sans exposer les détails internes.

    Args:
        error: Exception capturée
        context: Contexte de l'erreur (pour le log)

    Returns:
        Message d'erreur générique sécurisé
    """
    # Messages génériques par type d'erreur
    error_messages = {
        'FileNotFoundError': "Fichier non trouvé",
        'PermissionError': "Accès non autorisé",
        'ValueError': "Valeur invalide fournie",
        'TypeError': "Type de données incorrect",
        'KeyError': "Données manquantes",
        'IndexError': "Index hors limites",
        'ConnectionError': "Erreur de connexion",
        'TimeoutError': "Délai d'attente dépassé",
        'MemoryError': "Mémoire insuffisante",
    }

    error_type = type(error).__name__

    # Retourner un message générique
    if error_type in error_messages:
        return f"⚠️ Erreur : {error_messages[error_type]}"

    return "⚠️ Une erreur inattendue s'est produite. Veuillez réessayer."


def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """
    Log un événement de sécurité (à connecter à un système de logging).

    Args:
        event_type: Type d'événement (XSS_ATTEMPT, INVALID_UPLOAD, etc.)
        details: Détails de l'événement
        severity: Niveau de sévérité (INFO, WARNING, ERROR, CRITICAL)
    """
    # TODO: Connecter à un système de logging centralisé
    # Pour l'instant, on ne fait rien pour ne pas exposer de logs en console
    pass


# =============================================================================
# UTILITAIRES
# =============================================================================

def hash_sensitive_data(data: str) -> str:
    """
    Hash des données sensibles pour le logging sécurisé.

    Args:
        data: Données à hasher

    Returns:
        Hash SHA-256 tronqué
    """
    if not data:
        return "empty"

    return hashlib.sha256(data.encode()).hexdigest()[:16]


def mask_api_key(api_key: str) -> str:
    """
    Masque une clé API pour l'affichage sécurisé.

    Args:
        api_key: Clé API

    Returns:
        Clé masquée (ex: "sk-ant-***...***xyz")
    """
    if not api_key or len(api_key) < 10:
        return "***"

    return f"{api_key[:7]}***...***{api_key[-3:]}"
