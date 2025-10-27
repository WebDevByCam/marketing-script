# Marketing Script - Recolector de Datos de Negocios

Script profesional para recolectar información de negocios usando Google Places API o archivos de entrada, extraer datos de contacto mediante web scraping, y exportar resultados a múltiples formatos.

## 🚀 Características

- **Múltiples fuentes de datos**: Google Places API o archivos CSV/TXT
- **Web scraping inteligente**: Extracción automática de emails de sitios web
- **Procesamiento paralelo**: Acelera la recolección con múltiples workers
- **Múltiples formatos de salida**: CSV, Excel, TXT, Google Sheets
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

## 📖 Uso

### Modo Google Places API

```bash
# Buscar hoteles en Medellín
python main.py --city "Medellín" --type "hotel" --limit 50 --outfile hoteles_medellin.xlsx

# Con procesamiento paralelo y efectos visuales
python main.py --city "Bogotá" --type "restaurant" --workers 3 --humanize --outfile restaurantes.csv
```

### Modo archivo de entrada

```bash
# Procesar CSV existente
python main.py --input-file examples/empresas_ibague.csv --out-txt resultados.txt --workers 2

# Procesar archivo TXT simple
python main.py --input-file examples/empresas_ibague.txt --outfile procesados.xlsx --no-email-scan
```

### Modo Google Sheets

```bash
# Escribir directamente a Google Sheets
python main.py --city "Cali" --type "spa" --gsheet-id "1ABC...XYZ" --worksheet "Spas Cali" --sa-json credenciales.json
```

## 📁 Estructura del proyecto

```
marketing-script/
├── main.py                 # Script principal
├── requirements.txt        # Dependencias
├── .env.example           # Configuración de ejemplo
├── README.md              # Documentación
├── examples/              # Archivos de ejemplo
│   ├── empresas_ibague.csv
│   └── empresas_ibague.txt
└── src/                   # Módulos del código
    ├── __init__.py
    ├── business_processor.py  # Procesador principal
    ├── email_scraper.py      # Scraping de emails
    ├── places_api.py         # Cliente Google Places
    ├── output_writer.py      # Escritura de resultados
    └── utils.py              # Utilidades
```

## 🔧 Configuración

### Google Places API

1. Habilita la Places API en [Google Cloud Console](https://console.cloud.google.com/apis/library/places-backend.googleapis.com)
2. Crea una API key en [Credenciales](https://console.cloud.google.com/apis/credentials)
3. Añade la key a tu archivo `.env`:
   ```
   GOOGLE_API_KEY=tu_api_key_aqui
   ```

### Google Sheets (Opcional)

1. Crea una Service Account en Google Cloud
2. Descarga el archivo JSON de credenciales
3. Comparte tu spreadsheet con el email de la Service Account
4. Usa `--sa-json path/to/credentials.json` o configura `GOOGLE_APPLICATION_CREDENTIALS`

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
2. **API key error**: Verifica que `GOOGLE_API_KEY` esté configurada correctamente
3. **Timeout en scraping**: Reduce `--workers` o usa `--no-email-scan`
4. **Encoding errors**: Los archivos se guardan con UTF-8, abre con un editor compatible

### Recomendaciones para producción

- Usa `--workers 2-4` para balance entre velocidad y estabilidad
- Implementa delays entre requests para sitios sensibles
- Considera usar proxies para scraping intensivo
- Monitorea uso de la API de Google para evitar límites

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