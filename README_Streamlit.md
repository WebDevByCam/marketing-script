# Marketing Script - Dashboard Web

Aplicación web completa para gestión de datos de marketing usando Streamlit.

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar API Key
Crea un archivo `.env` en la raíz del proyecto:
```env
GOOGLE_API_KEY=tu_api_key_aqui
```

### 3. Ejecutar la aplicación
```bash
streamlit run app.py
```

La aplicación estará disponible en: http://localhost:8501

## 📋 Funcionalidades

### 🔍 Buscar Empresas
- Búsqueda de empresas por ciudad y tipo de negocio
- Verificación automática de información de contacto (teléfono/WhatsApp)
- Escaneo opcional de emails en páginas web
- Resultados exportables a CSV/Excel

### 🔄 Verificar Duplicados
- Comparación automática con base de datos existente
- Detección de duplicados por nombre y sitio web
- Opciones para filtrar o buscar empresas adicionales
- Reportes detallados de conflictos

### 📊 Merge Final
- Integración de nuevos datos con Excel maestro
- Preservación del archivo original
- Validación de integridad de datos
- Descarga automática de resultados

### 📁 Gestión de Archivos
- Vista organizada por directorios (Input/Output/Merged)
- Información detallada de archivos
- Descargas directas
- Previews de datos

## 🏗️ Arquitectura

```
marketing-script/
├── app.py                 # Aplicación principal Streamlit
├── requirements.txt       # Dependencias Python
├── .env                   # Variables de entorno (API keys)
├── .streamlit/           # Configuración Streamlit
│   └── config.toml
├── src/                  # Código fuente
│   ├── business_processor.py
│   ├── email_scraper.py
│   ├── output_writer.py
│   └── places_api.py
├── data/                 # Datos y archivos
│   ├── input/           # Excel maestro
│   ├── output/          # Resultados de búsqueda
│   └── merged/          # Archivos combinados
└── scripts/             # Scripts CLI
    ├── run_interactive.py
    ├── pre_merge.py
    └── merge_final.py
```

## ⚙️ Configuración

### Variables de Entorno (.env)
Crea un archivo `.env` en la raíz del proyecto:
```env
# API de Google Places (requerido)
GOOGLE_API_KEY=tu_clave_api_google_places

# Autenticación (opcional - valores por defecto si no se configuran)
AUTH_USERS=admin,usuario2
AUTH_PASSWORDS=admin123,password456
AUTH_NAMES=Administrador,Usuario 2
```

### Directorios de Datos
La aplicación crea automáticamente los directorios necesarios:
- `data/input/` - Coloca aquí tu Excel maestro
- `data/output/` - Resultados de búsquedas
- `data/merged/` - Archivos combinados

## 🔐 Autenticación

La aplicación incluye **autenticación básica** para proteger el acceso:

### Configuración de Usuarios
- **Variables de entorno**: Configura múltiples usuarios separados por comas
- **Por defecto**: Si no configuras usuarios, usa `admin` / `admin123`
- **Múltiples usuarios**: Soporta varios usuarios con diferentes permisos

### Credenciales de Ejemplo
```env
AUTH_USERS=admin,marketing,analista
AUTH_PASSWORDS=secure123,market456,analyst789
AUTH_NAMES=Administrador,Marketing,Analista
```

### Seguridad
- **Sesiones**: Las sesiones expiran después de 1 día
- **Cookies**: Uso de cookies seguras para mantener la sesión
- **Protección**: Solo usuarios autenticados pueden acceder a las funciones

## 🌐 Despliegue en Netlify

### 1. Preparar para Netlify
```bash
# Crear netlify.toml
[build]
  command = "pip install -r requirements.txt"
  publish = "."

[build.environment]
  PYTHON_VERSION = "3.9"

[[redirects]]
  from = "/*"
  to = "/.netlify/functions/streamlit"
  status = 200
```

### 2. Variables de entorno en Netlify
En el dashboard de Netlify, configura:
- `GOOGLE_API_KEY` = tu clave API

### 3. Desplegar
1. Sube el código a GitHub
2. Conecta el repositorio en Netlify
3. ¡Listo! Tendrás una URL pública

## 🔧 Desarrollo

### Ejecutar en modo desarrollo
```bash
streamlit run app.py --server.headless true --server.port 8501
```

### Tests
```bash
pytest tests/
```

### Formateo de código
```bash
black .
flake8 .
```

## 📊 Flujo de Trabajo

1. **Configuración inicial**: Coloca tu Excel maestro en `data/input/`
2. **Buscar empresas**: Usa la interfaz para encontrar nuevos contactos
3. **Verificar duplicados**: Revisa conflictos antes del merge
4. **Merge final**: Integra los datos verificados
5. **Descargar resultados**: Obtén el Excel actualizado

## 🐛 Solución de Problemas

### Error de API Key
- Verifica que el archivo `.env` existe y contiene `GOOGLE_API_KEY`
- Asegúrate de que la clave de Google Places API es válida

### Sin resultados de búsqueda
- Verifica la ortografía de ciudad y tipo de negocio
- Intenta con términos más generales
- Revisa los límites de la API de Google

### Problemas de merge
- Asegúrate de que hay un archivo Excel en `data/input/`
- Verifica que las columnas del Excel coincidan con el formato esperado

## 📝 Notas

- La aplicación está optimizada para búsquedas de hasta 100 empresas por vez
- Todos los resultados incluyen verificación de contacto (teléfono o WhatsApp)
- Los archivos originales se preservan automáticamente antes del merge
- La interfaz es responsive y funciona en dispositivos móviles

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.