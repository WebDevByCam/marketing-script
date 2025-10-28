"""
Utilidades del sistema de marketing.
"""

# Importar logger
from .logger import Logger, logger

# Importar funciones de utils.py usando importlib para evitar conflictos
import importlib.util
import os

utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils.py')
spec = importlib.util.spec_from_file_location("utils_module", utils_path)
utils_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils_module)

# Exponer las funciones
safe_get = utils_module.safe_get
normalize_url = utils_module.normalize_url
validate_email = utils_module.validate_email
clean_phone = utils_module.clean_phone
same_registrable_domain = utils_module.same_registrable_domain
EMAIL_REGEX = utils_module.EMAIL_REGEX

__all__ = [
    'Logger', 'logger',
    'safe_get', 'normalize_url', 'validate_email', 'clean_phone',
    'same_registrable_domain', 'EMAIL_REGEX'
]