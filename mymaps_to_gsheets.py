#!/usr/bin/env python3
# MyMaps Business Collector -> Google Sheets
# ------------------------------------------
# Busca negocios usando Google Places API y, si hay sitio web, intenta encontrar correos
# en páginas típicas (contacto, about, etc.). Escribe el resultado directamente en
# Google Sheets (o en CSV/XLSX si lo pides).
#
# REQUISITOS
# pip install: requests beautifulsoup4 python-dotenv pandas openpyxl tenacity tldextract gspread google-auth
#
# AUTENTICACIÓN
# 1) Google Places API:
#    - Habilita "Places API" en Google Cloud y crea una API Key.
#    - Crea un archivo .env junto al script con: GOOGLE_API_KEY=TU_API_KEY
# 2) Google Sheets (Service Account recomendado):
#    - Crea una Service Account en Google Cloud y descarga el JSON de credenciales.
#    - Comparte tu Google Sheet con el correo de la Service Account (Editor).
#    - O define la ruta al JSON con la variable de entorno GOOGLE_APPLICATION_CREDENTIALS,
#      o pásala con --sa-json al ejecutar el script.
#
# USO EJEMPLO
#   python mymaps_to_gsheets.py --city "Medellín" --type "hotel" \
#     --gsheet-id "<SPREADSHEET_ID>" --worksheet "Hoteles Medellín"
#
#   # También puedes guardar archivo local:
#   python mymaps_to_gsheets.py --city "Bogotá" --type "spa" --outfile "spas_bogota.csv"
#
import argparse
import os
import time
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
import pandas as pd
import tldextract
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Opcional: gspread (solo si escribes a Google Sheets)
try:
    import gspread
    from google.oauth2.service_account import Credentials as SACredentials
except Exception:
    gspread = None
    SACredentials = None

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
       retry=retry_if_exception_type(requests.RequestException))
def _get(url, **kwargs):
    resp = requests.get(url, timeout=kwargs.pop("timeout", 12), headers=HEADERS, **kwargs)
    resp.raise_for_status()
    return resp

def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    url = url.split("#")[0]
    return url

def same_registrable_domain(url_a: str, url_b: str) -> bool:
    try:
        da = tldextract.extract(url_a)
        db = tldextract.extract(url_b)
        return (da.domain, da.suffix) == (db.domain, db.suffix) and da.domain != "" and da.suffix != ""
    except Exception:
        return False

def harvest_emails_from_html(html: str) -> set[str]:
    emails = set(re.findall(EMAIL_REGEX, html or ""))
    bad_suffixes = {"example.com", "localhost"}
    return {e for e in emails if e.split("@")[-1].lower() not in bad_suffixes}

def candidate_paths():
    paths = [
        "/", "/contact", "/contacto", "/contact-us", "/contactenos", "/contactenos/",
        "/contactar", "/contactar/", "/about", "/nosotros", "/quienes-somos", "/acerca",
        "/ubicacion", "/location", "/reservas", "/reserva", "/bookings", "/booking",
        "/politica-de-datos", "/politica-de-privacidad", "/privacy-policy"
    ]
    preferred = ["/contact", "/contacto", "/contact-us", "/contactenos", "/contactar"]
    seen = set()
    ordered = []
    for p in preferred + paths:
        if p not in seen:
            ordered.append(p)
            seen.add(p)
        if len(ordered) >= 20:
            break
    return ordered

def find_emails_on_site(base_url: str, max_pages: int = 5) -> list[str]:
    base_url = normalize_url(base_url)
    emails = set()

    tried = 0
    for path in candidate_paths():
        if tried >= max_pages:
            break
        url = urljoin(base_url, path)
        try:
            r = _get(url)
            emails |= harvest_emails_from_html(r.text)
            tried += 1
        except requests.RequestException:
            continue
        time.sleep(0.75)

    # Explorar mailto: del home como refuerzo
    try:
        r = _get(base_url)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select('a[href^="mailto:"]'):
            href = a.get("href", "")
            email = href.replace("mailto:", "").split("?")[0].strip()
            if email and re.match(EMAIL_REGEX, email):
                emails.add(email)
    except requests.RequestException:
        pass

    # Prefiere correos del mismo dominio registrable (evita ruido de embeds)
    filtered = set()
    for e in emails:
        try:
            host = e.split("@")[-1]
            if same_registrable_domain(base_url, "https://" + host):
                filtered.add(e)
        except Exception:
            continue
    if filtered:
        return sorted(filtered)
    return sorted(emails)


