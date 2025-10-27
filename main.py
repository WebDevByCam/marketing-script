#!/usr/bin/env python3
"""
Marketing Script - Recolector de datos de negocios
==================================================

Busca negocios usando Google Places API o archivos de entrada, 
extrae información de contacto (emails, teléfonos) y exporta 
resultados a múltiples formatos.

Uso:
    python main.py --city "Medellín" --type "hotel" --outfile resultados.xlsx
    python main.py --input-file empresas.csv --out-txt salida.txt --workers 3
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Añadir src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.business_processor import BusinessDataProcessor
from src.output_writer import OutputWriter


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Recolector de datos de negocios con múltiples fuentes y formatos de salida",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Buscar hoteles en Medellín usando Places API
  python main.py --city "Medellín" --type "hotel" --limit 100 --outfile hoteles.xlsx
  
  # Procesar archivo CSV existente con datos básicos
  python main.py --input-file empresas.csv --out-txt resultados.txt --workers 3
  
  # Modo completo con Google Sheets
  python main.py --city "Bogotá" --type "restaurant" \\
    --gsheet-id "1ABC...XYZ" --worksheet "Restaurantes" \\
    --sa-json credenciales.json

Variables de entorno:
  GOOGLE_API_KEY              - API key para Google Places
  GOOGLE_APPLICATION_CREDENTIALS - Ruta al JSON de Service Account
        """
    )
    
    # Argumentos de entrada
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--city", help="Ciudad para buscar en Places API")
    source_group.add_argument("--input-file", help="Archivo CSV/TXT con datos de entrada")
    
    parser.add_argument("--type", dest="business_type", 
                       help="Tipo de negocio (requerido si usas --city)")
    parser.add_argument("--limit", type=int, default=200, 
                       help="Máximo resultados de Places API (default: 200)")
    
    # Configuración de scraping
    parser.add_argument("--email-scan-pages", type=int, default=5,
                       help="Páginas a revisar por sitio para emails (default: 5)")
    parser.add_argument("--no-email-scan", action="store_true",
                       help="Saltear búsqueda de emails (más rápido)")
    parser.add_argument("--workers", type=int, default=1,
                       help="Número de workers paralelos (default: 1)")
    
    # Salida
    parser.add_argument("--outfile", 
                       help="Archivo de salida (.csv, .xlsx, .txt)")
    parser.add_argument("--out-txt", 
                       help="Archivo de texto simple adicional")
    
    # Google Sheets
    parser.add_argument("--gsheet-id", 
                       help="ID del Google Spreadsheet")
    parser.add_argument("--worksheet", default="Resultados",
                       help="Nombre de la hoja (default: 'Resultados')")
    parser.add_argument("--sa-json", 
                       help="Ruta al JSON de Service Account")
    
    # Interfaz
    parser.add_argument("--humanize", action="store_true",
                       help="Efectos de tipeo humano en la salida")
    parser.add_argument("--humanize-speed", type=float, default=0.02,
                       help="Velocidad de tipeo (segundos por caracter, default: 0.02)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Salida detallada")
    
    args = parser.parse_args()
    
    # Validaciones
    if args.city and not args.business_type:
        parser.error("--type es requerido cuando usas --city")
    
    if args.input_file and not os.path.exists(args.input_file):
        parser.error(f"Archivo de entrada no existe: {args.input_file}")
    
    # Configurar API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if args.city and not api_key:
        parser.error("GOOGLE_API_KEY requerida en .env para usar Places API")
    
    # Inicializar procesador
    try:
        processor = BusinessDataProcessor(
            api_key=api_key,
            workers=args.workers,
            humanize=args.humanize,
            humanize_speed=args.humanize_speed
        )
        
        # Cargar datos
        if args.city:
            items = processor.load_from_places_api(
                args.city, args.business_type, args.limit
            )
        else:
            items = processor.load_from_file(args.input_file)
        
        if not items:
            processor.output_writer.print("[i] No se encontraron datos para procesar")
            return
        
        # Procesar datos
        results = processor.process_batch(
            items, 
            scan_emails=not args.no_email_scan,
            delay=0.3 if args.no_email_scan else 1.0
        )
        
        if not results:
            processor.output_writer.print("[i] No se generaron resultados")
            return
        
        processor.output_writer.print(f"[i] Procesados {len(results)} elementos")
        
        # Escribir salidas
        output_writer = processor.output_writer
        
        # Google Sheets
        if args.gsheet_id:
            output_writer.write_to_gsheets(
                results, args.gsheet_id, args.worksheet, args.sa_json
            )
        
        # Archivo principal
        if args.outfile:
            output_writer.auto_write(results, args.outfile)
        
        # Archivo de texto adicional
        if args.out_txt:
            output_writer.write_to_txt(results, args.out_txt)
        
        # Salida por defecto si no se especifica nada
        if not args.gsheet_id and not args.outfile and not args.out_txt:
            default_file = "resultados.csv"
            output_writer.write_to_csv(results, default_file)
            output_writer.print(f"[i] No se especificó salida, guardado en: {default_file}")
        
    except KeyboardInterrupt:
        print("\n[i] Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"[error] Error inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()