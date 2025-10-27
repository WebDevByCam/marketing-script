"""
Cliente para Google Places API.
"""
import time
from typing import List, Dict
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .utils import safe_get


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type(requests.RequestException))
def _get(url, **kwargs):
    """Realiza una petición GET con reintentos."""
    resp = requests.get(url, timeout=kwargs.pop("timeout", 12), headers=HEADERS, **kwargs)
    resp.raise_for_status()
    return resp


class PlacesAPIClient:
    """Cliente para interactuar con Google Places API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def text_search(self, query: str, limit: int = 120) -> List[Dict]:
        """Busca lugares usando text search."""
        url = f"{self.base_url}/textsearch/json"
        results = []
        pagetoken = None
        
        while len(results) < limit:
            params = {"query": query, "key": self.api_key}
            if pagetoken:
                params["pagetoken"] = pagetoken
                time.sleep(2.0)  # Requisito de Google antes de usar next_page_token
            
            try:
                r = _get(url, params=params)
                data = r.json()
                
                if data.get("status") != "OK":
                    print(f"[warn] Places API error: {data.get('status')} - {data.get('error_message', '')}")
                    break
                
                results.extend(data.get("results", []))
                pagetoken = data.get("next_page_token")
                
                if not pagetoken:
                    break
            except requests.RequestException as e:
                print(f"[error] Error en Places API: {e}")
                break
        
        return results[:limit]
    
    def place_details(self, place_id: str) -> Dict:
        """Obtiene detalles de un lugar específico."""
        url = f"{self.base_url}/details/json"
        fields = [
            "place_id", "name", "formatted_phone_number", "international_phone_number",
            "website", "formatted_address", "business_status", "url", "rating",
            "user_ratings_total", "price_level", "opening_hours"
        ]
        params = {
            "key": self.api_key,
            "place_id": place_id,
            "fields": ",".join(fields)
        }
        
        try:
            r = _get(url, params=params)
            data = r.json()
            
            if data.get("status") != "OK":
                print(f"[warn] Place details error: {data.get('status')} - {data.get('error_message', '')}")
                return {}
            
            return data.get("result", {})
        except requests.RequestException as e:
            print(f"[error] Error obteniendo detalles: {e}")
            return {}
    
    def build_query(self, city: str, business_type: str) -> str:
        """Construye una query para buscar negocios."""
        return f"{business_type} in {city}"