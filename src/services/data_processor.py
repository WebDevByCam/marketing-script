"""
Servicio de procesamiento de datos.
Implementa IDataProcessor siguiendo SRP.
"""
from typing import List, Dict, Any
import pandas as pd

from ..interfaces import IDataProcessor, IDuplicateDetector, ILogger
from ..utils.logger import Logger


class DataProcessor(IDataProcessor):
    """Servicio para procesamiento y limpieza de datos de negocios."""

    def __init__(self,
                 duplicate_detector: IDuplicateDetector,
                 logger: ILogger = None):
        self._duplicate_detector = duplicate_detector
        self._logger = logger or Logger()

    def process_business_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Procesa datos crudos de negocios aplicando limpieza y validación.

        Args:
            raw_data: Lista de diccionarios con datos de negocios

        Returns:
            DataFrame procesado y limpio
        """
        self._logger.info(f"Procesando {len(raw_data)} registros de datos de negocios")

        if not raw_data:
            self._logger.warning("No hay datos para procesar")
            return pd.DataFrame()

        try:
            # Convertir a DataFrame
            df = pd.DataFrame(raw_data)
            self._logger.info(f"DataFrame creado con {len(df)} filas y {len(df.columns)} columnas")

            # Limpiar datos básicos
            df = self._clean_basic_data(df)

            # Eliminar duplicados
            df = self._remove_duplicates(df)

            # Validar y filtrar datos requeridos
            df = self._validate_required_fields(df)

            # Limpiar y estandarizar campos de texto
            df = self._standardize_text_fields(df)

            self._logger.info(f"Procesamiento completado: {len(df)} registros válidos")

            return df

        except Exception as e:
            self._logger.error("Error procesando datos de negocios", exc=e)
            raise

    def _clean_basic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza básica de datos."""
        self._logger.debug("Aplicando limpieza básica de datos")

        # Eliminar filas completamente vacías
        df = df.dropna(how='all')

        # Limpiar espacios en blanco en strings
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina registros duplicados usando el detector de duplicados."""
        self._logger.debug("Eliminando registros duplicados")

        # Usar el servicio de detección de duplicados
        duplicates_mask = self._duplicate_detector.detect_duplicates(df)

        if duplicates_mask.any():
            duplicate_count = duplicates_mask.sum()
            self._logger.info(f"Eliminando {duplicate_count} registros duplicados")
            df = df[~duplicates_mask]

        return df

    def _validate_required_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Valida que los campos requeridos estén presentes."""
        self._logger.debug("Validando campos requeridos")

        required_fields = ['name', 'address', 'phone', 'email']
        existing_fields = [field for field in required_fields if field in df.columns]

        if not existing_fields:
            self._logger.warning("Ningún campo requerido encontrado en los datos")
            return df

        # Filtrar registros que tengan al menos un campo requerido no vacío
        valid_mask = df[existing_fields].notna().any(axis=1)
        invalid_count = len(df) - valid_mask.sum()

        if invalid_count > 0:
            self._logger.warning(f"Eliminando {invalid_count} registros sin información de contacto válida")
            df = df[valid_mask]

        return df

    def _standardize_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Estandariza campos de texto."""
        self._logger.debug("Estandarizando campos de texto")

        # Campos de texto a estandarizar
        text_fields = ['name', 'address', 'phone', 'email', 'website']

        for field in text_fields:
            if field in df.columns:
                # Convertir a string y limpiar
                df[field] = df[field].astype(str).str.strip()

                # Reemplazar valores vacíos con NaN
                df[field] = df[field].replace(['', 'nan', 'None', 'null'], pd.NA)

        return df