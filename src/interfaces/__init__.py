"""
Interfaces y abstracciones para el sistema de Marketing Script.
Define contratos para mantener bajo acoplamiento y alta cohesión.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Protocol
from pathlib import Path


class ILogger(Protocol):
    """Interfaz para logging."""

    def info(self, message: str) -> None:
        ...

    def error(self, message: str, exc: Optional[Exception] = None) -> None:
        ...

    def warning(self, message: str) -> None:
        ...

    def debug(self, message: str) -> None:
        ...


class IBusinessDataSource(ABC):
    """Interfaz para fuentes de datos de negocios."""

    @abstractmethod
    def search_businesses(self, city: str, business_type: str, limit: int) -> List[Dict]:
        """Busca negocios por ciudad y tipo."""
        pass

    @abstractmethod
    def get_business_details(self, business_id: str) -> Optional[Dict]:
        """Obtiene detalles completos de un negocio."""
        pass


class IContactInfoExtractor(ABC):
    """Interfaz para extracción de información de contacto."""

    @abstractmethod
    def extract_contacts(self, business_data: Dict) -> Dict:
        """Extrae información de contacto de datos de negocio."""
        pass

    @abstractmethod
    def validate_contact_info(self, contact_info: Dict) -> bool:
        """Valida que la información de contacto sea completa."""
        pass


class IDataProcessor(ABC):
    """Interfaz para procesamiento de datos."""

    @abstractmethod
    def process_business_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Procesa datos crudos de negocios."""
        pass

    @abstractmethod
    def filter_by_contact_info(self, data: List[Dict]) -> List[Dict]:
        """Filtra datos que tienen información de contacto válida."""
        pass


class IDataWriter(ABC):
    """Interfaz para escritura de datos."""

    @abstractmethod
    def write_data(self, data: List[Dict], filepath: Path) -> None:
        """Escribe datos a un archivo."""
        pass

    @abstractmethod
    def merge_data(self, new_data: List[Dict], existing_file: Path) -> Path:
        """Fusiona nuevos datos con archivo existente."""
        pass


class IDuplicateDetector(ABC):
    """Interfaz para detección de duplicados."""

    @abstractmethod
    def find_duplicates(self, new_data: List[Dict], existing_data: List[Dict]) -> Dict:
        """Encuentra duplicados entre nuevos y existentes."""
        pass

    @abstractmethod
    def remove_duplicates(self, data: List[Dict], duplicates: Dict) -> List[Dict]:
        """Remueve duplicados de los datos."""
        pass


class IConfiguration(ABC):
    """Interfaz para configuración de la aplicación."""

    @abstractmethod
    def get_api_key(self) -> str:
        """Obtiene la clave API."""
        pass

    @abstractmethod
    def get_database_path(self) -> Path:
        """Obtiene la ruta de la base de datos."""
        pass

    @abstractmethod
    def get_output_directory(self) -> Path:
        """Obtiene el directorio de salida."""
        pass

    @abstractmethod
    def get_rate_limit(self) -> int:
        """Obtiene el límite de rate para APIs."""
        pass


class IBusinessSearchService(ABC):
    """Interfaz para servicio de búsqueda de negocios."""

    @abstractmethod
    def search_businesses_with_contacts(self, city: str, business_type: str, target_count: int) -> List[Dict]:
        """Busca negocios hasta obtener target_count con información de contacto."""
        pass


class IMergeService(ABC):
    """Interfaz para servicio de merge de datos."""

    @abstractmethod
    def merge_with_existing(self, new_data: List[Dict], master_file: Path) -> Path:
        """Fusiona nuevos datos con archivo maestro."""
        pass

    @abstractmethod
    def detect_duplicates(self, new_data: List[Dict], master_file: Path) -> Dict:
        """Detecta duplicados antes del merge."""
        pass