"""
Utilidades generales para el script de marketing.
"""
import re
from urllib.parse import urlparse
import tldextract


EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)


def normalize_url(url: str) -> str:
    """Normaliza una URL añadiendo https:// si no tiene esquema y removiendo fragmentos."""
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    url = url.split("#")[0]
    return url


def same_registrable_domain(url_a: str, url_b: str) -> bool:
    """Verifica si dos URLs pertenecen al mismo dominio registrable."""
    try:
        da = tldextract.extract(url_a)
        db = tldextract.extract(url_b)
        return (da.domain, da.suffix) == (db.domain, db.suffix) and da.domain != "" and da.suffix != ""
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Valida que un email tenga formato correcto."""
    return bool(EMAIL_REGEX.match(email))


def clean_phone(phone: str) -> str:
    """Limpia y normaliza un número de teléfono."""
    if not phone:
        return ""
    # Remover caracteres no numéricos excepto + al inicio
    cleaned = re.sub(r'[^\d+]', '', phone)
    if cleaned.startswith('+'):
        return cleaned
    return cleaned


def safe_get(data: dict, *keys, default=""):
    """Obtiene un valor de un diccionario anidado de forma segura."""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data or default