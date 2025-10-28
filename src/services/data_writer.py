"""
Servicio de escritura de datos.
Implementa IDataWriter siguiendo SRP.
"""
from typing import List, Dict, Any
import pandas as pd
from pathlib import Path

from ..interfaces import IDataWriter, ILogger
from ..utils.logger import Logger


class DataWriter(IDataWriter):
    """Servicio para escribir datos procesados en diferentes formatos."""

    def __init__(self, output_dir: Path = None, logger: ILogger = None):
        self._output_dir = output_dir or Path.cwd() / "output"
        self._output_dir.mkdir(exist_ok=True)
        self._logger = logger or Logger()

    def write_to_csv(self, data: pd.DataFrame, filename: str) -> Path:
        """
        Escribe datos a archivo CSV.

        Args:
            data: DataFrame con los datos
            filename: Nombre del archivo (sin extensión)

        Returns:
            Path al archivo creado
        """
        output_path = self._output_dir / f"{filename}.csv"

        try:
            self._logger.info(f"Escribiendo {len(data)} registros a {output_path}")

            data.to_csv(output_path, index=False, encoding='utf-8-sig')
            self._logger.info(f"Archivo CSV creado exitosamente: {output_path}")

            return output_path

        except Exception as e:
            self._logger.error(f"Error escribiendo archivo CSV: {output_path}", exc=e)
            raise

    def write_to_excel(self, data: pd.DataFrame, filename: str, sheet_name: str = "Businesses") -> Path:
        """
        Escribe datos a archivo Excel.

        Args:
            data: DataFrame con los datos
            filename: Nombre del archivo (sin extensión)
            sheet_name: Nombre de la hoja de Excel

        Returns:
            Path al archivo creado
        """
        output_path = self._output_dir / f"{filename}.xlsx"

        try:
            self._logger.info(f"Escribiendo {len(data)} registros a {output_path}")

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name=sheet_name, index=False)

            self._logger.info(f"Archivo Excel creado exitosamente: {output_path}")

            return output_path

        except Exception as e:
            self._logger.error(f"Error escribiendo archivo Excel: {output_path}", exc=e)
            raise

    def write_to_json(self, data: List[Dict[str, Any]], filename: str) -> Path:
        """
        Escribe datos a archivo JSON.

        Args:
            data: Lista de diccionarios con los datos
            filename: Nombre del archivo (sin extensión)

        Returns:
            Path al archivo creado
        """
        output_path = self._output_dir / f"{filename}.json"

        try:
            self._logger.info(f"Escribiendo {len(data)} registros a {output_path}")

            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            self._logger.info(f"Archivo JSON creado exitosamente: {output_path}")

            return output_path

        except Exception as e:
            self._logger.error(f"Error escribiendo archivo JSON: {output_path}", exc=e)
            raise

    def write_multiple_formats(self, data: pd.DataFrame, base_filename: str) -> Dict[str, Path]:
        """
        Escribe datos en múltiples formatos.

        Args:
            data: DataFrame con los datos
            base_filename: Nombre base para los archivos

        Returns:
            Diccionario con paths de archivos creados
        """
        results = {}

        try:
            # CSV
            results['csv'] = self.write_to_csv(data, base_filename)

            # Excel
            results['excel'] = self.write_to_excel(data, base_filename)

            # JSON (convertir DataFrame a lista de dicts)
            json_data = data.to_dict('records')
            results['json'] = self.write_to_json(json_data, base_filename)

            self._logger.info(f"Datos escritos en {len(results)} formatos")

        except Exception as e:
            self._logger.error("Error escribiendo datos en múltiples formatos", exc=e)
            raise

        return results