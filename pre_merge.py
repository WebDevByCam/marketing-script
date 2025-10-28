#!/usr/bin/env python3
"""
Script de pre-merge: Verifica duplicados antes del merge final.
Compara datos nuevos con Excel maestro y permite buscar más si hay muchos duplicados.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
import re

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.business_processor import BusinessDataProcessor


def find_latest_output():
    """Encuentra el archivo más reciente en data/output/."""
    output_dir = Path("data/output")
    if not output_dir.exists():
        return None

    excel_files = list(output_dir.glob("*.xlsx")) + list(output_dir.glob("*.xls"))
    if not excel_files:
        return None

    # Ordenar por fecha de modificación, más reciente primero
    excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return str(excel_files[0])


def find_input_excel():
    """Encuentra el archivo Excel en data/input/."""
    input_dir = Path("data/input")
    if not input_dir.exists():
        return None

    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    if not excel_files:
        return None
    return str(excel_files[0])


def normalize_key(val: str) -> str:
    """Normaliza una clave para comparación."""
    if val is None:
        return ""
    s = str(val).lower().strip()
    # remove protocol and www
    s = re.sub(r'^https?://', '', s)
    s = re.sub(r'^www\.', '', s)
    # remove non-alphanumeric
    s = re.sub(r'[^a-z0-9]', '', s)
    return s


def compare_with_existing(new_data: List[Dict], existing_filepath: str) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Compara datos nuevos con Excel existente.
    Retorna: (datos_nuevos, datos_duplicados, info_duplicados)
    """
    if not os.path.exists(existing_filepath):
        return new_data, [], {}

    # Leer Excel existente
    df_exist = pd.read_excel(existing_filepath)
    df_exist.columns = [str(c).strip() for c in df_exist.columns]

    # Crear mapas de claves existentes
    existing_by_name = {}
    existing_by_website = {}

    for idx, row in df_exist.iterrows():
        name = str(row.get('Nombre', '')).strip()
        website = str(row.get('Pagina Web', '')).strip()

        if name:
            existing_by_name[normalize_key(name)] = idx
        if website and website != 'N/A':
            existing_by_website[normalize_key(website)] = idx

    # Clasificar datos nuevos
    nuevos = []
    duplicados = []
    info_duplicados = {}

    for item in new_data:
        nombre = item.get('Nombre', '').strip()
        website = item.get('Página Web', '').strip()

        # Verificar duplicados
        name_key = normalize_key(nombre)
        website_key = normalize_key(website) if website and website != 'N/A' else ''

        duplicated_by_name = name_key in existing_by_name
        duplicated_by_website = website_key and website_key in existing_by_website

        if duplicated_by_name or duplicated_by_website:
            duplicados.append(item)
            reason = []
            if duplicated_by_name:
                reason.append(f"Nombre: {nombre}")
            if duplicated_by_website:
                reason.append(f"Web: {website}")

            info_duplicados[nombre] = {
                'reason': ' | '.join(reason),
                'website': website,
                'telefono': item.get('Teléfono', ''),
                'whatsapp': item.get('WhatsApp', '')
            }
        else:
            nuevos.append(item)

    return nuevos, duplicados, info_duplicados


def clean_value(val):
    """Limpia valores: convierte NaN/None a 'N/A', strings vacías a 'N/A'."""
    if val is None or (isinstance(val, float) and str(val).lower() == 'nan'):
        return 'N/A'
    s = str(val).strip()
    return s if s else 'N/A'


def save_filtered_output(original_output_path: str, filtered_data: List[Dict], suffix: str = "_filtrado"):
    """Guarda los datos filtrados en un nuevo archivo."""
    if not filtered_data:
        return None

    # Limpiar valores en los datos
    cleaned_data = []
    for item in filtered_data:
        cleaned_item = {}
        for key, value in item.items():
            cleaned_item[key] = clean_value(value)
        cleaned_data.append(cleaned_item)

    # Crear nombre del archivo filtrado
    path_obj = Path(original_output_path)
    new_filename = f"{path_obj.stem}{suffix}{path_obj.suffix}"
    filtered_path = path_obj.parent / new_filename

    # Crear DataFrame y guardar
    df = pd.DataFrame(cleaned_data)
    df.to_excel(filtered_path, index=False)

    return str(filtered_path)


