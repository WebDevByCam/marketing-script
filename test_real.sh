#!/bin/bash
# Script de prueba para entorno real
# Ejecuta diferentes escenarios de uso del marketing script

echo "🧪 Marketing Script - Pruebas de entorno real"
echo "============================================"

PYTHON_CMD="C:/code/marketing-script/.venv/Scripts/python.exe"

echo ""
echo "📁 Prueba 1: Archivo CSV sin scraping (rápido)"
echo "----------------------------------------------"
$PYTHON_CMD main.py \
  --input-file examples/empresas_ibague.csv \
  --outfile resultados_csv_test.xlsx \
  --out-txt resultados_csv_test.txt \
  --no-email-scan \
  --humanize \
  --verbose

echo ""
echo "📁 Prueba 2: Archivo TXT con scraping limitado"
echo "---------------------------------------------"
$PYTHON_CMD main.py \
  --input-file examples/empresas_ibague.txt \
  --outfile resultados_txt_test.csv \
  --workers 2 \
  --email-scan-pages 1 \
  --humanize-speed 0.01 \
  --verbose

echo ""
echo "🌐 Prueba 3: Places API (requiere GOOGLE_API_KEY)"
echo "------------------------------------------------"
if [ -f .env ] && grep -q "GOOGLE_API_KEY=" .env; then
    echo "API key encontrada, ejecutando prueba con Places API..."
    $PYTHON_CMD main.py \
      --city "Ibagué" \
      --type "hotel" \
      --limit 5 \
      --outfile hoteles_places_test.xlsx \
      --workers 2 \
      --humanize \
      --verbose
else
    echo "⚠️  No se encontró GOOGLE_API_KEY en .env - saltando prueba de Places API"
    echo "   Para probar: copia .env.example a .env y añade tu API key"
fi

echo ""
echo "📊 Resumen de archivos generados:"
echo "--------------------------------"
ls -la *.xlsx *.csv *.txt 2>/dev/null | grep -E "\.(xlsx|csv|txt)$" || echo "No se generaron archivos"

echo ""
echo "✅ Pruebas completadas!"
echo "💡 Revisa los archivos generados para verificar la calidad de los datos"