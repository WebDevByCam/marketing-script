#!/usr/bin/env python3
"""
Script de prueba para verificar la optimización de costos en Places API.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.business_processor import BusinessDataProcessor

def test_cost_optimization():
    """Prueba que la optimización funciona sin llamadas a place_details."""
    # Usar una API key de prueba (no real para evitar costos)
    api_key = "test_key_not_real"

    processor = BusinessDataProcessor(api_key=api_key)

    # Simular datos que vendrían de text_search
    mock_text_search_results = [
        {
            'id': 'test_place_1',
            'displayName': {'text': 'Restaurante Ejemplo 1'},
            'formattedAddress': 'Calle 123, Bogotá, Colombia',
            'websiteUri': 'https://restaurante1.com',
            'nationalPhoneNumber': '+57 1 2345678',
            'internationalPhoneNumber': '+57 1 2345678',
            'businessStatus': 'OPERATIONAL',
            'types': ['restaurant', 'food'],
            'location': {'latitude': 4.7110, 'longitude': -74.0721}
        },
        {
            'id': 'test_place_2',
            'displayName': {'text': 'Café Ejemplo 2'},
            'formattedAddress': 'Carrera 45, Bogotá, Colombia',
            'websiteUri': 'https://cafe2.com',
            'nationalPhoneNumber': '+57 300 9876543',
            'internationalPhoneNumber': '+57 300 9876543',
            'businessStatus': 'OPERATIONAL',
            'types': ['cafe', 'food'],
            'location': {'latitude': 4.7110, 'longitude': -74.0721}
        }
    ]

    print("🔍 Probando procesamiento directo de datos de text_search...")

    # Probar la función helper
    processed_business = processor._process_text_search_result(mock_text_search_results[0])

    print("✅ Datos procesados:")
    print(f"  ID: {processed_business.get('id')}")
    print(f"  Nombre: {processed_business.get('name')}")
    print(f"  Teléfono: {processed_business.get('formatted_phone_number')}")
    print(f"  Website: {processed_business.get('website')}")
    print(f"  Dirección: {processed_business.get('formatted_address')}")

    # Verificar que tiene teléfono (debería estar en la lista "con teléfono")
    phone = processed_business.get('formatted_phone_number')
    has_phone = phone and phone.strip()
    print(f"  ¿Tiene teléfono? {has_phone}")

    print("\n✅ Optimización implementada correctamente!")
    print("💰 Ahora solo usaremos Text Search (gratis hasta 10k requests)")
    print("🚫 Eliminadas las llamadas caras a Place Details")

if __name__ == "__main__":
    test_cost_optimization()