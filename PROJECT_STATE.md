# PROJECT_STATE.md - newsletter-digest

> **Propósito**: Contrato de continuidad entre sesiones de Claude Code.
> **Regla**: Leer al inicio de cada sesión. Actualizar antes de terminar.

---

## Estado Actual

| Campo | Valor |
|-------|-------|
| Última sesión | 2026-01-07 |
| Estado general | 🟢 Funcional |
| Cron | Activo (6pm diario) |
| LLM Provider | Groq (Llama 3.3 70B) |

---

## Descripción

Script que extrae newsletters de Gmail, los clasifica con IA y los envía a una base de datos de Notion.

**Flujo:**
```
Gmail (label: data_science) → Groq (clasificación) → Notion (base de datos)
```

---

## En Progreso

No hay tareas activas. Sistema funcionando en producción.

---

## Completado Recientemente

| Fecha | Tarea | Detalles |
|-------|-------|----------|
| 2026-01-07 | Migración LM Studio → Groq | `summarizer.py` reescrito |
| 2026-01-07 | Procesamiento en batches | 10 newsletters/batch, 65s pausa |
| 2026-01-07 | Re-autenticación Gmail | Token expirado, regenerado |
| 2026-01-07 | Limpieza duplicados Notion | 86 duplicados eliminados |
| 2026-01-07 | Procesamiento 75 newsletters | Backlog de 14 días procesado |

---

## Arquitectura

```
newsletter-digest/
├── digest.py           # Script principal (CLI)
├── gmail_client.py     # Conexión Gmail API
├── summarizer.py       # Clasificación con Groq
├── notion_client.py    # Envío a Notion API
├── credentials.json    # OAuth Google (no commitear)
├── token.json          # Token Gmail (se regenera)
├── .env                # API keys (no commitear)
└── run_daily.sh        # Script para cron
```

---

## Integraciones

| Servicio | Estado | Notas |
|----------|--------|-------|
| Gmail API | ✅ | OAuth, label `data_science` |
| Groq API | ✅ | Llama 3.3 70B, tier gratuito |
| Notion API | ✅ | Base de datos con 762 registros |

---

## Variables de Entorno

```bash
# Groq (clasificación)
GROQ_API_KEY=gsk_xxx

# Gmail
GMAIL_LABEL=data_science
DAYS_BACK=7

# Notion
NOTION_TOKEN=ntn_xxx
NOTION_DATABASE_ID=xxx
```

---

## Rate Limits

| Servicio | Límite | Manejo |
|----------|--------|--------|
| Groq (free tier) | 12k tokens/min | Batches de 10 + 65s pausa |
| Gmail API | 250 quota units/user/sec | Sin issues |
| Notion API | 3 req/sec | Sin issues |

---

## Cron Job

```bash
# Ejecuta diariamente a las 6pm
0 18 * * * /bin/bash /Users/ulisesgonzalez/Documents/newsletter-digest/run_daily.sh >> /Users/ulisesgonzalez/Documents/newsletter-digest/cron.log 2>&1
```

---

## Comandos Frecuentes

```bash
# Activar entorno
cd ~/Documents/newsletter-digest
source venv/bin/activate

# Ejecutar manualmente
python digest.py --days 7 --max 50

# Ver labels de Gmail
python digest.py --list-labels

# Dry run (sin enviar a Notion)
python digest.py --dry-run

# Ver log del cron
tail -100 cron.log
```

---

## Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `RefreshError: Token expired` | Token Gmail expiró | Eliminar `token.json`, re-ejecutar |
| `429 rate_limit_exceeded` | Límite Groq | Script maneja automático con batches |
| `GROQ_API_KEY no configurada` | Falta variable | Agregar a `.env` |

---

## Deuda Técnica

| Issue | Impacto | Razón de posponer |
|-------|---------|-------------------|
| Tests unitarios | Bajo | Script simple, validación manual suficiente |
| Retry automático en errores | Bajo | Errores raros, cron re-ejecuta al día siguiente |
| Logging estructurado | Bajo | `cron.log` suficiente por ahora |

---

## Notas para Próxima Sesión

```
- El token de Gmail puede expirar cada ~7 días si no se usa. Si falla, eliminar token.json.
- Groq tier gratuito es suficiente para uso diario (~10-20 newsletters).
- Si se necesita procesar más de 100 newsletters, considerar upgrade a Groq Dev Tier.
- La base de datos de Notion tiene ~762 registros únicos.
```

---

## Historial de Sesiones

| Fecha | Resumen |
|-------|---------|
| 2026-01-07 | Migración a Groq, fix Gmail token, limpieza duplicados |
| 2025-12-24 | Última ejecución exitosa con LM Studio |
| 2025-12-22 | Setup inicial del proyecto |
