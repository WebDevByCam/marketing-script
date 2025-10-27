"""
Scraper de emails de sitios web.
"""
import time
import re
from typing import List, Set, Dict
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import normalize_url, same_registrable_domain, EMAIL_REGEX
from .places_api import _get


def harvest_emails_from_html(html: str) -> Set[str]:
    """Extrae emails del HTML usando regex."""
    emails = set(re.findall(EMAIL_REGEX, html or ""))
    bad_suffixes = {"example.com", "localhost", "test.com", "demo.com"}
    return {e for e in emails if e.split("@")[-1].lower() not in bad_suffixes}


def get_candidate_paths() -> List[str]:
    """Devuelve lista de rutas típicas donde buscar información de contacto."""
    paths = [
        "/", "/contact", "/contacto", "/contact-us", "/contactenos", "/contactenos/",
        "/contactar", "/contactar/", "/about", "/nosotros", "/quienes-somos", "/acerca",
        "/ubicacion", "/location", "/reservas", "/reserva", "/bookings", "/booking",
        "/politica-de-datos", "/politica-de-privacidad", "/privacy-policy"
    ]
    preferred = ["/contact", "/contacto", "/contact-us", "/contactenos", "/contactar"]
    seen = set()
    ordered = []
    
    for p in preferred + paths:
        if p not in seen:
            ordered.append(p)
            seen.add(p)
        if len(ordered) >= 20:
            break
    
    return ordered


class EmailScraper:
    """Scraper para encontrar emails en sitios web."""
    
    def __init__(self, max_pages: int = 5, delay: float = 0.75):
        self.max_pages = max_pages
        self.delay = delay
    
    def find_emails_on_site(self, base_url: str) -> List[str]:
        """Busca emails en un sitio web."""
        base_url = normalize_url(base_url)
        if not base_url:
            return []
        
        emails = set()
        tried = 0
        
        # Buscar en rutas candidatas
        for path in get_candidate_paths():
            if tried >= self.max_pages:
                break
            
            url = urljoin(base_url, path)
            try:
                r = _get(url)
                emails |= harvest_emails_from_html(r.text)
                tried += 1
            except requests.RequestException:
                continue
            
            time.sleep(self.delay)
        
        # Buscar mailto: en el home como refuerzo
        try:
            r = _get(base_url)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select('a[href^="mailto:"]'):
                href = a.get("href", "")
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email and re.match(EMAIL_REGEX, email):
                    emails.add(email)
        except requests.RequestException:
            pass
        
        # Filtrar emails del mismo dominio (evita ruido de embeds)
        filtered = set()
        for email in emails:
            try:
                host = email.split("@")[-1]
                if same_registrable_domain(base_url, "https://" + host):
                    filtered.add(email)
            except Exception:
                continue
        
        return sorted(filtered) if filtered else sorted(emails)
    
    def find_emails_parallel(self, urls: List[str], workers: int = 3) -> Dict[str, List[str]]:
        """Busca emails en múltiples sitios en paralelo."""
        results = {}
        
        if workers <= 1:
            # Secuencial
            for url in urls:
                results[url] = self.find_emails_on_site(url)
        else:
            # Paralelo
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_url = {
                    executor.submit(self.find_emails_on_site, url): url 
                    for url in urls if url
                }
                
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        results[url] = future.result()
                    except Exception as e:
                        print(f"[warn] Error buscando emails en {url}: {e}")
                        results[url] = []
        
        return results