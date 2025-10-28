"""
Configuración centralizada de la aplicación.
Sigue el patrón Singleton para configuración global.
"""
import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

from ..interfaces import IConfiguration


class AppConfig(IConfiguration):
    """Configuración centralizada usando variables de entorno."""

    _instance: Optional['AppConfig'] = None

    def __new__(cls) -> 'AppConfig':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Carga la configuración desde variables de entorno."""
        load_dotenv()

        # API Configuration
        self._api_key = os.getenv('GOOGLE_API_KEY', '')

        # Path Configuration
        self._project_root = Path(__file__).parent.parent.parent
        self._data_dir = self._project_root / 'data'
        self._input_dir = self._data_dir / 'input'
        self._output_dir = self._data_dir / 'output'
        self._merged_dir = self._data_dir / 'merged'

        # Rate Limiting
        self._rate_limit = int(os.getenv('RATE_LIMIT_PER_MINUTE', '600'))

        # Auth Configuration
        self._auth_users = os.getenv('AUTH_USERS', 'admin')
        self._auth_passwords = os.getenv('AUTH_PASSWORDS', 'admin123')
        self._auth_names = os.getenv('AUTH_NAMES', 'Administrador')

        # Ensure directories exist
        self._create_directories()

    def _create_directories(self) -> None:
        """Crea directorios necesarios si no existen."""
        for directory in [self._data_dir, self._input_dir, self._output_dir, self._merged_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def api_key(self) -> str:
        """Obtiene la clave API de Google Places."""
        if not self._api_key:
            raise ValueError("GOOGLE_API_KEY no configurada en variables de entorno")
        return self._api_key

    def get_api_key(self) -> str:
        return self.api_key

    def get_database_path(self) -> Path:
        return self._project_root / 'marketing_script.db'

    def get_output_directory(self) -> Path:
        return self._output_dir

    def get_input_directory(self) -> Path:
        return self._input_dir

    def get_merged_directory(self) -> Path:
        return self._merged_dir

    def get_rate_limit(self) -> int:
        return self._rate_limit

    def get_auth_config(self) -> Dict:
        """Obtiene configuración de autenticación."""
        usernames = [u.strip() for u in self._auth_users.split(',')]
        passwords = [p.strip() for p in self._auth_passwords.split(',')]
        names = [n.strip() for n in self._auth_names.split(',')]

        # Ensure all lists have same length
        min_length = min(len(usernames), len(passwords), len(names))
        usernames = usernames[:min_length]
        passwords = passwords[:min_length]
        names = names[:min_length]

        return {
            "usernames": {
                usernames[i]: {
                    "name": names[i],
                    "password": passwords[i]
                }
                for i in range(len(usernames))
            }
        }


# Global config instance
config = AppConfig()