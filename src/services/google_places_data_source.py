"""
Fuente de datos de Google Places API.
Implementa IBusinessDataSource siguiendo SRP.
"""
from typing import List, Dict, Any
import requests
import time
from urllib.parse import urlencode

from ..interfaces import IBusinessDataSource, ILogger
from ..utils.logger import Logger


class GooglePlacesDataSource(IBusinessDataSource):
    """Fuente de datos que obtiene información de negocios desde Google Places API."""

    def __init__(self, api_key: str, logger: ILogger = None):
        self._api_key = api_key
        self._base_url = "https://maps.googleapis.com/maps/api/place"
        self._logger = logger or Logger()

    def search_businesses(self, city: str, business_type: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca negocios usando Google Places API.

        Args:
            city: Ciudad de búsqueda
            business_type: Tipo de negocio
            limit: Número máximo de resultados

        Returns:
            Lista de diccionarios con información de negocios
        """
        self._logger.info(f"Buscando {business_type} en {city} (límite: {limit})")

        try:
            # Primera búsqueda: Text Search para encontrar lugares
            text_results = self._text_search(city, business_type, limit)

            if not text_results:
                self._logger.warning("No se encontraron resultados en text search")
                return []

            # Obtener detalles completos para cada lugar
            detailed_results = []
            for place in text_results[:limit]:
                place_id = place.get('place_id')
                if place_id:
                    details = self._get_place_details(place_id)
                    if details:
                        detailed_results.append(details)
                        time.sleep(0.1)  # Rate limiting

            self._logger.info(f"Obtenidos {len(detailed_results)} resultados detallados")

            return detailed_results

        except Exception as e:
            self._logger.error("Error buscando negocios", exc=e)
            raise

    def _text_search(self, city: str, business_type: str, limit: int) -> List[Dict[str, Any]]:
        """Realiza búsqueda de texto usando Places API Text Search."""
        query = f"{business_type} in {city}"

        params = {
            'query': query,
            'key': self._api_key,
            'maxprice': 4,  # No limit on price
            'type': self._map_business_type(business_type)
        }

        url = f"{self._base_url}/textsearch/json"

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 'OK':
                self._logger.warning(f"Text search failed: {data.get('status')}")
                return []

            results = data.get('results', [])
            self._logger.debug(f"Text search encontró {len(results)} resultados")

            return results

        except requests.RequestException as e:
            self._logger.error(f"Error en text search request: {e}")
            raise

    def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Obtiene detalles completos de un lugar usando Place Details API."""
        params = {
            'place_id': place_id,
            'key': self._api_key,
            'fields': 'name,formatted_address,formatted_phone_number,website,types,geometry,place_id'
        }

        url = f"{self._base_url}/details/json"

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 'OK':
                self._logger.warning(f"Place details failed for {place_id}: {data.get('status')}")
                return None

            result = data.get('result', {})

            # Estructurar el resultado
            business_data = {
                'place_id': result.get('place_id'),
                'name': result.get('name'),
                'address': result.get('formatted_address'),
                'phone': result.get('formatted_phone_number'),
                'website': result.get('website'),
                'types': result.get('types', []),
                'latitude': result.get('geometry', {}).get('location', {}).get('lat'),
                'longitude': result.get('geometry', {}).get('location', {}).get('lng'),
                'source': 'google_places'
            }

            return business_data

        except requests.RequestException as e:
            self._logger.error(f"Error obteniendo detalles del lugar {place_id}: {e}")
            return None

    def _map_business_type(self, business_type: str) -> str:
        """Mapea tipos de negocio a tipos de Places API."""
        type_mapping = {
            'restaurant': 'restaurant',
            'hotel': 'lodging',
            'store': 'store',
            'bar': 'bar',
            'cafe': 'cafe',
            'doctor': 'doctor',
            'dentist': 'dentist',
            'lawyer': 'lawyer',
            'school': 'school',
            'bank': 'bank',
            'pharmacy': 'pharmacy',
            'gym': 'gym',
            'spa': 'spa',
            'salon': 'beauty_salon'
        }

        # Buscar coincidencia exacta primero
        business_lower = business_type.lower()
        if business_lower in type_mapping:
            return type_mapping[business_lower]

        # Buscar coincidencia parcial
        for key, value in type_mapping.items():
            if key in business_lower:
                return value

        # Tipo por defecto
        return 'establishment'