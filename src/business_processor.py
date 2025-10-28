"""
Procesador principal de datos de negocios.
"""
import os
import time
import csv
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .places_api import PlacesAPIClient
from .email_scraper import EmailScraper
from .output_writer import OutputWriter
from .utils import safe_get, clean_phone


class BusinessDataProcessor:
    """Procesador principal para recolectar y procesar datos de negocios."""
    
    def __init__(self, api_key: str = None, workers: int = 1, 
                 humanize: bool = False, humanize_speed: float = 0.02,
                 rate_limit_per_minute: int = 600):
        self.api_key = api_key
        self.workers = workers
        self.places_client = PlacesAPIClient(api_key, rate_limit_per_minute=rate_limit_per_minute) if api_key else None
        self.email_scraper = EmailScraper()
        self.output_writer = OutputWriter(humanize, humanize_speed)
    
    def load_from_places_api(self, city: str, business_type: str, limit: int = 200) -> List[Dict]:
        """Carga datos desde Google Places API."""
        if not self.places_client:
            raise ValueError("API key requerida para usar Places API")
        
        query = self.places_client.build_query(city, business_type)
        self.output_writer.print(f"[i] Buscando: {query} (limit={limit})")
        
        results = self.places_client.text_search(query, limit)
        self.output_writer.print(f"[i] Resultados de Places: {len(results)}")
        
        return results
    
    def load_from_file(self, filepath: str) -> List[Dict]:
        """Carga datos desde archivo (TXT o CSV)."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No existe el archivo: {filepath}")
        
        results = []
        
        if filepath.lower().endswith('.csv'):
            # Leer CSV
            with open(filepath, "r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    results.append({
                        "place_id": None,
                        "name": row.get("nombre", row.get("name", "")),
                        "website": row.get("website", row.get("pagina_web", "")),
                        "formatted_address": row.get("direccion", row.get("address", "")),
                        "formatted_phone_number": row.get("telefono", row.get("phone", "")),
                        "email": row.get("email", row.get("correo", "")),
                        "city": row.get("ciudad", row.get("city", "")),
                        "url": row.get("website", row.get("pagina_web", ""))
                    })
        else:
            # Leer TXT línea por línea
            with open(filepath, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Formato: 'Nombre - https://example.com' o solo 'https://example.com'
                    if "http" in line or "." in line:
                        parts = line.split("-", 1)
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            website = parts[1].strip()
                        else:
                            name = ""
                            website = line.strip()
                        
                        results.append({
                            "place_id": None,
                            "name": name,
                            "website": website,
                            "formatted_address": "",
                            "url": website
                        })
                    else:
                        # Solo nombre sin website
                        results.append({
                            "place_id": None,
                            "name": line,
                            "website": "",
                            "formatted_address": "",
                            "url": ""
                        })
        
        self.output_writer.print(f"[i] Cargados {len(results)} elementos desde {filepath}")
        return results
    
    def process_item(self, item: Dict, scan_emails: bool = True, city: str = "") -> Dict:
        """Procesa un item individual (lugar o entrada de archivo)."""
        # Obtener detalles si es de Places API
        place_id = item.get("place_id") or item.get("id")
        data = item
        
        if place_id and self.places_client:
            try:
                details = self.places_client.place_details(place_id)
                if details:
                    data = details
            except Exception as e:
                self.output_writer.print(f"[warn] Error obteniendo detalles para {place_id}: {e}")
        
        # Extraer información básica
        name = safe_get(data, "name") or safe_get(data, "displayName", {}).get("text") or safe_get(item, "name", default="")
        phone = (safe_get(data, "formatted_phone_number") or 
                safe_get(data, "nationalPhoneNumber") or 
                safe_get(data, "internationalPhoneNumber") or 
                safe_get(item, "formatted_phone_number", default=""))
        website = safe_get(data, "website") or safe_get(data, "websiteUri") or safe_get(item, "website") or safe_get(item, "url", default="")
        address = safe_get(data, "formatted_address") or safe_get(data, "formattedAddress") or safe_get(item, "formatted_address", default="")
        existing_email = safe_get(item, "email", default="")
        
        # Buscar emails si se solicita y hay website
        email_list = []
        if existing_email:
            email_list = [existing_email]
        elif scan_emails and website:
            try:
                email_list = self.email_scraper.find_emails_on_site(website)
            except Exception as e:
                self.output_writer.print(f"[warn] Error buscando emails en {website}: {e}")
        
        return {
            "Nombre": name.strip(),
            "Teléfono": clean_phone(phone).strip() if phone else "N/A",
            "Correo": ", ".join(email_list) if email_list else "N/A",
            "Página Web": website.strip() if website else "N/A",
            "Ciudad": city or safe_get(item, "city", default=""),
            "Dirección (opcional)": address.strip(),
            "Google Maps URL (opcional)": safe_get(data, "url", default=""),
            "place_id (debug)": place_id or ""
        }
    
    def process_batch(self, items: List[Dict], scan_emails: bool = True, 
                     delay: float = 1.0, city: str = "") -> List[Dict]:
        """Procesa un lote de items."""
        results = []
        
        if self.workers > 1 and len(items) > 1:
            # Procesamiento paralelo
            self.output_writer.print(f"[i] Ejecutando con {self.workers} workers...")
            
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {
                    executor.submit(self.process_item, item, scan_emails, city): item 
                    for item in items
                }
                
                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.output_writer.print(f"[warn] Error en worker: {e}")
                        continue
                    
                    if i % 20 == 0:
                        self.output_writer.print(f"[i] Procesados {i}/{len(items)} ...")
        else:
            # Procesamiento secuencial
            for i, item in enumerate(items, 1):
                try:
                    result = self.process_item(item, scan_emails, city)
                    results.append(result)
                except Exception as e:
                    self.output_writer.print(f"[warn] Error procesando item {i}: {e}")
                    continue
                
                if not scan_emails:
                    time.sleep(0.3)
                else:
                    time.sleep(delay)
                
                if i % 20 == 0:
                    self.output_writer.print(f"[i] Procesados {i}/{len(items)} ...")
        
        return results

    def load_businesses_with_contact_info(self, city: str, business_type: str, target_count: int, search_variation: str = "") -> List[Dict]:
        """
        Load businesses from Google Places API that have contact information.
        
        Args:
            city (str): City and country for the search
            business_type (str): Type of business to search for
            target_count (int): Target number of businesses to return
            search_variation (str): Additional search terms to add variety
            
        Returns:
            list: List of businesses with basic contact information (filtered from API results)
        """
        # Add search variation to avoid duplicate results
        if search_variation:
            # Add variation terms to the business type
            varied_business_type = f"{business_type} {search_variation}"
        else:
            varied_business_type = business_type
            
        # Load businesses from Places API - get enough to reach target
        businesses = self.load_from_places_api(city, varied_business_type, target_count * 3)  # Get more to ensure we reach target
        
        if not businesses:
            return []
        
        # First priority: businesses with verified phone numbers
        businesses_with_phone = []
        businesses_without_phone = []
        
        for business in businesses:
            place_id = business.get('id')  # Nueva API usa 'id' en lugar de 'place_id'
            if place_id:
                try:
                    # Get detailed information for this business
                    details = self.places_client.place_details(place_id)
                    if details:
                        # Check if it has phone number
                        phone = details.get('formatted_phone_number') or details.get('international_phone_number')
                        if phone:
                            # Merge basic info with detailed info
                            merged_business = {**business, **details}
                            businesses_with_phone.append(merged_business)
                        else:
                            # Still include businesses without phone, but mark them
                            merged_business = {**business, **details}
                            businesses_without_phone.append(merged_business)
                except Exception as e:
                    self.output_writer.print(f"[warn] Error getting details for {place_id}: {e}")
                    continue
        
        # Combine results: first those with phone, then those without
        final_results = businesses_with_phone + businesses_without_phone
        
        result_count = min(len(final_results), target_count)
        selected_results = final_results[:result_count]
        
        self.output_writer.print(f"[i] Found {len(businesses_with_phone)} businesses with phone and {len(businesses_without_phone)} without phone. Returning {len(selected_results)} total")
        return selected_results