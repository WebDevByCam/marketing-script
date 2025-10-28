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
    
    def __init__(self, api_key: str, rate_limit_per_minute: int = 600):
        self.api_key = api_key
        self.base_url = "https://places.googleapis.com/v1"
        self.rate_limit_per_minute = rate_limit_per_minute
        self.min_delay_between_requests = 60.0 / rate_limit_per_minute  # segundos
        self.last_request_time = 0
    
    def _rate_limit_delay(self):
        """Aplica delay para respetar rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay_between_requests:
            sleep_time = self.min_delay_between_requests - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def text_search(self, query: str, limit: int = 120) -> List[Dict]:
        """Busca lugares usando text search (Nueva API)."""
        url = f"{self.base_url}/places:searchText"
        results = []
        page_token = None
        
        while len(results) < limit:
            self._rate_limit_delay()
            
            payload = {
                "textQuery": query,
                "maxResultCount": min(20, limit - len(results))  # Nueva API limita a 20 por request
            }
            if page_token:
                payload["pageToken"] = page_token
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.websiteUri,places.nationalPhoneNumber,places.internationalPhoneNumber"
            }
            
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=10)
                r.raise_for_status()
                data = r.json()
                
                if "places" in data:
                    results.extend(data["places"])
                    page_token = data.get("nextPageToken")
                    
                    if not page_token:
                        break
                    
                    # Delay adicional entre páginas
                    time.sleep(1.0)
                else:
                    print(f"[warn] No places found in response")
                    break
                    
            except requests.RequestException as e:
                print(f"[error] Error en Places API: {e}")
                break
        
        return results[:limit]
    
    def place_details(self, place_id: str) -> Dict:
        """Obtiene detalles de un lugar específico (Nueva API)."""
        self._rate_limit_delay()
        
        url = f"{self.base_url}/places/{place_id}"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,internationalPhoneNumber,nationalPhoneNumber,websiteUri,businessStatus"
        }
        
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            # Normalizar respuesta para compatibilidad con código existente
            return {
                "place_id": data.get("id"),
                "name": data.get("displayName", {}).get("text"),
                "formatted_phone_number": data.get("nationalPhoneNumber") or data.get("internationalPhoneNumber"),
                "international_phone_number": data.get("internationalPhoneNumber"),
                "website": data.get("websiteUri"),
                "formatted_address": data.get("formattedAddress"),
                "business_status": data.get("businessStatus"),
                "url": f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            }
        except requests.RequestException as e:
            print(f"[error] Error obteniendo detalles: {e}")
            return {}
    
    def build_query(self, city: str, business_type: str) -> str:
        """Construye una query para buscar negocios."""
        return f"{business_type} in {city}"