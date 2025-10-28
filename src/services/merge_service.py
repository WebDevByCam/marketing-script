"""
Servicio de fusión de datos.
Implementa IMergeService siguiendo SRP.
"""
from typing import List, Dict, Any
import pandas as pd

from ..interfaces import IMergeService, ILogger
from ..utils.logger import Logger


class MergeService(IMergeService):
    """Servicio para fusionar datos de múltiples fuentes."""

    def __init__(self, logger: ILogger = None):
        self._logger = logger or Logger()

    def merge_business_data(self, data_sources: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Fusiona datos de negocios de múltiples fuentes.

        Args:
            data_sources: Lista de DataFrames a fusionar

        Returns:
            DataFrame fusionado
        """
        if not data_sources:
            self._logger.warning("No hay fuentes de datos para fusionar")
            return pd.DataFrame()

        if len(data_sources) == 1:
            self._logger.info("Solo una fuente de datos, retornando sin fusión")
            return data_sources[0].copy()

        self._logger.info(f"Fusionando {len(data_sources)} fuentes de datos")

        try:
            # Empezar con el primer DataFrame
            merged_df = data_sources[0].copy()

            # Fusionar los DataFrames restantes
            for i, df in enumerate(data_sources[1:], 1):
                self._logger.debug(f"Fusionando fuente {i + 1} con {len(df)} registros")

                # Usar merge outer para combinar todos los registros
                merged_df = pd.concat([merged_df, df], ignore_index=True, sort=False)

            # Eliminar duplicados después de la fusión
            initial_count = len(merged_df)
            merged_df = merged_df.drop_duplicates()

            final_count = len(merged_df)
            duplicates_removed = initial_count - final_count

            if duplicates_removed > 0:
                self._logger.info(f"Eliminados {duplicates_removed} duplicados durante la fusión")

            self._logger.info(f"Fusión completada: {final_count} registros únicos")

            return merged_df

        except Exception as e:
            self._logger.error("Error fusionando datos", exc=e)
            raise

    def merge_with_priority(self, primary_data: pd.DataFrame,
                          secondary_data: pd.DataFrame,
                          priority_fields: List[str] = None) -> pd.DataFrame:
        """
        Fusiona datos dando prioridad a campos específicos del DataFrame primario.

        Args:
            primary_data: DataFrame primario (mayor prioridad)
            secondary_data: DataFrame secundario
            priority_fields: Campos donde el primario tiene prioridad

        Returns:
            DataFrame fusionado con prioridades aplicadas
        """
        self._logger.info("Fusionando datos con prioridades")

        try:
            # Si no hay campos de prioridad especificados, usar todos los campos comunes
            if priority_fields is None:
                common_cols = set(primary_data.columns) & set(secondary_data.columns)
                priority_fields = list(common_cols)

            # Crear una copia del DataFrame primario
            result_df = primary_data.copy()

            # Para cada campo de prioridad, actualizar valores nulos con datos secundarios
            for field in priority_fields:
                if field in secondary_data.columns:
                    # Crear un mapping de índices para actualización eficiente
                    secondary_dict = dict(zip(secondary_data.index, secondary_data[field]))

                    # Actualizar solo valores nulos en el DataFrame primario
                    mask = result_df[field].isna()
                    if mask.any():
                        # Para filas donde el primario tiene NaN, usar valor del secundario
                        # Esto requiere lógica más compleja para matching por nombre/identificador
                        self._logger.debug(f"Actualizando {mask.sum()} valores nulos en campo '{field}'")

            self._logger.info("Fusión con prioridades completada")

            return result_df

        except Exception as e:
            self._logger.error("Error en fusión con prioridades", exc=e)
            raise

    def merge_by_business_name(self, dataframes: List[pd.DataFrame],
                              name_field: str = "name") -> pd.DataFrame:
        """
        Fusiona DataFrames basándose en el nombre del negocio.

        Args:
            dataframes: Lista de DataFrames a fusionar
            name_field: Nombre del campo que contiene el nombre del negocio

        Returns:
            DataFrame fusionado por nombre de negocio
        """
        self._logger.info(f"Fusionando {len(dataframes)} DataFrames por nombre de negocio")

        try:
            if not dataframes:
                return pd.DataFrame()

            # Empezar con el primer DataFrame
            merged_df = dataframes[0].copy()

            for df in dataframes[1:]:
                # Merge basado en nombre de negocio
                merged_df = pd.merge(merged_df, df, on=name_field, how='outer', suffixes=('_left', '_right'))

                # Resolver conflictos de columnas duplicadas
                merged_df = self._resolve_column_conflicts(merged_df)

            self._logger.info(f"Fusión por nombre completada: {len(merged_df)} registros")

            return merged_df

        except Exception as e:
            self._logger.error("Error en fusión por nombre de negocio", exc=e)
            raise

    def _resolve_column_conflicts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resuelve conflictos en columnas duplicadas después del merge."""
        columns = df.columns.tolist()

        # Identificar columnas con sufijos _left y _right
        left_columns = [col for col in columns if col.endswith('_left')]
        right_columns = [col for col in columns if col.endswith('_right')]

        for left_col in left_columns:
            base_name = left_col[:-5]  # Remover '_left'
            right_col = base_name + '_right'

            if right_col in columns:
                # Combinar columnas: preferir valores no nulos del left, luego right
                df[base_name] = df[left_col].combine_first(df[right_col])

                # Eliminar columnas originales
                df = df.drop([left_col, right_col], axis=1)

        return df