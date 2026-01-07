#!/bin/bash
# Script para ejecutar el procesamiento diario de newsletters
# Ejecuta automáticamente a las 6:00 PM

cd /Users/ulisesgonzalez/Documents/newsletter-digest
source venv/bin/activate

LOG_FILE="/Users/ulisesgonzalez/Documents/newsletter-digest/cron.log"

echo "========================================" >> "$LOG_FILE"
echo "Ejecutando: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Verificar si LM Studio está corriendo
if ! curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "LM Studio no está corriendo. Iniciando..." >> "$LOG_FILE"
    open -a "LM Studio"

    # Esperar hasta 60 segundos a que el servidor esté listo
    for i in {1..12}; do
        sleep 5
        if curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
            echo "LM Studio servidor listo" >> "$LOG_FILE"
            break
        fi
        echo "Esperando servidor LM Studio... intento $i/12" >> "$LOG_FILE"
    done
fi

# Verificar nuevamente si el servidor está disponible
if ! curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "ERROR: LM Studio servidor no disponible después de 60s" >> "$LOG_FILE"
    osascript -e 'display notification "LM Studio no está disponible. Inicia el servidor manualmente." with title "Newsletter Digest - Error"'
    exit 1
fi

# Ejecutar procesamiento
echo "Iniciando procesamiento..." >> "$LOG_FILE"
python3 process_all.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Completado exitosamente: $(date)" >> "$LOG_FILE"
    osascript -e 'display notification "Digest de newsletters completado" with title "Newsletter Digest"'
else
    echo "Error en procesamiento (código: $EXIT_CODE): $(date)" >> "$LOG_FILE"
    osascript -e 'display notification "Error procesando newsletters. Revisa cron.log" with title "Newsletter Digest - Error"'
fi

echo "" >> "$LOG_FILE"
