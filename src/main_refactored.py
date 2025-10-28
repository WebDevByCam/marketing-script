"""
Aplicación principal refactorizada siguiendo SOLID principles.
Ejemplo de uso de la nueva arquitectura con inyección de dependencias.
"""
import os
from pathlib import Path

from src.config.app_config import AppConfig
from src.services import (
    BusinessSearchService,
    DataProcessor,
    DataWriter,
    DuplicateDetector,
    GooglePlacesDataSource,
    ContactInfoExtractor
)
from src.utils.logger import Logger


def create_business_search_application():
    """
    Crea una instancia de la aplicación de búsqueda de negocios
    con todas las dependencias inyectadas siguiendo DIP.
    """
    # Configuración centralizada
    config = AppConfig()

    # Logger centralizado
    logger = Logger()

    # Dependencias de bajo nivel (concretas)
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY environment variable is required")

    data_source = GooglePlacesDataSource(api_key, logger)
    contact_extractor = ContactInfoExtractor(logger)
    duplicate_detector = DuplicateDetector(logger=logger)

    # Servicios de nivel medio
    data_processor = DataProcessor(duplicate_detector, logger)
    data_writer = DataWriter(config.get_output_path(), logger)

    # Servicio de alto nivel (inyectando dependencias)
    search_service = BusinessSearchService(
        data_source=data_source,
        contact_extractor=contact_extractor,
        logger=logger
    )

    return {
        'search_service': search_service,
        'data_processor': data_processor,
        'data_writer': data_writer,
        'config': config,
        'logger': logger
    }


def main():
    """
    Función principal que demuestra el uso de la nueva arquitectura SOLID.
    """
    try:
        # Crear aplicación con inyección de dependencias
        app = create_business_search_application()
        logger = app['logger']
        search_service = app['search_service']
        data_processor = app['data_processor']
        data_writer = app['data_writer']

        logger.info("Iniciando aplicación de búsqueda de negocios")

        # Parámetros de búsqueda (podrían venir de UI)
        city = "Madrid"  # Ejemplo
        business_type = "restaurant"
        target_count = 50

        # Ejecutar búsqueda usando el servicio de alto nivel
        logger.info(f"Buscando {target_count} {business_type} en {city}")
        raw_businesses = search_service.search_businesses_with_contacts(
            city=city,
            business_type=business_type,
            target_count=target_count
        )

        if not raw_businesses:
            logger.warning("No se encontraron negocios con información de contacto válida")
            return

        # Procesar datos usando el servicio de procesamiento
        logger.info("Procesando datos obtenidos")
        processed_df = data_processor.process_business_data(raw_businesses)

        if processed_df.empty:
            logger.warning("No quedaron datos válidos después del procesamiento")
            return

        # Guardar resultados en múltiples formatos
        base_filename = f"{business_type}_{city.lower().replace(' ', '_')}"
        output_files = data_writer.write_multiple_formats(processed_df, base_filename)

        logger.info("Búsqueda completada exitosamente")
        logger.info(f"Resultados guardados en: {list(output_files.keys())}")

        # Mostrar resumen
        print("\n=== RESULTADOS DE BÚSQUEDA ===")
        print(f"Ciudad: {city}")
        print(f"Tipo de negocio: {business_type}")
        print(f"Total encontrados: {len(raw_businesses)}")
        print(f"Total procesados: {len(processed_df)}")
        print(f"Archivos generados: {len(output_files)}")
        print(f"Ubicación: {app['config'].get_output_path()}")

        for format_name, file_path in output_files.items():
            print(f"- {format_name.upper()}: {file_path.name}")

    except Exception as e:
        logger.error("Error en la ejecución principal", exc=e)
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())