#!/usr/bin/env python3
"""
Post Merge Manager - Gestión automática de archivos después del merge
Mueve el archivo merged a input y elimina archivos antiguos.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

def move_merged_to_input(merged_file_path: str, backup_old_input: bool = True) -> dict:
    """
    Mueve el archivo merged a la carpeta input y opcionalmente respalda el input anterior.

    Args:
        merged_file_path (str): Ruta completa al archivo merged
        backup_old_input (bool): Si True, crea backup del input anterior

    Returns:
        dict: Resultado de la operación
    """
    try:
        merged_path = Path(merged_file_path)
        input_dir = Path("data/input")

        # Verificar que el archivo merged existe
        if not merged_path.exists():
            return {"error": f"El archivo merged no existe: {merged_file_path}"}

        # Verificar que el directorio input existe
        if not input_dir.exists():
            input_dir.mkdir(parents=True, exist_ok=True)

        # Encontrar archivos existentes en input
        existing_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
        old_input_files = []

        if existing_files:
            # Backup de archivos existentes si se solicita
            if backup_old_input:
                backup_dir = input_dir / "backup"
                backup_dir.mkdir(exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_subdir = backup_dir / f"backup_{timestamp}"
                backup_subdir.mkdir(exist_ok=True)

                for old_file in existing_files:
                    backup_path = backup_subdir / old_file.name
                    shutil.move(str(old_file), str(backup_path))
                    old_input_files.append(str(old_file))

                print(f"[✓] Archivos anteriores respaldados en: {backup_subdir}")
            else:
                # Eliminar archivos antiguos sin backup
                for old_file in existing_files:
                    old_file.unlink()
                    old_input_files.append(str(old_file))
                    print(f"[🗑️] Archivo anterior eliminado: {old_file.name}")

        # Mover el archivo merged a input
        new_input_name = f"base_datos_master.xlsx"  # Nombre estándar para el input
        new_input_path = input_dir / new_input_name

        # Copiar en lugar de mover para mantener el original en merged
        shutil.copy2(str(merged_path), str(new_input_path))

        # Verificar que el archivo se copió correctamente
        if new_input_path.exists():
            # Leer y verificar que el archivo es válido
            try:
                df = pd.read_excel(new_input_path)
                record_count = len(df)
                print(f"[✓] Archivo copiado exitosamente: {new_input_path}")
                print(f"[📊] Registros en nuevo input: {record_count}")
            except Exception as e:
                return {"error": f"Error al verificar el archivo copiado: {e}"}
        else:
            return {"error": "Error al copiar el archivo merged"}

        result = {
            "success": True,
            "new_input_file": str(new_input_path),
            "old_input_files": old_input_files,
            "backup_created": backup_old_input and bool(old_input_files),
            "record_count": record_count if 'record_count' in locals() else 0
        }

        print(f"[🎉] Operación completada exitosamente!")
        print(f"[📁] Nuevo archivo input: {new_input_path}")
        if old_input_files:
            print(f"[🗂️] Archivos anteriores: {len(old_input_files)}")

        return result

    except Exception as e:
        error_msg = f"Error en move_merged_to_input: {str(e)}"
        print(f"[❌] {error_msg}")
        return {"error": error_msg}

def cleanup_old_files(days_old: int = 30) -> dict:
    """
    Limpia archivos antiguos de las carpetas output y merged.

    Args:
        days_old (int): Archivos más antiguos que estos días serán eliminados

    Returns:
        dict: Resultado de la limpieza
    """
    try:
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_files = []

        # Limpiar output
        output_dir = Path("data/output")
        if output_dir.exists():
            for file_path in output_dir.glob("*.xlsx"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    cleaned_files.append(str(file_path))

        # Limpiar merged (mantener solo los más recientes)
        merged_dir = Path("data/merged")
        if merged_dir.exists():
            merged_files = list(merged_dir.glob("*.xlsx"))
            if len(merged_files) > 5:  # Mantener máximo 5 archivos merged
                # Ordenar por fecha de modificación (más antiguos primero)
                merged_files.sort(key=lambda x: x.stat().st_mtime)
                files_to_delete = merged_files[:-5]  # Mantener los 5 más recientes

                for file_path in files_to_delete:
                    file_path.unlink()
                    cleaned_files.append(str(file_path))

        return {
            "success": True,
            "files_cleaned": cleaned_files,
            "files_count": len(cleaned_files)
        }

    except Exception as e:
        return {"error": f"Error en cleanup_old_files: {str(e)}"}

def main():
    """Función principal para testing."""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python post_merge_manager.py <ruta_archivo_merged>")
        print("Ejemplo: python post_merge_manager.py data/merged/merged_file.xlsx")
        return

    merged_file = sys.argv[1]

    print("🔄 Iniciando gestión post-merge...")
    print(f"📁 Archivo merged: {merged_file}")

    # Mover merged a input
    result = move_merged_to_input(merged_file, backup_old_input=True)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    print("✅ Operación completada exitosamente!")

    # Limpieza opcional de archivos antiguos
    if len(sys.argv) > 2 and sys.argv[2] == "--cleanup":
        print("\n🧹 Iniciando limpieza de archivos antiguos...")
        cleanup_result = cleanup_old_files(days_old=7)  # Una semana
        if "error" not in cleanup_result:
            print(f"🗑️ Archivos limpiados: {cleanup_result['files_count']}")

if __name__ == "__main__":
    main()