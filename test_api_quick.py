#!/usr/bin/env python3
"""Test real con API - 3 restaurantes en Bogota."""
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.path.insert(0, 'src')
from src.business_processor import BusinessDataProcessor

# Cargar API key
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    print('ERROR: No se encontro GOOGLE_API_KEY')
    exit(1)

print('Test real con API - 3 restaurantes en Bogota')
print('=' * 60)

# Inicializar procesador con rate limiting
start_time = time.time()
processor = BusinessDataProcessor(
    api_key=api_key,
    workers=1,
    humanize=False,
    rate_limit_per_minute=600
)

# Buscar
results = processor.load_from_places_api(
    city='Bogota, Colombia',
    business_type='restaurantes',
    limit=3
)

search_time = time.time() - start_time
print(f'\nBusqueda completada en {search_time:.2f} segundos')
print(f'Resultados encontrados: {len(results)}')

# Procesar (sin email scan para ser rapidos)
start_process = time.time()
processed = processor.process_batch(results, scan_emails=False, delay=0)
process_time = time.time() - start_process

print(f'Procesamiento completado en {process_time:.2f} segundos')
print(f'Total de registros procesados: {len(processed)}')

# Calcular rate (aproximado)
total_requests = len(results) + len([r for r in results if r.get('place_id')])
total_time = search_time + process_time
rate_per_min = (total_requests / total_time) * 60 if total_time > 0 else 0
print(f'\nRate limiting: ~{rate_per_min:.1f} requests/minuto')
if rate_per_min <= 600:
    print('Rate esta dentro del limite (<=600 req/min)')
else:
    print('Rate excede el limite')

# Generar Excel con template columns
output_path = 'data/output/test_api_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.xlsx'
processor.output_writer.write_to_excel(processed, output_path, use_template_columns=True)
print(f'\nExcel generado: {output_path}')

# Verificar contenido
import pandas as pd
df = pd.read_excel(output_path)
print(f'Columnas: {list(df.columns)}')
print(f'Filas: {len(df)}')

print('\n' + '=' * 60)
print('TEST REAL COMPLETADO')
