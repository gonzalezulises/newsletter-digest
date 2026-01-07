# CLAUDE.md - newsletter-digest

## PROTOCOLO DE CONTINUIDAD

**AL INICIAR cada sesión:**
1. Leer `PROJECT_STATE.md` para contexto actual
2. Verificar estado del cron en `cron.log`

**AL TERMINAR cada sesión:**
1. Actualizar "Completado Recientemente" en PROJECT_STATE.md
2. Actualizar fecha de última sesión
3. Agregar entrada al historial

---

## Descripción

Script Python que extrae newsletters de Gmail, los clasifica con Groq (Llama 3.3) y los envía a Notion.

---

## Quick Start

```bash
cd ~/Documents/newsletter-digest
source venv/bin/activate
python digest.py --days 7
```

---

## Estructura

| Archivo | Función |
|---------|---------|
| `digest.py` | CLI principal |
| `gmail_client.py` | Conexión Gmail API |
| `summarizer.py` | Clasificación con Groq (batches) |
| `notion_client.py` | Envío a Notion |
| `run_daily.sh` | Script para cron |

---

## Comandos Útiles

```bash
# Procesar newsletters
python digest.py --label "data_science" --days 14 --max 100

# Ver labels disponibles
python digest.py --list-labels

# Solo generar JSON
python digest.py --dry-run

# Ver log del cron
tail -f cron.log
```

---

## Dependencias Clave

- `groq` - Cliente API de Groq
- `google-auth-oauthlib` - OAuth para Gmail
- `notion-client` - Cliente API de Notion

No agregar alternativas (OpenAI, Anthropic, etc.) sin justificación.

---

## Rate Limits

Groq tier gratuito: 12k tokens/minuto.

El script procesa en batches de 10 newsletters con 65 segundos de pausa entre cada batch. No modificar estos valores sin entender el impacto.

---

## Troubleshooting Común

| Problema | Solución |
|----------|----------|
| Token Gmail expirado | `rm token.json` + re-ejecutar |
| Rate limit Groq | Esperar 1 minuto, script maneja automático |
| Duplicados en Notion | Script de limpieza en historial de chat |

---

## Comportamiento del Agente

| Tipo de tarea | Acción |
|---------------|--------|
| Bug en ejecución | Diagnosticar con logs, ejecutar directamente |
| Cambio de provider LLM | Proponer plan, confirmar antes |
| Modificar rate limits | Explicar impacto, confirmar |

**Prohibido:**
- Cambiar credenciales sin confirmar
- Modificar estructura de Notion sin validar
- Agregar dependencias pesadas sin justificación
