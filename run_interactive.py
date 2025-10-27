#!/usr/bin/env python3
"""
Script interactivo para buscar empresas usando Google Places API.
Flujo completo: backup → búsqueda → generación Excel para revisión.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.business_processor import BusinessDataProcessor
from src.output_writer import OutputWriter


def find_input_excel():
    """Busca el archivo Excel en data/input/."""
    input_dir = Path("data/input")
    if not input_dir.exists():
        return None
    
    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    if excel_files:
        return str(excel_files[0])  # Retorna el primero encontrado
    return None


def validate_positive_int(prompt: str) -> int:
    """Solicita un número entero positivo."""
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("❌ El número debe ser mayor que 0. Intenta de nuevo.")
        except ValueError:
            print("❌ Por favor ingresa un número válido.")


def validate_non_empty(prompt: str) -> str:
    """Solicita un texto no vacío."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("❌ Este campo no puede estar vacío. Intenta de nuevo.")


def main():
    print("=" * 70)
    print("🚀 BÚSQUEDA INTERACTIVA DE EMPRESAS")
    print("=" * 70)
    print()
    
    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ ERROR: No se encontró GOOGLE_API_KEY en el archivo .env")
        print("   Por favor crea un archivo .env con tu clave de API de Google.")
        return 1
    
    # Verificar si existe Excel en data/input
    input_excel = find_input_excel()
    if input_excel:
        print(f"✅ Archivo Excel encontrado: {input_excel}")
        print()
    else:
        print("⚠️  No se encontró archivo Excel en data/input/")
        print("   Si quieres hacer merge después, coloca tu Excel allí primero.")
        print()
    
    # Preguntas interactivas
    print("📋 Por favor responde las siguientes preguntas:")
    print()
    
    cantidad = validate_positive_int("1️⃣  ¿Cuántas empresas quieres buscar? (número): ")
    print()
    
    ciudad = validate_non_empty("2️⃣  ¿De qué ciudad y país? (ej: Bogotá, Colombia): ")
    print()
    
    tipo_negocio = validate_non_empty("3️⃣  ¿De qué sector o tipo de mercado? (ej: restaurantes, hoteles): ")
    print()
    
    # Confirmación
    print("-" * 70)
    print("📝 RESUMEN DE LA BÚSQUEDA:")
    print(f"   • Cantidad: {cantidad} empresas")
    print(f"   • Ubicación: {ciudad}")
    print(f"   • Tipo: {tipo_negocio}")
    print("-" * 70)
    print()
    
    confirmar = input("¿Continuar con la búsqueda? (s/n): ").lower().strip()
    if confirmar not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Búsqueda cancelada.")
        return 0
    
    print()
    print("🔍 Iniciando búsqueda...")
    print()
    
    # Crear backup del Excel de input si existe
    if input_excel:
        try:
            output_writer = OutputWriter(humanize=False)
            backup_path = output_writer.create_backup(input_excel)
            print(f"✅ Backup creado: {backup_path}")
            print()
        except Exception as e:
            print(f"⚠️  No se pudo crear backup: {e}")
            print()
    
    # Inicializar procesador con rate limiting de 600 req/min
    processor = BusinessDataProcessor(
        api_key=api_key,
        workers=1,  # Secuencial para mejor control de rate limiting
        humanize=True,
        rate_limit_per_minute=600
    )
    
    try:
        # Buscar en Places API
        results = processor.load_from_places_api(
            city=ciudad,
            business_type=tipo_negocio,
            limit=cantidad
        )
        
        if not results:
            print("❌ No se encontraron resultados.")
            return 1
        
        print(f"✅ Se encontraron {len(results)} resultados")
        print()
        
        # Procesar resultados (obtener detalles, escanear emails opcional)
        print("🔄 Procesando resultados...")
        scan_emails = input("¿Escanear páginas web en busca de emails? (s/n): ").lower().strip()
        scan_emails = scan_emails in ['s', 'si', 'sí', 'y', 'yes']
        print()
        
        processed_data = processor.process_batch(
            items=results,
            scan_emails=scan_emails,
            delay=0  # El rate limiting ya está manejado en PlacesAPIClient
        )
        
        # Generar nombre descriptivo para el archivo de salida
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ciudad_clean = ciudad.replace(",", "").replace(" ", "_")
        tipo_clean = tipo_negocio.replace(" ", "_")
        output_filename = f"output_{ciudad_clean}_{tipo_clean}_{timestamp}.xlsx"
        output_path = os.path.join("data", "output", output_filename)
        
        # Asegurar que existe el directorio de output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Escribir Excel con formato template (solo 6 columnas)
        processor.output_writer.write_to_excel(
            data=processed_data,
            filepath=output_path,
            use_template_columns=True
        )
        
        print()
        print("=" * 70)
        print("✅ BÚSQUEDA COMPLETADA")
        print("=" * 70)
        print(f"📊 Archivo generado: {output_path}")
        print(f"📈 Total de registros: {len(processed_data)}")
        print()
        print("📋 PRÓXIMOS PASOS:")
        print("   1. Revisa el archivo generado en data/output/")
        print("   2. Verifica que los datos sean correctos")
        if input_excel:
            print("   3. Si todo está bien, ejecuta el merge:")
            print(f"      python merge_final.py")
        else:
            print("   3. Si quieres hacer merge, coloca tu Excel en data/input/")
            print("      y ejecuta: python merge_final.py")
        print("=" * 70)
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print("❌ Búsqueda interrumpida por el usuario.")
        return 1
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
