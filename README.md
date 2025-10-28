# Marketing Script - Recolector de Datos de Negocios

Script profesional para recolectar información de negocios usando Google Places API o archivos de entrada, extraer datos de contacto mediante web scraping, y exportar resultados a Excel local con gestión de backups automáticos.

## 🚀 Características

- **Múltiples fuentes de datos**: Google Places API o archivos CSV/TXT
- **Web scraping inteligente**: Extracción automática de emails de sitios web
- **Rate limiting automático**: Respeta límites de Google (600 requests/minuto)
- **Backups automáticos**: Copias de seguridad con timestamp antes de modificar datos
- **Flujo de revisión**: Genera Excel para revisión antes del merge final
- **Procesamiento paralelo**: Acelera la recolección con múltiples workers
- **Múltiples formatos de salida**: CSV, Excel, TXT
- **Interfaz humanizada**: Efectos de tipeo para demostraciones
- **Código modular**: Fácil de mantener y extender

## 📋 Requisitos

- Python 3.8+
- Entorno virtual recomendado

## 🛠️ Instalación

1. **Clonar y preparar entorno**:
   ```bash
   cd marketing-script
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tu GOOGLE_API_KEY si vas a usar Places API
   ```

## 📖 Flujo de Trabajo

### Modo Interactivo (Recomendado)

Este es el flujo completo para buscar empresas y actualizar tu base de datos:

1. **Coloca tu Excel maestro** en `data/input/`:
   ```bash
   # Tu archivo debe tener las columnas: Nombre, WhatsApp, Telefono, Correo, Pagina Web, Ciudad
   cp "mi_base_datos.xlsx" data/input/
   ```

2. **Ejecuta la búsqueda interactiva**:
   ```bash
   python run_interactive.py
   ```
   
   El script te preguntará:
   - ¿Cuántas empresas buscamos? (número)
   - ¿De qué ciudad y país? (ej: Bogotá, Colombia)
   - ¿De qué sector o tipo de mercado? (ej: restaurantes, hoteles)
   
   El script automáticamente:
   - ✅ Crea un backup del Excel maestro en `data/backups/`
   - ✅ Busca empresas en Google Places API con rate limiting
   - ✅ Genera un Excel nuevo en `data/output/` para revisión
   - ✅ Usa formato exacto del template (6 columnas)

3. **Revisa el archivo generado** en `data/output/`:
   - Abre el Excel generado
   - Verifica que los datos sean correctos
   - Valida nombres, teléfonos, correos, websites, ciudades

4. **Ejecuta el merge final** (solo después de revisar):
   ```bash
   python merge_final.py
   ```
   
   El script automáticamente:
   - ✅ Crea otro backup del Excel maestro
   - ✅ Fusiona los datos nuevos sin agregar columnas
   - ✅ Actualiza el Excel maestro en `data/input/`
   - ✅ Distingue números móviles (WhatsApp) vs fijos (Telefono)

### Modo CLI (Avanzado)

```bash
# Buscar hoteles en Medellín
python main.py --city "Medellín" --type "hotel" --limit 50 --outfile hoteles_medellin.xlsx

# Con procesamiento paralelo y efectos visuales
python main.py --city "Bogotá" --type "restaurant" --workers 3 --humanize --outfile restaurantes.csv

# Procesar CSV existente
python main.py --input-file examples/empresas_ibague.csv --out-txt resultados.txt --workers 2

# Procesar archivo TXT simple
python main.py --input-file examples/empresas_ibague.txt --outfile procesados.xlsx --no-email-scan
```

## 📁 Estructura del proyecto

```
marketing-script/
├── main.py                    # Script principal (CLI avanzado)
├── run_interactive.py         # Script interactivo (recomendado)
├── merge_final.py             # Script para merge después de revisión
├── requirements.txt           # Dependencias
├── .env.example              # Configuración de ejemplo
├── README.md                 # Documentación
├── data/                     # Carpeta de datos
│   ├── input/               # Excel maestro (tu base de datos)
│   ├── output/              # Excel generado para revisión
│   └── backups/             # Copias de seguridad automáticas
├── examples/                 # Archivos de ejemplo
│   ├── empresas_ibague.csv
│   └── empresas_ibague.txt
└── src/                      # Módulos del código
    ├── __init__.py
    ├── business_processor.py  # Procesador principal
    ├── email_scraper.py      # Scraping de emails
    ├── places_api.py         # Cliente Google Places + rate limiting
    ├── output_writer.py      # Escritura de resultados + backups
    └── utils.py              # Utilidades
```