def human_print(text: str, humanize: bool = False, speed: float = 0.02):
    """Print texto simulando tipeo humano. Si humanize=False hace print normal."""
    if not humanize:
        print(text)
        return
    # Simular tipeo con posibles typos leves y corrección
    out = []
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(speed * (0.5 + random.random()))
    print()

def places_text_search(api_key: str, query: str, limit: int = 120) -> list[dict]:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    out = []
    pagetoken = None
    while len(out) < limit:
        params = {"query": query, "key": api_key}
        if pagetoken:
            params["pagetoken"] = pagetoken
            time.sleep(2.0)  # Requisito de Google antes de usar next_page_token
        r = _get(url, params=params)
        data = r.json()
        out.extend(data.get("results", []))
        pagetoken = data.get("next_page_token")
        if not pagetoken:
            break
    return out[:limit]

def place_details(api_key: str, place_id: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    fields = [
        "place_id",
        "name",
        "formatted_phone_number",
        "international_phone_number",
        "website",
        "formatted_address",
        "business_status",
        "url"
    ]
    params = {"key": api_key, "place_id": place_id, "fields": ",".join(fields)}
    r = _get(url, params=params)
    return r.json().get("result", {})

def build_query(city: str, biz_type: str) -> str:
    return f"{biz_type} in {city}"

def write_to_gsheets(df: pd.DataFrame, spreadsheet_id: str, worksheet_title: str, sa_json_path: str | None):
    import os
    if gspread is None or SACredentials is None:
        raise RuntimeError("gspread/google-auth no instalados. Ejecuta: pip install gspread google-auth")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if sa_json_path and os.path.exists(sa_json_path):
        creds = SACredentials.from_service_account_file(sa_json_path, scopes=scopes)
    else:
        sa_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_env and os.path.exists(sa_env):
            creds = SACredentials.from_service_account_file(sa_env, scopes=scopes)
        else:
            raise RuntimeError("No se encontró el JSON de la Service Account. Usa --sa-json o GOOGLE_APPLICATION_CREDENTIALS.")
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(worksheet_title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet_title, rows="1000", cols="20")
    ws.clear()
    values = [list(df.columns)] + df.fillna("").values.tolist()
    ws.update(range_name="A1", values=values)

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Colecta datos de negocios y exporta a Google Sheets/CSV/XLSX.")
    parser.add_argument("--city", required=True, help="Ciudad, ej.: 'Medellín'")
    parser.add_argument("--type", dest="biz_type", required=True, help="Tipo: 'hotel', 'spa', 'restaurant', etc.")
    parser.add_argument("--limit", type=int, default=200, help="Máx. resultados (default 200)")
    parser.add_argument("--email-scan-pages", type=int, default=5, help="Páginas a revisar por sitio (default 5)")
    parser.add_argument("--no-email-scan", action="store_true", help="No buscar correos en la web (más rápido)")
    parser.add_argument("--gsheet-id", help="ID del Google Spreadsheet (si se setea, escribe en Sheets)")
    parser.add_argument("--worksheet", default="Resultados", help="Nombre de la pestaña (default 'Resultados')")
    parser.add_argument("--sa-json", help="Ruta al JSON de Service Account (si no usas variable de entorno)")
    parser.add_argument("--outfile", help="Opcional: también guardar en .csv o .xlsx")
    parser.add_argument("--input-file", help="Opcional: archivo de entrada con una URL por línea o 'nombre - sitio' por línea; si se setea, no usa Google Places API")
    parser.add_argument("--input-csv", help="Opcional: archivo CSV con columnas: Nombre,Teléfono,Correo,Página Web,Ciudad (usa estos valores si se proveen)")
    parser.add_argument("--out-txt", help="Opcional: guardar salida como texto simple (cada entrada en una línea) en este archivo")
    parser.add_argument("--workers", type=int, default=1, help="Número de hilos para escanear sitios (default 1 = secuencial)")
    parser.add_argument("--humanize", action="store_true", help="Si se setea, imprime progreso con efecto de tipeo humano")
    parser.add_argument("--humanize-speed", type=float, default=0.02, help="Velocidad base del tipeo humano en segundos por carácter (default 0.02)")
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")

    # Modo alternativo: si el usuario provee --input-file no es obligatorio GOOGLE_API_KEY
    use_places = True
    if args.input_csv:
        if not os.path.exists(args.input_csv):
            raise SystemExit(f"ERROR: No existe el archivo CSV de entrada: {args.input_csv}")
        use_places = False
        # Cargar CSV y transformar en 'results'
        results = []
        df_in = pd.read_csv(args.input_csv, dtype=str).fillna("")
        for _, row in df_in.iterrows():
            website = row.get('Página Web') or row.get('website') or row.get('Web') or ""
            results.append({
                'place_id': None,
                'name': row.get('Nombre') or row.get('name') or "",
                'website': website,
                'formatted_address': "",
                'url': website,
                # conservar teléfono y correo en el dict para usarlos si existen
                'phone_raw': row.get('Teléfono') or row.get('phone') or "",
                'email_raw': row.get('Correo') or row.get('Email') or row.get('email') or "",
                'city_raw': row.get('Ciudad') or row.get('city') or ""
            })
    elif args.input_file:
        if not os.path.exists(args.input_file):
            raise SystemExit(f"ERROR: No existe el archivo de entrada: {args.input_file}")
        use_places = False
    else:
        if not api_key:
            raise SystemExit("ERROR: Define GOOGLE_API_KEY en .env o usa --input-file para ejecutar sin API")

    if use_places:
        query = build_query(args.city, args.biz_type)
        print(f"[i] Buscando: {query} (limit={args.limit})")
        results = places_text_search(api_key, query, limit=args.limit)
        print(f"[i] Resultados de Places: {len(results)}")
    else:
        # Si venimos de --input-csv ya tenemos 'results' cargado.
        if args.input_csv:
            pass
        elif args.input_file:
            # Leer archivo de entrada: cada línea puede ser una URL o 'Nombre - sitio'
            results = []
            with open(args.input_file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    # Soportar formatos: 'Nombre - https://example.com' o solo 'https://example.com'
                    if "http" in line or "." in line:
                        # intentar extraer URL
                        parts = line.split("-")
                        if len(parts) >= 2 and (parts[-1].strip().startswith("http") or "." in parts[-1]):
                            website = parts[-1].strip()
                            name = "-".join(parts[:-1]).strip()
                        else:
                            website = line.strip()
                            name = ""
                        results.append({
                            "place_id": None,
                            "name": name,
                            "website": website,
                            "formatted_address": "",
                            "url": website
                        })
                    else:
                        # si no parece URL, lo interpretamos como nombre de negocio sin web
                        results.append({
                            "place_id": None,
                            "name": line,
                            "website": "",
                            "formatted_address": "",
                            "url": ""
                        })

    rows = []

    # Preparar lista de tareas: por cada item, si tiene website y se permite scan, se escanea
    tasks = []
    for r in results:
        place_id = r.get("place_id")
        if place_id:
            # We will fetch details later in worker if needed
            website = None
        else:
            website = r.get("website") or r.get("url")
        tasks.append((r, website))

    def process_item(r, website, humanize=False):
        # Obtener detalles si tenemos place_id
        place_id = r.get("place_id")
        d = r
        if place_id:
            try:
                d = place_details(api_key, place_id)
            except requests.RequestException as e:
                human_print(f"[warn] falló details para {place_id}: {e}", humanize=humanize)
                d = r
        name = (d.get("name") or r.get("name") or "")
        phone = d.get("formatted_phone_number") or d.get("international_phone_number") or r.get('phone_raw') or r.get('Teléfono') or ""
        website_local = d.get("website") or r.get("website") or website or ""
        address = d.get("formatted_address") or r.get("formatted_address") or ""
        city = args.city or r.get('city_raw') or ""

        # Si el CSV ya trae correo, úsalo. Si no y hay sitio y el usuario permite scan, intentar
        email_list = []
        if r.get('email_raw'):
            email_list = [r.get('email_raw')]
        elif website_local and not args.no_email_scan:
            try:
                email_list = find_emails_on_site(website_local, max_pages=args.email_scan_pages)
            except Exception:
                email_list = []

        emails = ", ".join(email_list) if email_list else "N/A"
        phone_out = phone if phone else "N/A"
        website_out = website_local if website_local else "N/A"

        return {
            "Nombre": name.strip(),
            "Teléfono": phone_out.strip(),
            "Correo": emails.strip(),
            "Página Web": website_out.strip(),
            "Ciudad": city.strip(),
            "Dirección (opcional)": address.strip(),
            "Google Maps URL (opcional)": d.get("url", "").strip(),
            "place_id (debug)": place_id
        }

    # Ejecutar en paralelo si el usuario lo pide
    if getattr(args, "workers", None) and args.workers > 1:
        human_print(f"[i] Ejecutando con {args.workers} workers...", humanize=args.humanize, speed=args.humanize_speed)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(process_item, r, website, args.humanize): (r, website) for (r, website) in tasks}
            for i, fut in enumerate(as_completed(futures), 1):
                try:
                    row = fut.result()
                except Exception as e:
                    human_print(f"[warn] error en worker: {e}", humanize=args.humanize, speed=args.humanize_speed)
                    continue
                rows.append(row)
                if i % 20 == 0:
                    human_print(f"[i] procesados {i}/{len(tasks)} ...", humanize=args.humanize, speed=args.humanize_speed)
    else:
        # Secuencial
        for idx, (r, website) in enumerate(tasks, 1):
            row = process_item(r, website, args.humanize)
            rows.append(row)
            time.sleep(0.3 if args.no_email_scan else 1.0)
            if idx % 20 == 0:
                human_print(f"[i] procesados {idx}/{len(tasks)} ...", humanize=args.humanize, speed=args.humanize_speed)

    if not rows:
        print("[i] No se recolectó data.")
        return

    df = pd.DataFrame(rows, columns=[
        "Nombre", "Teléfono", "Correo", "Página Web", "Ciudad",
        "Dirección (opcional)", "Google Maps URL (opcional)", "place_id (debug)"
    ])

    if args.gsheet_id:
        print(f"[i] Escribiendo en Google Sheets (spreadsheet={args.gsheet_id}, worksheet={args.worksheet})")
        write_to_gsheets(df, args.gsheet_id, args.worksheet, args.sa_json)
        print("[✓] Google Sheets actualizado.")

    if args.outfile:
        out = args.outfile
        if out.lower().endswith(".csv"):
            df.to_csv(out, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(out, index=False, engine="openpyxl")
        print(f"[✓] Archivo guardado -> {out}")

    if args.out_txt:
        # Guardar una versión simple en texto
        with open(args.out_txt, "w", encoding="utf-8") as fh:
            for _, row in df.iterrows():
                # línea compacta: Nombre | Teléfono | Correo | Web | Ciudad | Dirección
                line = " | ".join([str(row.get(c, "")) for c in [
                    "Nombre", "Teléfono", "Correo", "Página Web", "Ciudad", "Dirección (opcional)"
                ]])
                fh.write(line + "\n")
        print(f"[✓] Archivo de texto guardado -> {args.out_txt}")

    if not args.gsheet_id and not args.outfile:
        df.to_csv("resultados.csv", index=False, encoding="utf-8-sig")
        print("[i] No indicaste salida. Guardado por defecto -> resultados.csv")

if __name__ == "__main__":
    main()