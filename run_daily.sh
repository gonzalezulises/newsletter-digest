#!/bin/bash
# Script para ejecutar el procesamiento diario de newsletters
# Usa Groq API (no requiere servidor local)

cd /Users/ulisesgonzalez/Documents/newsletter-digest
source venv/bin/activate

echo "========================================"
echo "Ejecutando: $(date)"
echo "========================================"

# Ejecutar procesamiento con Groq
python3 digest.py --label "data_science" --days 7 --max 50

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Completado exitosamente: $(date)"
    osascript -e 'display notification "Digest de newsletters completado" with title "Newsletter Digest"'
else
    echo "Error en procesamiento (código: $EXIT_CODE): $(date)"
    osascript -e 'display notification "Error procesando newsletters. Revisa cron.log" with title "Newsletter Digest - Error"'
fi

echo ""
