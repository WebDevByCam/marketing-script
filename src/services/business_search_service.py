"""
Servicio de búsqueda de negocios.
Implementa IBusinessSearchService siguiendo SRP.
"""
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from ..interfaces import IBusinessSearchService, IBusinessDataSource, IContactInfoExtractor, ILogger
from ..utils.logger import Logger


class BusinessSearchService(IBusinessSearchService):
    """Servicio para búsqueda de negocios con información de contacto."""

    def __init__(self,
                 data_source: IBusinessDataSource,
                 contact_extractor: IContactInfoExtractor,
                 logger: ILogger = None):
        self._data_source = data_source
        self._contact_extractor = contact_extractor
        self._logger = logger or Logger()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_businesses_with_contacts(self, city: str, business_type: str, target_count: int) -> List[Dict]:
        """
        Busca negocios iterativamente hasta obtener target_count con información de contacto válida.

        Args:
            city: Ciudad de búsqueda
            business_type: Tipo de negocio
            target_count: Número objetivo de resultados válidos

        Returns:
            Lista de negocios con información de contacto válida
        """
        self._logger.info(f"Iniciando búsqueda de {target_count} {business_type} en {city}")

        valid_results = []
        search_limit = target_count * 2  # Buscar inicialmente el doble
        max_iterations = 5

        for iteration in range(max_iterations):
            if len(valid_results) >= target_count:
                break

            remaining = target_count - len(valid_results)
            current_limit = min(search_limit, remaining * 3)

            self._logger.info(f"Iteración {iteration + 1}: Buscando {current_limit} resultados adicionales")

            try:
                # Buscar datos crudos
                raw_results = self._data_source.search_businesses(city, business_type, current_limit)

                if not raw_results:
                    self._logger.warning(f"No se encontraron resultados en iteración {iteration + 1}")
                    break

                # Procesar y validar contactos
                for business in raw_results:
                    if len(valid_results) >= target_count:
                        break

                    try:
                        contact_info = self._contact_extractor.extract_contacts(business)

                        if self._contact_extractor.validate_contact_info(contact_info):
                            # Combinar datos del negocio con información de contacto
                            enriched_business = {**business, **contact_info}
                            valid_results.append(enriched_business)
                            self._logger.debug(f"Resultado válido encontrado: {business.get('name', 'Unknown')}")

                    except Exception as e:
                        self._logger.warning(f"Error procesando negocio {business.get('name', 'Unknown')}: {e}")
                        continue

                search_limit *= 2  # Duplicar límite para siguiente iteración

            except Exception as e:
                self._logger.error(f"Error en iteración {iteration + 1}", exc=e)
                break

        self._logger.info(f"Búsqueda completada: {len(valid_results)} resultados válidos de {target_count} solicitados")

        return valid_results[:target_count]  # Asegurar no exceder el límite solicitado