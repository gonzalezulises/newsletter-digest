"""
Módulo para enviar newsletters a Notion.
"""

import os
import requests
from datetime import datetime


class NotionClient:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self._existing_titles = None

    def is_configured(self) -> bool:
        """Verificar si Notion está configurado."""
        return bool(self.token and self.database_id)

    def get_existing_titles(self) -> set:
        """Obtener títulos existentes en la base de datos para evitar duplicados."""
        if self._existing_titles is not None:
            return self._existing_titles

        self._existing_titles = set()

        response = requests.post(
            f"{self.base_url}/databases/{self.database_id}/query",
            headers=self.headers,
            json={"page_size": 100}
        )

        if response.status_code == 200:
            results = response.json().get("results", [])
            for page in results:
                title_prop = page.get("properties", {}).get("Título", {})
                title_list = title_prop.get("title", [])
                if title_list:
                    title = title_list[0].get("text", {}).get("content", "")
                    self._existing_titles.add(title.lower().strip())

        return self._existing_titles

    def newsletter_exists(self, titulo: str) -> bool:
        """Verificar si un newsletter ya existe por título."""
        existing = self.get_existing_titles()
        return titulo.lower().strip() in existing

    def clear_database(self) -> int:
        """Eliminar todas las entradas de la base de datos."""
        deleted = 0

        response = requests.post(
            f"{self.base_url}/databases/{self.database_id}/query",
            headers=self.headers,
            json={"page_size": 100}
        )

        if response.status_code == 200:
            results = response.json().get("results", [])
            for page in results:
                page_id = page["id"]
                del_response = requests.patch(
                    f"{self.base_url}/pages/{page_id}",
                    headers=self.headers,
                    json={"archived": True}
                )
                if del_response.status_code == 200:
                    deleted += 1

        # Limpiar cache
        self._existing_titles = None
        return deleted

    def add_newsletter(self, newsletter: dict) -> dict:
        """
        Agregar un newsletter a la base de datos de Notion.

        Args:
            newsletter: Dict con titulo, fuente, fecha, categoria, resumen, tags, link
        """
        # Construir propiedades según el schema de Notion
        properties = {
            "Título": {
                "title": [{"text": {"content": newsletter.get("titulo", "Sin título")}}]
            },
            "Fuente": {
                "rich_text": [{"text": {"content": newsletter.get("fuente", "")}}]
            },
            "Fecha": {
                "date": {"start": newsletter.get("fecha", datetime.now().strftime("%Y-%m-%d"))}
            },
            "Categoría": {
                "select": {"name": newsletter.get("categoria", "Noticia")}
            },
            "Resumen": {
                "rich_text": [{"text": {"content": newsletter.get("resumen", "")[:2000]}}]
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in newsletter.get("tags", [])[:5]]
            }
        }

        # Agregar herramienta si existe
        if newsletter.get("herramienta"):
            properties["Herramienta o librería"] = {
                "rich_text": [{"text": {"content": newsletter.get("herramienta", "")}}]
            }

        # Agregar link si existe
        if newsletter.get("link"):
            properties["Link"] = {
                "url": newsletter.get("link")
            }

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }

        response = requests.post(
            f"{self.base_url}/pages",
            headers=self.headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"    Error Notion: {response.status_code} - {response.text[:200]}")
            return {"error": response.text}

        return response.json()

    def add_newsletters(self, newsletters: list[dict]) -> dict:
        """
        Agregar múltiples newsletters a Notion, evitando duplicados.

        Returns:
            Dict con estadísticas de la operación
        """
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}

        print("  Verificando duplicados...")
        self.get_existing_titles()

        for i, nl in enumerate(newsletters, 1):
            titulo = nl.get('titulo', 'Sin título')

            # Verificar si ya existe
            if self.newsletter_exists(titulo):
                print(f"  ⏭️  Saltando {i}/{len(newsletters)}: {titulo[:40]}... (ya existe)")
                results["skipped"] += 1
                continue

            print(f"  📤 Enviando {i}/{len(newsletters)}: {titulo[:40]}...")

            result = self.add_newsletter(nl)

            if "error" in result:
                results["failed"] += 1
                results["errors"].append(result["error"])
            else:
                results["success"] += 1
                # Agregar a cache para evitar duplicados en el mismo batch
                self._existing_titles.add(titulo.lower().strip())

        return results


def create_notion_database_template():
    """
    Retorna el schema recomendado para crear la base de datos en Notion.
    """
    return """
## Crear base de datos en Notion

1. Abre Notion y crea una nueva página
2. Escribe /database y selecciona "Database - Full page"
3. Configura estas columnas:

| Columna   | Tipo         | Opciones                                            |
|-----------|--------------|-----------------------------------------------------|
| Título    | Title        | (default)                                           |
| Fuente    | Text         |                                                     |
| Fecha     | Date         |                                                     |
| Categoría | Select       | Herramienta, Tutorial, Práctica, Tema, Aplicación   |
| Resumen   | Text         |                                                     |
| Tags      | Multi-select | (se crean automáticamente)                          |
| Link      | URL          |                                                     |

4. Comparte la base de datos con tu integración (ver instrucciones)
"""
