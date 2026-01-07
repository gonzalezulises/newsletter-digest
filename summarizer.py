"""
Módulo para generar resúmenes estructurados usando Groq (Llama 3).
Genera JSON listo para Notion.

Groq es gratis y muy rápido. Obtén tu API key en: https://console.groq.com/keys
"""

import json
import os
import time

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """Clasifica newsletters de data science.

Para CADA newsletter extrae:

1. **titulo**: Asunto limpio
2. **fuente**: Remitente
3. **categoria**: Herramienta | Tutorial | Noticia
4. **herramienta**: Si es categoría Herramienta, nombre de la herramienta/librería. Si no, null.
5. **resumen**: 1-2 oraciones en español. IMPORTANTE: Menciona las librerías de Python utilizadas si las hay (ej: pandas, pyspark, scikit-learn, pytorch, langchain, etc.)
6. **tags**: 2 tags:
   - Tipo: tutorial, herramienta, noticia
   - Campo: machine-learning, deep-learning, nlp, computer-vision, time-series, recommender-systems, reinforcement-learning, causal-inference, statistical-modeling, data-engineering, mlops, analytics-bi, feature-engineering, optimization, bayesian-methods, generative-ai, llm, rag-systems

JSON:
{"newsletters":[{"titulo":"...","fuente":"...","categoria":"...","herramienta":"...","resumen":"...","tags":["tipo","campo"]}]}

Solo JSON."""

# Tamaño de batch para respetar límites de Groq (12k tokens/min en tier gratuito)
BATCH_SIZE = 10
BATCH_DELAY_SECONDS = 65  # Esperar 65s entre batches para reset de rate limit


class NewsletterSummarizer:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY no configurada en .env\n"
                "Obtén tu API key gratis en: https://console.groq.com/keys"
            )

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def _process_batch(self, newsletters: list[dict], batch_offset: int) -> list[dict]:
        """Procesa un batch de newsletters y retorna la lista de resultados."""

        # Guardar metadata original (fecha, link a Gmail)
        metadata = {}
        for i, nl in enumerate(newsletters, 1):
            metadata[i] = {
                "fecha": nl['date'].strftime('%Y-%m-%d'),
                "gmail_link": f"https://mail.google.com/mail/u/0/#inbox/{nl['id']}"
            }

        # Preparar contenido de cada newsletter
        newsletter_texts = []
        for i, nl in enumerate(newsletters, 1):
            body = nl['body'][:800] if nl['body'] else "Sin contenido"
            newsletter_texts.append(f"""
---
Newsletter {i}:
Asunto: {nl['subject']}
De: {nl['from']}
Contenido:
{body}
""")

        all_newsletters = "\n".join(newsletter_texts)

        user_prompt = f"""Analiza estos {len(newsletters)} newsletters y genera el JSON estructurado:

{all_newsletters}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        content = response.choices[0].message.content.strip()

        # Limpiar y parsear JSON
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        try:
            data = json.loads(content)
            results = data.get("newsletters", [])

            # Agregar fecha real y link de Gmail a cada newsletter
            for i, nl in enumerate(results, 1):
                if i in metadata:
                    nl["fecha"] = metadata[i]["fecha"]
                    if not nl.get("link"):
                        nl["link"] = metadata[i]["gmail_link"]

            return results
        except json.JSONDecodeError as e:
            print(f"    ⚠️  Error parseando JSON del batch: {e}")
            return []

    def generate_digest(self, newsletters: list[dict], max_newsletters: int = 10) -> dict:
        """
        Generar digest estructurado en JSON.
        Procesa en batches para respetar límites de rate de Groq.
        """
        if not newsletters:
            return {"newsletters": []}

        newsletters = newsletters[:max_newsletters]
        total = len(newsletters)
        all_results = []

        # Calcular número de batches
        num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(num_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total)
            batch = newsletters[start_idx:end_idx]

            print(f"  📦 Batch {batch_num + 1}/{num_batches} ({start_idx + 1}-{end_idx} de {total})")
            print(f"     Enviando a Groq (Llama 3.3)...")

            try:
                results = self._process_batch(batch, start_idx)
                all_results.extend(results)
                print(f"     ✅ {len(results)} procesados")
            except Exception as e:
                print(f"     ❌ Error en batch: {e}")

            # Esperar entre batches (excepto el último)
            if batch_num < num_batches - 1:
                print(f"     ⏳ Esperando {BATCH_DELAY_SECONDS}s (rate limit)...")
                time.sleep(BATCH_DELAY_SECONDS)

        return {"newsletters": all_results}
