"""
Detector de duplicados.
Implementa IDuplicateDetector siguiendo SRP.
"""
from typing import List, Dict, Any
import pandas as pd
from difflib import SequenceMatcher

from ..interfaces import IDuplicateDetector, ILogger
from ..utils.logger import Logger


class DuplicateDetector(IDuplicateDetector):
    """Servicio para detectar registros duplicados en datos de negocios."""

    def __init__(self,
                 similarity_threshold: float = 0.85,
                 logger: ILogger = None):
        self._similarity_threshold = similarity_threshold
        self._logger = logger or Logger()

    def detect_duplicates(self, data: pd.DataFrame) -> pd.Series:
        """
        Detecta registros duplicados basándose en similitud de nombre y dirección.

        Args:
            data: DataFrame con datos de negocios

        Returns:
            Series booleana indicando cuáles registros son duplicados
        """
        self._logger.info(f"Detectando duplicados en {len(data)} registros")

        if data.empty:
            return pd.Series([], dtype=bool)

        try:
            # Inicializar máscara de duplicados
            duplicates_mask = pd.Series(False, index=data.index)

            # Campos para comparación
            name_field = self._find_field(data.columns, ['name', 'business_name', 'company'])
            address_field = self._find_field(data.columns, ['address', 'location', 'addr'])

            if not name_field:
                self._logger.warning("No se encontró campo de nombre para detección de duplicados")
                return duplicates_mask

            # Procesar cada registro
            for idx, row in data.iterrows():
                if duplicates_mask[idx]:
                    continue  # Ya marcado como duplicado

                current_name = str(row.get(name_field, '')).strip().lower()
                current_address = str(row.get(address_field, '')).strip().lower() if address_field else ''

                # Comparar con registros posteriores
                for compare_idx in data.index[data.index > idx]:
                    if duplicates_mask[compare_idx]:
                        continue

                    compare_name = str(data.loc[compare_idx, name_field]).strip().lower()
                    compare_address = (str(data.loc[compare_idx, address_field]).strip().lower()
                                     if address_field else '')

                    # Calcular similitud
                    name_similarity = self._calculate_similarity(current_name, compare_name)

                    # Si los nombres son muy similares
                    if name_similarity >= self._similarity_threshold:
                        # Verificar dirección si está disponible
                        address_similarity = (self._calculate_similarity(current_address, compare_address)
                                            if current_address and compare_address else 0.0)

                        # Considerar duplicado si nombre es muy similar y dirección también (o no hay dirección)
                        if (not current_address or not compare_address or
                            address_similarity >= self._similarity_threshold):
                            duplicates_mask[compare_idx] = True
                            self._logger.debug(f"Duplicado detectado: '{current_name}' ~ '{compare_name}' "
                                             f"(similitud: {name_similarity:.2f})")

            duplicate_count = duplicates_mask.sum()
            self._logger.info(f"Detectados {duplicate_count} registros duplicados")

            return duplicates_mask

        except Exception as e:
            self._logger.error("Error detectando duplicados", exc=e)
            raise

    def find_similar_businesses(self, data: pd.DataFrame,
                               target_business: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Encuentra negocios similares a uno objetivo.

        Args:
            data: DataFrame con datos de negocios
            target_business: Diccionario con datos del negocio objetivo

        Returns:
            Lista de negocios similares
        """
        self._logger.debug("Buscando negocios similares")

        try:
            similar_businesses = []

            target_name = str(target_business.get('name', '')).strip().lower()
            target_address = str(target_business.get('address', '')).strip().lower()

            name_field = self._find_field(data.columns, ['name', 'business_name', 'company'])
            address_field = self._find_field(data.columns, ['address', 'location', 'addr'])

            if not name_field:
                return similar_businesses

            for _, row in data.iterrows():
                name = str(row.get(name_field, '')).strip().lower()
                address = str(row.get(address_field, '')).strip().lower() if address_field else ''

                name_similarity = self._calculate_similarity(target_name, name)
                address_similarity = (self._calculate_similarity(target_address, address)
                                    if target_address and address else 0.0)

                # Considerar similar si el nombre es bastante similar
                if name_similarity >= 0.7:
                    similarity_score = (name_similarity + address_similarity) / 2 if address_similarity > 0 else name_similarity

                    similar_business = row.to_dict()
                    similar_business['_similarity_score'] = similarity_score
                    similar_businesses.append(similar_business)

            # Ordenar por similitud descendente
            similar_businesses.sort(key=lambda x: x['_similarity_score'], reverse=True)

            self._logger.debug(f"Encontrados {len(similar_businesses)} negocios similares")

            return similar_businesses

        except Exception as e:
            self._logger.error("Error buscando negocios similares", exc=e)
            raise

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similitud entre dos textos usando SequenceMatcher."""
        if not text1 or not text2:
            return 0.0

        # Usar SequenceMatcher para calcular similitud
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()

    def _find_field(self, columns: pd.Index, possible_names: List[str]) -> str:
        """Encuentra el nombre de campo más probable de una lista de opciones."""
        columns_lower = columns.str.lower()

        for name in possible_names:
            if name.lower() in columns_lower:
                return columns[columns_lower == name.lower()].iloc[0]

        return None