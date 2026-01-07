# Newsletter Digest Generator

Script que extrae newsletters de Gmail, los clasifica con **Groq (Llama 3.3)** y los envía a Notion.

## Configuración Rápida

### 1. Instalar dependencias

```bash
cd newsletter-digest
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Groq API (GRATIS)

1. Ve a [Groq Console](https://console.groq.com/keys)
2. Crea una cuenta (o usa Google login)
3. Click en "Create API Key"
4. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
5. Edita `.env` y pega tu API key en `GROQ_API_KEY`

### 3. Configurar Gmail API (una sola vez)

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo (o usa uno existente)
3. Habilita **Gmail API**:
   - Ve a "APIs & Services" > "Library"
   - Busca "Gmail API" y habilítala
4. Configura pantalla de consentimiento OAuth:
   - Ve a "APIs & Services" > "OAuth consent screen"
   - Selecciona "External"
   - Llena los campos requeridos (nombre de app, email)
   - En "Scopes", agrega `.../auth/gmail.readonly`
   - En "Test users", agrega tu email
5. Crea credenciales:
   - Ve a "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Selecciona "Desktop app"
   - Descarga el JSON
6. Renombra el archivo descargado a `credentials.json` y ponlo en esta carpeta

### 4. Configurar Notion (opcional)

1. Ve a [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Nombre: "Newsletter Digest"
4. Copia el "Internal Integration Token"
5. Crea una base de datos en Notion con estas propiedades:
   - `Título` (title)
   - `Fuente` (select)
   - `Categoría` (select: Herramienta, Tutorial, Noticia)
   - `Herramienta` (text)
   - `Resumen` (text)
   - `Tags` (multi-select)
   - `Fecha` (date)
   - `Link` (url)
6. Comparte la base de datos con tu integración
7. Agrega a tu `.env`:
   ```
   NOTION_TOKEN=secret_xxx
   NOTION_DATABASE_ID=xxx
   ```

### 5. Crear un label en Gmail

1. En Gmail, crea un label llamado "data_science" (o el nombre que prefieras)
2. Mueve tus newsletters a ese label, o crea filtros automáticos

## Uso

```bash
# Generar digest de los últimos 7 días (máximo 10)
python digest.py

# Procesar más newsletters
python digest.py --max 50

# Especificar label diferente
python digest.py --label "Suscripciones"

# Cambiar período de búsqueda
python digest.py --days 14

# Ver labels disponibles
python digest.py --list-labels

# Solo generar JSON, no enviar a Notion
python digest.py --dry-run
```

## Primera ejecución

La primera vez que ejecutes el script:
1. Se abrirá tu navegador para autenticarte con Google
2. Autoriza los permisos de lectura
3. Se guardará un `token.json` para futuras ejecuciones

## Estructura del proyecto

```
newsletter-digest/
├── credentials.json    # Credenciales de Google (tú lo agregas)
├── token.json          # Token de sesión (se genera automáticamente)
├── .env                # Variables de entorno (tú lo creas)
├── .env.example        # Ejemplo de configuración
├── requirements.txt    # Dependencias
├── digest.py           # Script principal
├── gmail_client.py     # Módulo de conexión a Gmail
├── summarizer.py       # Módulo de clasificación con Groq
├── notion_client.py    # Módulo de envío a Notion
└── README.md
```

## Automatización (cron)

Para ejecutar automáticamente cada día a las 6pm:

```bash
crontab -e
```

Agregar:
```
0 18 * * * /bin/bash /ruta/a/newsletter-digest/run_daily.sh >> /ruta/a/newsletter-digest/cron.log 2>&1
```

## Rate Limits

Groq tiene un límite de 12,000 tokens/minuto en el tier gratuito. El script procesa automáticamente en batches de 10 newsletters con pausas de 65 segundos entre cada batch.

Para 75 newsletters, el tiempo total es aproximadamente 9 minutos.

## Costos

- **Gmail API**: Gratis
- **Groq API**: Gratis (30 req/min, 14,400 req/día con Llama 3.3)
- **Notion API**: Gratis

## Troubleshooting

### Token de Gmail expirado
```
RefreshError: Token has been expired or revoked.
```
Solución: Elimina `token.json` y ejecuta el script de nuevo para re-autenticarte.

### Rate limit de Groq
```
Error code: 429 - rate_limit_exceeded
```
Solución: El script ya maneja esto automáticamente con batches. Si persiste, espera 1 minuto y vuelve a intentar.
