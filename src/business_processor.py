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
        
        # Usar los campos separados de WhatsApp y Teléfono si existen
        whatsapp = safe_get(data, "whatsapp") or safe_get(item, "whatsapp", default="")
        telefono = safe_get(data, "telefono") or safe_get(item, "telefono", default="")
        
        # Si no tenemos separados, usar el teléfono general y determinar
        if not whatsapp and not telefono:
            phone = (safe_get(data, "formatted_phone_number") or 
                    safe_get(data, "nationalPhoneNumber") or 
                    safe_get(data, "internationalPhoneNumber") or 
                    safe_get(item, "formatted_phone_number", default=""))
            
            if phone:
                # Limpiar el número para análisis
                clean_number = ''.join(filter(str.isdigit, phone))
                
                # En Colombia: números que empiezan con 573 o 3 son móviles (probablemente WhatsApp)
                if clean_number.startswith('573') or (len(clean_number) == 10 and clean_number.startswith('3')):
                    whatsapp = phone
                else:
                    telefono = phone
        
        website = safe_get(data, "website") or safe_get(data, "websiteUri") or safe_get(item, "website") or safe_get(item, "url", default="")
        address = safe_get(data, "formatted_address") or safe_get(data, "formattedAddress") or safe_get(item, "formatted_address", default="")
        existing_email = safe_get(item, "email", default="")
        
        # Filtrar URLs que no son páginas web reales (WhatsApp, redes sociales, Google Maps)
        if website:
            website_lower = website.lower()
            # URLs a excluir
            excluded_domains = [
                'wa.me', 'wa.link', 'whatsapp.com', 'web.whatsapp.com',
                'instagram.com', 'facebook.com', 'twitter.com', 'tiktok.com',
                'linkedin.com', 'youtube.com', 'maps.google.com', 'goo.gl',
                'bit.ly', 'tinyurl.com', 't.co'
            ]
            
            # Verificar si la URL contiene alguno de los dominios excluidos
            is_excluded = any(domain in website_lower for domain in excluded_domains)
            
            if is_excluded:
                website = ""  # Marcar como vacío para que se convierta en "N/A"
        
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
            "WhatsApp": clean_phone(whatsapp).strip() if whatsapp else "N/A",
            "Telefono": clean_phone(telefono).strip() if telefono else "N/A",
            "Correo": ", ".join(email_list) if email_list else "N/A",
            "Página Web": website.strip() if website else "N/A",
            "Ciudad": city or safe_get(item, "city", default="N/A"),
            "Dirección (opcional)": address.strip() if address else "N/A",
            "Google Maps URL (opcional)": safe_get(data, "url", default="N/A") if website else "N/A",
            "place_id (debug)": place_id or "N/A"
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
        all_businesses_with_phone = []
        all_businesses_without_phone = []
        attempts = 0
        max_attempts = 5  # Máximo número de búsquedas diferentes
        
        # Lista de variaciones para intentar si no alcanzamos el target
        variations_to_try = [search_variation]
        if search_variation:
            # Agregar algunas variaciones adicionales si tenemos una variación base
            variations_to_try.extend([
                f"{search_variation} zona",
                f"{search_variation} area", 
                f"{search_variation} sector",
                f"{search_variation} barrio"
            ])
        
        for current_variation in variations_to_try:
            if len(all_businesses_with_phone) >= target_count:
                break
                
            attempts += 1
            if attempts > max_attempts:
                break
            
            # Add search variation to avoid duplicate results
            if current_variation:
                # Add variation terms to the business type
                varied_business_type = f"{business_type} {current_variation}"
            else:
                varied_business_type = business_type
                
            # Load businesses from Places API - get enough to reach target
            remaining_needed = target_count - len(all_businesses_with_phone)
            search_limit = max(remaining_needed * 3, 60)  # Buscar al menos 60 resultados por intento
            
            businesses = self.load_from_places_api(city, varied_business_type, search_limit)
            
            if not businesses:
                continue
            
            # Process businesses directly from text_search results - NO additional API calls
            businesses_with_phone = []
            businesses_without_phone = []
            
            for business in businesses:
                # Process data directly from text_search result
                processed_business = self._process_text_search_result(business)
                
                # Check if it has phone number
                phone = processed_business.get('formatted_phone_number')
                if phone and phone.strip():
                    businesses_with_phone.append(processed_business)
                else:
                    businesses_without_phone.append(processed_business)
            
            # Agregar a las listas globales, evitando duplicados por place_id
            existing_place_ids = {b.get('id') or b.get('place_id') for b in all_businesses_with_phone}
            
            for business in businesses_with_phone:
                place_id = business.get('id') or business.get('place_id')
                if place_id and place_id not in existing_place_ids:
                    all_businesses_with_phone.append(business)
                    existing_place_ids.add(place_id)
            
            for business in businesses_without_phone:
                place_id = business.get('id') or business.get('place_id')
                if place_id and place_id not in existing_place_ids:
                    all_businesses_without_phone.append(business)
                    existing_place_ids.add(place_id)
            
            self.output_writer.print(f"[i] Attempt {attempts}: Found {len(businesses_with_phone)} new businesses with phone. Total: {len(all_businesses_with_phone)}")
        
        # Combine results: ONLY those with phone numbers
        final_results = all_businesses_with_phone
        
        result_count = min(len(final_results), target_count)
        selected_results = final_results[:result_count]
        
        self.output_writer.print(f"[i] Found {len(all_businesses_with_phone)} businesses with phone and {len(all_businesses_without_phone)} without phone. Returning {len(selected_results)} total after {attempts} attempts")
        return selected_results
        """Procesa un resultado de text_search al formato interno esperado."""
        # Extraer datos directamente del resultado de text_search
        place_id = business.get('id')
        display_name = business.get('displayName', {})
        name = display_name.get('text') if isinstance(display_name, dict) else str(display_name)
        
        # Teléfonos - usar national primero, luego international
        phone = (business.get('nationalPhoneNumber') or 
                business.get('internationalPhoneNumber'))
        
        website = business.get('websiteUri')
        address = business.get('formattedAddress')
        
        # Crear URL de Google Maps
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""
        
        # Determinar si es WhatsApp o teléfono fijo
        whatsapp = None
        telefono = None
        
        if phone:
            # Limpiar el número para análisis
            clean_number = ''.join(filter(str.isdigit, phone))
            
            # En Colombia: números que empiezan con 3 son móviles (probablemente WhatsApp)
            if clean_number.startswith('573') or (len(clean_number) == 10 and clean_number.startswith('3')):
                whatsapp = phone
            else:
                telefono = phone
        
        return {
            'place_id': place_id,
            'id': place_id,  # Para compatibilidad
            'name': name,
            'displayName': display_name,
            'formatted_phone_number': phone,
            'nationalPhoneNumber': business.get('nationalPhoneNumber'),
            'internationalPhoneNumber': business.get('internationalPhoneNumber'),
            'website': website,
            'websiteUri': website,
            'formatted_address': address,
            'formattedAddress': address,
            'business_status': business.get('businessStatus'),
            'types': business.get('types', []),
            'location': business.get('location'),
            'priceLevel': business.get('priceLevel'),
            'rating': business.get('rating'),
            'userRatingCount': business.get('userRatingCount'),
            'url': maps_url,
            'whatsapp': whatsapp,  # Nuevo campo
            'telefono': telefono  # Nuevo campo
        }
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
        all_businesses_with_phone = []
        all_businesses_without_phone = []
        attempts = 0
        max_attempts = 5  # Máximo número de búsquedas diferentes
        
        # Lista de variaciones para intentar si no alcanzamos el target
        variations_to_try = [search_variation]
        if search_variation:
            # Agregar algunas variaciones adicionales si tenemos una variación base
            variations_to_try.extend([
                f"{search_variation} zona",
                f"{search_variation} area",
                f"{search_variation} sector",
                f"{search_variation} barrio"
            ])
        
        for current_variation in variations_to_try:
            if len(all_businesses_with_phone) >= target_count:
                break
                
            attempts += 1
            if attempts > max_attempts:
                break
            
            # Add search variation to avoid duplicate results
            if current_variation:
                # Add variation terms to the business type
                varied_business_type = f"{business_type} {current_variation}"
            else:
                varied_business_type = business_type
                
            # Load businesses from Places API - get enough to reach target
            remaining_needed = target_count - len(all_businesses_with_phone)
            search_limit = max(remaining_needed * 3, 60)  # Buscar al menos 60 resultados por intento
            
            businesses = self.load_from_places_api(city, varied_business_type, search_limit)
            
            if not businesses:
                continue
            
            # Process businesses directly from text_search results - NO additional API calls
            businesses_with_phone = []
            businesses_without_phone = []
            
            for business in businesses:
                # Process data directly from text_search result
                processed_business = self._process_text_search_result(business)
                
                # Check if it has phone number
                phone = processed_business.get('formatted_phone_number')
                if phone and phone.strip():
                    businesses_with_phone.append(processed_business)
                else:
                    businesses_without_phone.append(processed_business)
            
            # Agregar a las listas globales, evitando duplicados por place_id
            existing_place_ids = {b.get('id') or b.get('place_id') for b in all_businesses_with_phone}
            
            for business in businesses_with_phone:
                place_id = business.get('id') or business.get('place_id')
                if place_id and place_id not in existing_place_ids:
                    all_businesses_with_phone.append(business)
                    existing_place_ids.add(place_id)
            
            for business in businesses_without_phone:
                place_id = business.get('id') or business.get('place_id')
                if place_id and place_id not in existing_place_ids:
                    all_businesses_without_phone.append(business)
                    existing_place_ids.add(place_id)
            
            self.output_writer.print(f"[i] Attempt {attempts}: Found {len(businesses_with_phone)} new businesses with phone. Total: {len(all_businesses_with_phone)}")
        
        # Combine results: ONLY those with phone numbers
        final_results = all_businesses_with_phone
        
        result_count = min(len(final_results), target_count)
        selected_results = final_results[:result_count]
        
        self.output_writer.print(f"[i] Found {len(all_businesses_with_phone)} businesses with phone and {len(all_businesses_without_phone)} without phone. Returning {len(selected_results)} total after {attempts} attempts")
        return selected_results
    def _process_text_search_result(self, business: Dict) -> Dict:
        """Procesa un resultado de text_search al formato interno esperado."""
        # Extraer datos directamente del resultado de text_search
        place_id = business.get("id")
        display_name = business.get("displayName", {})
        name = display_name.get("text") if isinstance(display_name, dict) else str(display_name)
        
        # Teléfonos - usar national primero, luego international
        phone = (business.get("nationalPhoneNumber") or 
                business.get("internationalPhoneNumber"))
        
        website = business.get("websiteUri")
        address = business.get("formattedAddress")
        
        # Crear URL de Google Maps
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""
        
        # Determinar si es WhatsApp o teléfono fijo
        whatsapp = None
        telefono = None
        
        if phone:
            # Limpiar el número para análisis
            clean_number = "".join(filter(str.isdigit, phone))
            
            # En Colombia: números que empiezan con 3 son móviles (probablemente WhatsApp)
            if clean_number.startswith("573") or (len(clean_number) == 10 and clean_number.startswith("3")):
                whatsapp = phone
            else:
                telefono = phone
        
        return {
            "place_id": place_id,
            "id": place_id,  # Para compatibilidad
            "name": name,
            "displayName": display_name,
            "formatted_phone_number": phone,
            "nationalPhoneNumber": business.get("nationalPhoneNumber"),
            "internationalPhoneNumber": business.get("internationalPhoneNumber"),
            "website": website,
            "websiteUri": website,
            "formatted_address": address,
            "formattedAddress": address,
            "business_status": business.get("businessStatus"),
            "types": business.get("types", []),
            "location": business.get("location"),
            "priceLevel": business.get("priceLevel"),
            "rating": business.get("rating"),
            "userRatingCount": business.get("userRatingCount"),
            "url": maps_url,
            "whatsapp": whatsapp,  # Nuevo campo
            "telefono": telefono  # Nuevo campo
        }
        return selected_results