def main():
    print("=" * 80)
    print("🔍 PRE-MERGE - Verificación de Duplicados")
    print("=" * 80)
    print()

    # Buscar archivos
    output_file = find_latest_output()
    input_file = find_input_excel()

    if not output_file:
        print("❌ ERROR: No se encontró ningún archivo en data/output/")
        print("   Primero ejecuta: python run_interactive.py")
        return 1

    if not input_file:
        print("❌ ERROR: No se encontró Excel maestro en data/input/")
        print("   Coloca tu archivo Excel en data/input/")
        return 1

    print(f"📁 Archivo de salida: {output_file}")
    print(f"📁 Excel maestro: {input_file}")
    print()

    # Leer datos nuevos
    try:
        df_new = pd.read_excel(output_file)
        new_data = df_new.to_dict('records')
        print(f"✅ Leídos {len(new_data)} registros del archivo de salida")
    except Exception as e:
        print(f"❌ Error leyendo archivo de salida: {e}")
        return 1

    # Comparar con existentes
    print()
    print("🔍 Comparando con datos existentes...")
    nuevos, duplicados, info_duplicados = compare_with_existing(new_data, input_file)

    # Mostrar resultados
    print()
    print("=" * 80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("=" * 80)
    print(f"📈 Total de registros analizados: {len(new_data)}")
    print(f"✅ Registros NUEVOS: {len(nuevos)}")
    print(f"🔄 Registros DUPLICADOS: {len(duplicados)}")
    print()

    if duplicados:
        print("📋 DETALLE DE DUPLICADOS:")
        print("-" * 50)
        for nombre, info in info_duplicados.items():
            print(f"• {nombre}")
            print(f"  Motivo: {info['reason']}")
            print(f"  Tel: {info['telefono']} | WA: {info['whatsapp']}")
            print()

    # Preguntar qué hacer
    if len(duplicados) > 0:
        print("🤔 ¿Qué deseas hacer?")
        print(f"   1. Continuar con merge (agregará {len(nuevos)} registros nuevos)")
        print(f"   2. Buscar {len(duplicados)} empresas adicionales para compensar")
        print("   3. Cancelar")
        print()
        while True:
            opcion = input("Elige una opción (1/2/3): ").strip()

            if opcion == "1":
                # Continuar con merge normal
                if nuevos:
                    filtered_path = save_filtered_output(output_file, nuevos, "_sin_duplicados")
                    if filtered_path:
                        print(f"✅ Archivo filtrado guardado: {filtered_path}")
                        print("   (contiene solo los registros nuevos)")
                else:
                    print("⚠️  No hay registros nuevos para agregar")
                break

            elif opcion == "2":
                # Buscar más empresas
                if not nuevos:
                    print("❌ No hay registros válidos para usar como base")
                    return 1

                # Obtener información de búsqueda del archivo original
                ciudad = None
                tipo_negocio = None
                filename = Path(output_file).name

                # Extraer info del nombre del archivo (formato: output_{ciudad}_{tipo}_{timestamp}.xlsx)
                parts = filename.replace('output_', '').replace('.xlsx', '').split('_')
                if len(parts) >= 3:
                    ciudad_parts = []
                    tipo_parts = []

                    # Ciudad hasta encontrar el tipo
                    for part in parts[:-2]:  # Excluir timestamp
                        if part in ['hoteles', 'restaurantes', 'tiendas', 'empresas', 'negocios']:
                            tipo_parts.append(part)
                        else:
                            ciudad_parts.append(part)

                    if ciudad_parts:
                        ciudad = ' '.join(ciudad_parts).replace('_', ' ')
                    if tipo_parts:
                        tipo_negocio = ' '.join(tipo_parts)

                if not ciudad or not tipo_negocio:
                    print("❌ No se pudo determinar la ciudad/tipo de negocio del archivo")
                    ciudad = input("Ciudad: ").strip()
                    tipo_negocio = input("Tipo de negocio: ").strip()

                print()
                print(f"🔍 Buscando {len(duplicados)} empresas adicionales...")
                print(f"   Ciudad: {ciudad}")
                print(f"   Tipo: {tipo_negocio}")
                print()

                # Inicializar procesador
                processor = BusinessDataProcessor(
                    api_key=os.getenv('GOOGLE_API_KEY'),
                    workers=1,
                    humanize=True,
                    rate_limit_per_minute=600
                )

                # Buscar empresas adicionales
                try:
                    additional_results = processor.load_businesses_with_contact_info(
                        city=ciudad,
                        business_type=tipo_negocio,
                        target_count=len(duplicados)
                    )

                    if additional_results:
                        # Procesar los adicionales
                        processed_additional = processor.process_batch(
                            items=additional_results,
                            scan_emails=False,
                            delay=0,
                            ciudad=ciudad
                        )

                        # Combinar con los nuevos
                        combined_data = nuevos + processed_additional

                        # Guardar archivo combinado
                        combined_path = save_filtered_output(output_file, combined_data, "_con_adicionales")
                        if combined_path:
                            print(f"✅ Archivo combinado guardado: {combined_path}")
                            print(f"   Registros nuevos: {len(nuevos)}")
                            print(f"   Registros adicionales: {len(processed_additional)}")
                            print(f"   Total: {len(combined_data)}")
                    else:
                        print("❌ No se encontraron empresas adicionales")

                except Exception as e:
                    print(f"❌ Error buscando empresas adicionales: {e}")

                break

            elif opcion == "3":
                print("❌ Operación cancelada")
                return 0

            else:
                print("❌ Opción inválida. Elige 1, 2 o 3.")
    else:
        print("🎉 ¡No hay duplicados! Todos los registros son nuevos.")
        print("   Puedes proceder directamente al merge.")

    print()
    print("=" * 80)
    print("✅ PRE-MERGE COMPLETADO")
    print("=" * 80)

    if len(nuevos) > 0:
        print("📋 PRÓXIMOS PASOS:")
        print("   1. Revisa el archivo filtrado generado")
        print("   2. Si todo está bien, ejecuta:")
        print("      python merge_final.py")
    else:
        print("📋 No hay registros nuevos para agregar")

    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())