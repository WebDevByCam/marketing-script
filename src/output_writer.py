"""
Escritura de resultados en diferentes formatos.
"""
import os
import time
import random
from typing import List, Dict
import pandas as pd

# Opcional: gspread (solo si escribes a Google Sheets)
try:
    import gspread
    from google.oauth2.service_account import Credentials as SACredentials
except ImportError:
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
    
    def write_to_excel(self, data: List[Dict], filepath: str):
        """Escribe datos a Excel."""
        if not data:
            self.print("[warn] No hay datos para escribir")
            return
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine="openpyxl")
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
        """Escribe datos a Google Sheets."""
        if gspread is None or SACredentials is None:
            raise RuntimeError(
                "gspread/google-auth no instalados. "
                "Ejecuta: pip install gspread google-auth"
            )
        
        if not data:
            self.print("[warn] No hay datos para escribir")
            return
        
        # Configurar credenciales
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        
        if sa_json_path and os.path.exists(sa_json_path):
            creds = SACredentials.from_service_account_file(sa_json_path, scopes=scopes)
        else:
            sa_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if sa_env and os.path.exists(sa_env):
                creds = SACredentials.from_service_account_file(sa_env, scopes=scopes)
            else:
                raise RuntimeError(
                    "No se encontró el JSON de la Service Account. "
                    "Usa --sa-json o GOOGLE_APPLICATION_CREDENTIALS."
                )
        
        # Escribir a Google Sheets
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(spreadsheet_id)
        
        try:
            ws = sh.worksheet(worksheet_title)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=worksheet_title, rows="1000", cols="20")
        
        # Preparar datos
        df = pd.DataFrame(data)
        ws.clear()
        values = [list(df.columns)] + df.fillna("").values.tolist()
        ws.update(range_name="A1", values=values)
        
        self.print(f"[✓] Google Sheets actualizado -> {spreadsheet_id}")
    
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