#!/usr/bin/env python3
"""Test de las mejoras en el email scraper."""
import sys
import os

sys.path.insert(0, 'src')
from src.email_scraper import EmailScraper

def test_email_scraper():
    """Prueba el scraper mejorado."""
    scraper = EmailScraper(max_pages=3, delay=1.0)

    # Sitios de prueba (sitios que probablemente tengan emails visibles)
    test_sites = [
        "https://www.python.org/",  # Debería tener emails
        "https://www.github.com/",  # Probablemente no permita scraping
        "https://www.google.com/",  # Robots.txt restrictivo
    ]

    print("🧪 TEST: Mejoras en Email Scraper")
    print("=" * 50)

    for site in test_sites:
        print(f"\n🔍 Probando: {site}")
        try:
            emails = scraper.find_emails_on_site(site)
            if emails:
                print(f"   ✅ Encontrados: {emails}")
            else:
                print("   ⚠️  No se encontraron emails")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 50)
    print("✅ Test completado")

if __name__ == "__main__":
    test_email_scraper()
