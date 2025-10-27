"""
Escritura de resultados en diferentes formatos.
"""
import os
import time
import random
from typing import List, Dict
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill

# Google Sheets integration has been removed from the core writer to keep
# the project lightweight. If you need to re-add Sheets support, reintroduce
# the gspread/google-auth dependency and the corresponding methods.
gspread = None
SACredentials = None


def human_print(text: str, humanize: bool = False, speed: float = 0.02):
    """Print texto simulando tipeo humano. Si humanize=False hace print normal."""
    if not humanize:
        print(text)
        return
    
    # Simular tipeo con posibles typos leves y corrección
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(speed * (0.5 + random.random()))
    print()


class OutputWriter:
    """Maneja la escritura de resultados en diferentes formatos."""
    
    def __init__(self, humanize: bool = False, humanize_speed: float = 0.02):
        self.humanize = humanize
        self.humanize_speed = humanize_speed
    
    def print(self, text: str):
        """Imprime texto con o sin efecto de tipeo."""
        human_print(text, self.humanize, self.humanize_speed)
    
    def write_to_csv(self, data: List[Dict], filepath: str):
        """Escribe datos a CSV."""
        if not data:
            self.print("[warn] No hay datos para escribir")
            return
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        self.print(f"[✓] Archivo CSV guardado -> {filepath}")
    
    def write_to_excel(self, data: List[Dict], filepath: str, use_template_columns: bool = False):
        """Escribe datos a Excel.
        
        Si use_template_columns=True, usa solo las columnas básicas del template
        (Nombre, WhatsApp, Telefono, Correo, Pagina Web, Ciudad) sin campos de debug.
        """
        if not data:
            self.print("[warn] No hay datos para escribir")
            return
        
        # Normalizar y ordenar columnas según el formato solicitado
        df = pd.DataFrame(data)

        if use_template_columns:
            # Usar solo columnas del template (sin debug ni opcionales)
            template_cols = [
                "Nombre",
                "WhatsApp",
                "Telefono",
                "Correo",
                "Pagina Web",
                "Ciudad"
            ]
            
            # Mapear nombres de columnas a formato objetivo
            col_map = {
                "Teléfono": "Telefono",
                "Teléfono (opcional)": "Telefono",
                "Página Web": "Pagina Web",
                "Página web": "Pagina Web",
                "Correo": "Correo",
                "Ciudad": "Ciudad",
                "Nombre": "Nombre",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            
            # Asegurar que las columnas existan
            for c in template_cols:
                if c not in df.columns:
                    df[c] = ""
            
            df_out = df[template_cols]
        else:
            # Mapear nombres de columnas a formato objetivo (sin acentos para compatibilidad)
            col_map = {
                "Teléfono": "Telefono",
                "Teléfono (opcional)": "Telefono",
                "Página Web": "Pagina Web",
                "Página web": "Pagina Web",
                "Correo": "Correo",
                "Ciudad": "Ciudad",
                "Nombre": "Nombre",
            }
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

            # Columnas objetivo y orden
            target_cols = [
                "Nombre",
                "WhatsApp",
                "Telefono",
                "Correo",
                "Pagina Web",
                "Ciudad",
                "Dirección (opcional)",
                "Google Maps URL (opcional)",
                "place_id (debug)",
            ]

            # Asegurar que las columnas existan
            for c in target_cols:
                if c not in df.columns:
                    df[c] = ""

            df_out = df[target_cols]

        # Escribir usando pandas y luego estilizar encabezado con openpyxl
        df_out.to_excel(filepath, index=False, engine="openpyxl")

        try:
            wb = load_workbook(filepath)
            ws = wb.active
            header_fill = PatternFill(start_color="FFF59D", end_color="FFF59D", fill_type="solid")
            header_font = Font(bold=True)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
            wb.save(filepath)
        except Exception:
            # Si falla el formateo, no interrumpir el flujo
            pass

        self.print(f"[✓] Archivo Excel guardado -> {filepath}")
    
    def write_to_txt(self, data: List[Dict], filepath: str, separator: str = " | "):
        """Escribe datos a archivo de texto simple."""
        if not data:
            self.print("[warn] No hay datos para escribir")
            return
        
        with open(filepath, "w", encoding="utf-8") as fh:
            for row in data:
                # línea compacta: campos principales separados
                fields = [
                    "Nombre", "Teléfono", "Correo", "Página Web", 
                    "Ciudad", "Dirección (opcional)"
                ]
                line = separator.join([str(row.get(field, "")) for field in fields])
                fh.write(line + "\n")
        
        self.print(f"[✓] Archivo de texto guardado -> {filepath}")
    
    def write_to_gsheets(self, data: List[Dict], spreadsheet_id: str, 
                        worksheet_title: str, sa_json_path: str = None):
        # Google Sheets support removed from this writer. If you need to
        # export directly to Google Sheets, use a separate script or re-add
        # the dependency and implementation. For now, prefer CSV/XLSX/TXT.
        raise NotImplementedError("Google Sheets writing has been removed. Use CSV/XLSX output.")

    def merge_with_gsheet(self, data: List[Dict], spreadsheet_id: str, worksheet_title: str, sa_json_path: str = None, key_fields: list = None):
        # Removed: merging with Google Sheets is no longer supported in the
        # cleaned project. Implement externally if required.
        raise NotImplementedError("Google Sheets merge has been removed. Use local CSV/XLSX workflows.")

    def create_backup(self, filepath: str) -> str:
        """Crea una copia de seguridad del archivo con timestamp.
        
        Retorna la ruta de la copia creada.
        """
        from datetime import datetime
        import shutil
        
        if not os.path.exists(filepath):
            return ""
        
        # Crear carpeta de backups si no existe
        backup_dir = os.path.join(os.path.dirname(filepath), '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)
        backup_name = f"{name}_backup_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        shutil.copy2(filepath, backup_path)
        self.print(f"[✓] Backup creado -> {backup_path}")
        return backup_path

    def merge_into_existing_excel(self, existing_filepath: str, data: List[Dict], key_priority: list = None, create_backup: bool = True):
        """Fusiona `data` (lista de dicts) dentro de un archivo Excel existente.

        Reglas:
        - No se agregan columnas nuevas. Sólo se actualizan las columnas que ya
          existen en el archivo Excel.
        - Se intenta emparejar filas usando, por defecto, 'Pagina Web' si existe
          y tiene valores, o en su defecto 'Nombre'. Se normaliza la clave para
          evitar variaciones simples (http(s), www, mayúsculas, caracteres).
        - Si no existe coincidencia, se añade una nueva fila al final con las
          columnas existentes (los campos que no estén disponibles se dejan vacíos).

        Parámetros:
        - existing_filepath: ruta al archivo Excel a actualizar (se sobrescribe).
        - data: lista de diccionarios con datos procesados.
        - key_priority: lista de columnas a usar como clave en orden de preferencia.
        - create_backup: si True, crea backup automático antes de sobrescribir.
        """
        import re

        if not data:
            self.print("[warn] No hay datos para fusionar en Excel existente")
            return
        
        # Crear backup si se solicita
        if create_backup:
            self.create_backup(existing_filepath)

        if key_priority is None:
            key_priority = ["Pagina Web", "Nombre"]

        # Leer el Excel existente
        if not os.path.exists(existing_filepath):
            raise FileNotFoundError(f"No existe el archivo Excel: {existing_filepath}")

        df_exist = pd.read_excel(existing_filepath)

        # Normalizar columnas: strip
        df_exist.columns = [str(c).strip() for c in df_exist.columns]

        existing_cols = list(df_exist.columns)

        # Decide la columna clave presente en el archivo existente
        key_col = None
        for k in key_priority:
            if k in df_exist.columns:
                key_col = k
                break
        # If no key column present, fall back to first column named 'Nombre' or index
        if key_col is None:
            if 'Nombre' in df_exist.columns:
                key_col = 'Nombre'
            else:
                key_col = df_exist.columns[0]

        def normalize_key(val: str) -> str:
            if val is None:
                return ""
            s = str(val).lower().strip()
            # remove protocol and www
            s = re.sub(r'^https?://', '', s)
            s = re.sub(r'^www\.', '', s)
            # remove non-alphanumeric
            s = re.sub(r'[^a-z0-9]', '', s)
            return s

        # Build mapping of existing keys -> row index
        existing_keys = df_exist.get(key_col, pd.Series([""] * len(df_exist))).fillna("")
        existing_map = {normalize_key(v): i for i, v in enumerate(existing_keys)}

        # Helper to determine if a phone looks like mobile (quick heuristic)
        def looks_like_mobile(phone: str) -> bool:
            if not phone:
                return False
            digits = re.sub(r'\D', '', str(phone))
            if digits.startswith('57'):
                digits = digits[2:]
            # In Colombia mobiles start with '3' (e.g., 300,311,312,320...)
            return digits.startswith('3')

        # Iterate new data and merge
        for item in data:
            # build item key using same priority
            item_key_val = ""
            for k in key_priority:
                if k in item and item[k]:
                    item_key_val = item[k]
                    break
            if not item_key_val:
                # fallback to Nombre
                item_key_val = item.get('Nombre', '')

            nkey = normalize_key(item_key_val)

            if nkey in existing_map:
                idx = existing_map[nkey]
                # Update only columns that exist in df_exist and in item
                for col in existing_cols:
                    if col in item and col not in [None, 'Unnamed: 0']:
                        # Special handling: distribute phone between WhatsApp/Telefono
                        if col == 'WhatsApp':
                            # prefer explicit 'WhatsApp' in item, else try to detect
                            val = item.get('WhatsApp') or item.get('Telefono') or item.get('Teléfono')
                            if val and not looks_like_mobile(val):
                                # if detected as non-mobile, skip writing to WhatsApp
                                continue
                            df_exist.at[idx, col] = val
                        elif col == 'Telefono':
                            val = item.get('Telefono') or item.get('Teléfono') or item.get('phone')
                            # if this looks like mobile, prefer WhatsApp instead
                            if val and looks_like_mobile(val):
                                # if Telefono column exists but we have a mobile, leave Telefono empty
                                # unless Telefono is empty and WhatsApp column doesn't exist
                                if 'WhatsApp' not in df_exist.columns:
                                    df_exist.at[idx, col] = val
                                else:
                                    # skip writing mobile into Telefono
                                    pass
                            else:
                                df_exist.at[idx, col] = val
                        else:
                            df_exist.at[idx, col] = item.get(col, df_exist.at[idx, col])
            else:
                # Row not found: append a new row but only with existing columns
                new_row = {c: '' for c in existing_cols}
                for c in existing_cols:
                    if c in item:
                        # map phone heuristics as above
                        if c == 'WhatsApp':
                            val = item.get('WhatsApp') or item.get('Telefono') or item.get('Teléfono')
                            if val and not looks_like_mobile(val):
                                # don't insert non-mobile into WhatsApp
                                continue
                            new_row[c] = val
                        elif c == 'Telefono':
                            val = item.get('Telefono') or item.get('Teléfono') or item.get('phone')
                            if val and looks_like_mobile(val):
                                if 'WhatsApp' not in existing_cols:
                                    new_row[c] = val
                                else:
                                    # skip mobile into Telefono when WhatsApp exists
                                    pass
                            else:
                                new_row[c] = val
                        else:
                            new_row[c] = item.get(c, '')
                df_exist = pd.concat([df_exist, pd.DataFrame([new_row])], ignore_index=True)

        # Guardar de vuelta sin cambiar las columnas existentes
        # Mantener estilo simple: escribir por pandas (sobrescribe contenido)
        df_exist.to_excel(existing_filepath, index=False, engine='openpyxl')
        self.print(f"[✓] Archivo Excel actualizado -> {existing_filepath}")
    
    def auto_write(self, data: List[Dict], filepath: str):
        """Escribe automáticamente según la extensión del archivo."""
        if not filepath:
            return
        
        ext = filepath.lower().split('.')[-1]
        
        if ext == 'csv':
            self.write_to_csv(data, filepath)
        elif ext in ['xlsx', 'xls']:
            self.write_to_excel(data, filepath)
        elif ext == 'txt':
            self.write_to_txt(data, filepath)
        else:
            self.print(f"[warn] Formato no reconocido: {ext}, guardando como CSV")
            self.write_to_csv(data, filepath + '.csv')