## 🔧 Configuración

### Google Places API (New)

1. Habilita **Places API (New)** en [Google Cloud Console](https://console.cloud.google.com/apis/library/places.googleapis.com)
2. Crea una API key en [Credenciales](https://console.cloud.google.com/apis/credentials)
3. Añade la key a tu archivo `.env`:
   ```
   GOOGLE_API_KEY=tu_api_key_aqui
   ```

### Archivo .env

Copia `.env.example` a `.env` y configura:
```bash
cp .env.example .env
# Edita .env con tu GOOGLE_API_KEY
```

### Consideraciones Éticas y Legales

Este script está diseñado para respetar las políticas de Google:

- ✅ **Rate Limiting**: Implementado con 600 requests/minuto máximo (límite de Google)
- ✅ **Robots.txt**: Verifica permisos antes de scrapear sitios web
- ✅ **Delays Configurables**: Usa `--delay` para controlar frecuencia de requests
- ✅ **No Abuso**: Limita workers paralelos y añade sleeps entre requests
- ✅ **Términos de Servicio**: Compatible con Places API (New) y políticas de scraping ético
- ✅ **Backups Automáticos**: Protege tus datos con copias antes de modificar

**Recomendaciones para uso responsable:**
- El script respeta automáticamente el límite de 600 req/min de Google
- Respeta robots.txt de los sitios web
- Usa delays de al menos 1-2 segundos entre requests para scraping
- Limita workers a 2-3 para evitar sobrecarga

## 🔄 Sistema de Backups

### Backups Automáticos

El sistema crea copias de seguridad automáticas en estas situaciones:

1. **Antes de búsqueda**: Al ejecutar `run_interactive.py`, se crea backup del Excel en `data/input/`
2. **Antes de merge**: Al ejecutar `merge_final.py`, se crea otro backup antes de modificar

### Formato de Backups

Los archivos se guardan con timestamp para fácil identificación:
```
data/backups/
├── Plan_de_mercadeo_backup_20251027_115725.xlsx
├── Plan_de_mercadeo_backup_20251027_120530.xlsx
└── Plan_de_mercadeo_backup_20251027_121045.xlsx
```

Formato: `{nombre_original}_backup_{YYYYMMDD_HHMMSS}.xlsx`

### Restaurar desde Backup

Si necesitas restaurar un backup:
```bash
# Encuentra el backup que quieres restaurar
ls data/backups/

# Copia de vuelta a input/
cp data/backups/Plan_de_mercadeo_backup_20251027_115725.xlsx data/input/Plan_de_mercadeo.xlsx
```

## 🎯 Heurística de Números (Colombia)

El sistema distingue automáticamente entre números móviles y fijos:

### Regla de Clasificación

Después de limpiar el prefijo del país (57):
- **Móvil (WhatsApp)**: Si el primer dígito es `3` → columna `WhatsApp`
- **Fijo (Telefono)**: Si el primer dígito NO es `3` → columna `Telefono`

### Ejemplos

```
573001234567  → WhatsApp: 3001234567  (empieza con 3)
576012345678  → Telefono: 6012345678  (empieza con 6)
573211112222  → WhatsApp: 3211112222  (empieza con 3)
572123456     → Telefono: 2123456     (empieza con 2)
```

Esta heurística funciona bien para Colombia. Si trabajas con otros países, puedes modificarla en `src/output_writer.py` en la función `looks_like_mobile()`.

## 📊 Formatos de entrada

### Archivo CSV
```csv
nombre,telefono,email,website,ciudad,direccion
Hotel Central,+57 300 123 4567,info@hotel.com,https://hotel.com,Ibagué,Carrera 3 # 12-34
```

### Archivo TXT
```
Hotel Central - https://hotelcentral.com
Restaurante Plaza - https://restaurante.com
Café Solo (sin URL)
https://sitioweb.com
```

## 🎯 Opciones avanzadas

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--workers N` | Procesamiento paralelo | `--workers 3` |
| `--humanize` | Efectos de tipeo | `--humanize --humanize-speed 0.01` |
| `--no-email-scan` | Saltar búsqueda de emails | Para mayor velocidad |
| `--email-scan-pages N` | Páginas a revisar por sitio | `--email-scan-pages 3` |
| `--verbose` | Salida detallada | Para debugging |

## 🧪 Ejemplos de prueba

```bash
# Prueba rápida con archivo de ejemplo (sin scraping)
python main.py --input-file examples/empresas_ibague.csv --out-txt prueba.txt --no-email-scan

# Prueba con scraping real (usa sitios de ejemplo)
python main.py --input-file examples/empresas_ibague.txt --outfile prueba.xlsx --workers 2

# Prueba completa con Places API (requiere API key)
python main.py --city "Medellín" --type "hotel" --limit 10 --outfile hoteles_test.csv --humanize
```

## 🔍 Solución de problemas

### Errores comunes

1. **ModuleNotFoundError**: Asegúrate de activar el entorno virtual y instalar dependencias
   ```bash
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **API key error**: Verifica que `GOOGLE_API_KEY` esté configurada correctamente en `.env`
   ```bash
   # Verifica que existe el archivo .env
   cat .env
   # Debe contener: GOOGLE_API_KEY=tu_key_aqui
   ```

3. **Rate limit exceeded**: El script implementa rate limiting automático de 600 req/min
   - Si ves este error, puede ser temporal
   - Espera 1 minuto y reintenta
   - Reduce el límite de búsqueda para consumir menos requests

4. **No se encontró archivo en data/input/**: Asegúrate de colocar tu Excel maestro allí
   ```bash
   cp "tu_archivo.xlsx" data/input/
   ```

5. **Timeout en scraping**: Reduce `--workers` o usa `--no-email-scan`

6. **Encoding errors**: Los archivos se guardan con UTF-8, abre con un editor compatible

7. **Columnas incorrectas en Excel**: El template espera estas columnas exactas:
   - Nombre
   - WhatsApp
   - Telefono
   - Correo
   - Pagina Web
   - Ciudad

### Validación de datos

Antes de hacer merge, siempre:
1. ✅ Revisa el archivo en `data/output/`
2. ✅ Verifica que los nombres sean correctos
3. ✅ Valida que los teléfonos tengan formato correcto
4. ✅ Comprueba que los websites sean válidos
5. ✅ Confirma que las ciudades correspondan

### Recomendaciones para producción

- Usa `run_interactive.py` para búsquedas nuevas (flujo completo)
- Siempre revisa el output antes de hacer merge
- Mantén backups actualizados (se crean automáticamente)
- Para búsquedas grandes, hazlo en lotes pequeños (50-100 por vez)
- Monitorea uso de la API de Google para evitar límites

## 🧪 Testing

### Test Local (sin API)

```bash
# Activar entorno
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Test de componentes básicos
python -c "
from src.output_writer import OutputWriter
import os

# Test backup
writer = OutputWriter(humanize=False)
backup = writer.create_backup('data/input/tu_excel.xlsx')
print(f'Backup creado: {backup}')

# Test write con template columns
test_data = [{'Nombre': 'Test', 'Ciudad': 'Bogota'}]
writer.write_to_excel(test_data, 'data/output/test.xlsx', use_template_columns=True)
print('Excel de prueba generado')
"
```

### Test Real (con API)

```bash
# Test rápido con 3 negocios
python test_api_quick.py

# Esto valida:
# - Rate limiting funciona
# - Formato Excel correcto
# - Columnas template
# - Datos completos
```

## 📝 Próximas mejoras

- [ ] Soporte para robots.txt
- [ ] Cache de resultados
- [ ] Interfaz web
- [ ] Validación de datos más robusta
- [ ] Exportación a formatos adicionales (JSON, XML)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.