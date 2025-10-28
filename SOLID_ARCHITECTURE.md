# Arquitectura SOLID - Sistema de Marketing

Este proyecto ha sido refactorizado siguiendo los principios SOLID para crear una arquitectura modular, mantenible y extensible.

## 🏗️ Arquitectura Implementada

### Principios SOLID Aplicados

1. **S - Single Responsibility Principle (SRP)**
   - Cada clase tiene una única responsabilidad
   - Servicios especializados para cada aspecto del negocio

2. **O - Open/Closed Principle (OCP)**
   - Interfaces abiertas a extensión, cerradas a modificación
   - Nuevas implementaciones pueden agregarse sin cambiar código existente

3. **L - Liskov Substitution Principle (LSP)**
   - Implementaciones pueden substituirse por sus interfaces
   - Todas las implementaciones son intercambiables

4. **I - Interface Segregation Principle (ISP)**
   - Interfaces específicas y pequeñas
   - Clientes no dependen de interfaces que no usan

5. **D - Dependency Inversion Principle (DIP)**
   - Dependencia de abstracciones, no de concretos
   - Inyección de dependencias para desacoplar componentes

## 📁 Estructura del Proyecto

```
src/
├── interfaces/          # Contratos y abstracciones (ISP)
│   └── __init__.py     # Definiciones de interfaces
├── config/             # Configuración centralizada
│   └── app_config.py   # Singleton para configuración
├── utils/              # Utilidades compartidas
│   ├── logger.py       # Sistema de logging centralizado
│   └── __init__.py
├── services/           # Implementaciones concretas (SRP)
│   ├── business_search_service.py     # Servicio de búsqueda
│   ├── data_processor.py              # Procesamiento de datos
│   ├── data_writer.py                 # Escritura de datos
│   ├── merge_service.py               # Fusión de datos
│   ├── duplicate_detector.py          # Detección de duplicados
│   ├── google_places_data_source.py   # Fuente de datos Google Places
│   ├── contact_info_extractor.py      # Extracción de contactos
│   └── __init__.py
└── main_refactored.py  # Aplicación principal con DI
```

## 🔧 Interfaces Definidas

### IBusinessSearchService
- `search_businesses_with_contacts(city, business_type, target_count)`
- Servicio de alto nivel que coordina búsqueda y extracción de contactos

### IDataProcessor
- `process_business_data(raw_data)`
- Procesamiento, limpieza y validación de datos

### IDataWriter
- `write_to_csv(data, filename)`
- `write_to_excel(data, filename)`
- `write_to_json(data, filename)`
- `write_multiple_formats(data, base_filename)`
- Escritura de datos en múltiples formatos

### IMergeService
- `merge_business_data(data_sources)`
- `merge_with_priority(primary_data, secondary_data)`
- `merge_by_business_name(dataframes)`
- Fusión de datos de múltiples fuentes

### IDuplicateDetector
- `detect_duplicates(data)`
- `find_similar_businesses(data, target_business)`
- Detección de registros duplicados

### IBusinessDataSource
- `search_businesses(city, business_type, limit)`
- Abstracción para fuentes de datos externas

### IContactInfoExtractor
- `extract_contacts(business_data)`
- `validate_contact_info(contact_info)`
- Extracción y validación de información de contacto

### IConfiguration
- Gestión centralizada de configuración

### ILogger
- Sistema de logging unificado

## 🚀 Uso de la Nueva Arquitectura

```python
from src.main_refactored import create_business_search_application

# Crear aplicación con inyección de dependencias
app = create_business_search_application()

# Usar servicios
businesses = app['search_service'].search_businesses_with_contacts(
    city="Madrid",
    business_type="restaurant",
    target_count=50
)

processed_data = app['data_processor'].process_business_data(businesses)
app['data_writer'].write_multiple_formats(processed_data, "restaurantes_madrid")
```

## 🔄 Beneficios de la Nueva Arquitectura

### Mantenibilidad
- **Separación de responsabilidades**: Cada clase tiene un propósito claro
- **Fácil testing**: Interfaces permiten mocks y stubs
- **Código legible**: Estructura modular facilita comprensión

### Extensibilidad
- **Nuevas fuentes de datos**: Implementar IBusinessDataSource
- **Nuevos formatos de salida**: Extender IDataWriter
- **Nuevos detectores**: Implementar IDuplicateDetector

### Testabilidad
- **Inyección de dependencias**: Fácil substitución en tests
- **Interfaces**: Permiten testing con doubles
- **SRP**: Lógica aislada facilita pruebas unitarias

### Robustez
- **Manejo de errores**: Logging centralizado y validaciones
- **Retry logic**: Tenacity para llamadas externas
- **Validaciones**: Información de contacto verificada

## 🛠️ Dependencias Agregadas

- `phonenumbers>=8.13.0`: Validación de números telefónicos
- `email-validator>=2.1.0`: Validación de direcciones email
- `tenacity>=8.2.0`: Lógica de reintento para APIs externas

## 📋 Próximos Pasos

1. **Refactorizar código legacy**: Actualizar archivos existentes para usar nuevas interfaces
2. **Implementar tests**: Crear suite de pruebas unitarias e integración
3. **Agregar más fuentes de datos**: Implementar otras APIs (Yelp, Foursquare, etc.)
4. **Mejorar UI**: Integrar nueva arquitectura con Streamlit
5. **Agregar métricas**: Sistema de monitoreo y analytics

## 🎯 Ejemplo de Extensión

Para agregar una nueva fuente de datos:

```python
from src.interfaces import IBusinessDataSource

class YelpDataSource(IBusinessDataSource):
    def search_businesses(self, city: str, business_type: str, limit: int = 20):
        # Implementación específica de Yelp API
        pass
```

La nueva implementación puede inyectarse sin cambiar el código existente gracias a DIP.