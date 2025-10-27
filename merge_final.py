#!/usr/bin/env python3
"""
Script para hacer merge final del Excel generado en data/output/
con el Excel maestro en data/input/.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.output_writer import OutputWriter


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
    if excel_files:
        return str(excel_files[0])
    return None


def main():
    print("=" * 70)
    print("🔄 MERGE FINAL - Fusión de Datos")
    print("=" * 70)
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
        print("   Coloca tu archivo Excel en data/input/ y vuelve a intentar.")
        return 1
    
    print(f"📁 Archivo de salida: {output_file}")
    print(f"📁 Excel maestro: {input_file}")
    print()
    
    # Confirmación
    print("⚠️  ADVERTENCIA: Este proceso modificará tu Excel maestro.")
    print("   (Se creará un backup automático antes de modificar)")
    print()
    confirmar = input("¿Continuar con el merge? (s/n): ").lower().strip()
    
    if confirmar not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Merge cancelado.")
        return 0
    
    print()
    print("🔄 Iniciando merge...")
    print()
    
    try:
        # Inicializar output writer
        writer = OutputWriter(humanize=False)
        
        # Leer datos del archivo de salida
        import pandas as pd
        df_new = pd.read_excel(output_file)
        new_data = df_new.to_dict('records')
        
        print(f"✅ Leídos {len(new_data)} registros del archivo de salida")
        
        # Hacer merge (crea backup automáticamente)
        writer.merge_into_existing_excel(
            existing_filepath=input_file,
            data=new_data,
            key_priority=['Pagina Web', 'Nombre'],
            create_backup=True
        )
        
        print()
        print("=" * 70)
        print("✅ MERGE COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(f"📊 Archivo actualizado: {input_file}")
        print(f"💾 Backup creado en: data/backups/")
        print()
        print("📋 PRÓXIMOS PASOS:")
        print("   • Abre el Excel maestro y verifica los cambios")
        print("   • Si hay algún problema, puedes restaurar desde data/backups/")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print()
        print(f"❌ ERROR durante el merge: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
