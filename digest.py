#!/usr/bin/env python3
"""
Newsletter Digest Generator

Extrae newsletters de Gmail, los clasifica con LM Studio y los envía a Notion.

Uso:
    python digest.py                    # Procesar y enviar a Notion
    python digest.py --dry-run          # Solo generar JSON, no enviar
    python digest.py --label "News"     # Especificar label
    python digest.py --days 14          # Últimos 14 días
    python digest.py --list-labels      # Listar labels disponibles
    python digest.py --setup-notion     # Ver instrucciones de Notion
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description='Genera un digest de newsletters y lo envía a Notion'
    )
    parser.add_argument(
        '--label', '-l',
        default=os.getenv('GMAIL_LABEL', 'Newsletters'),
        help='Label de Gmail donde están los newsletters'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=int(os.getenv('DAYS_BACK', '7')),
        help='Días hacia atrás para buscar (default: 7)'
    )
    parser.add_argument(
        '--max', '-m',
        type=int,
        default=10,
        help='Máximo de newsletters a procesar (default: 10)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Archivo JSON de salida (opcional)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo generar JSON, no enviar a Notion'
    )
    parser.add_argument(
        '--list-labels',
        action='store_true',
        help='Listar labels disponibles en Gmail'
    )
    parser.add_argument(
        '--setup-notion',
        action='store_true',
        help='Mostrar instrucciones para configurar Notion'
    )

    args = parser.parse_args()

    # Mostrar instrucciones de Notion
    if args.setup_notion:
        from notion_client import create_notion_database_template
        print(create_notion_database_template())
        print("\n## Configurar integración\n")
        print("1. Ve a https://www.notion.so/my-integrations")
        print("2. Click 'New integration'")
        print("3. Nombre: 'Newsletter Digest'")
        print("4. Copia el 'Internal Integration Token'")
        print("5. En tu base de datos, click '...' > 'Connections' > Agrega tu integración")
        print("6. Copia el ID de la base de datos de la URL:")
        print("   https://notion.so/TU_DATABASE_ID?v=...")
        print("\n7. Agrega a tu .env:")
        print("   NOTION_TOKEN=secret_xxx")
        print("   NOTION_DATABASE_ID=xxx")
        return

    from gmail_client import GmailClient, list_labels
    from summarizer import NewsletterSummarizer
    from notion_client import NotionClient

    # Listar labels
    if args.list_labels:
        list_labels()
        return

    print(f"\n📬 Newsletter Digest Generator")
    print(f"=" * 40)
    print(f"Label: {args.label}")
    print(f"Período: últimos {args.days} días")
    print(f"Máximo: {args.max} newsletters")
    print()

    # Conectar a Gmail
    print("🔐 Conectando a Gmail...")
    try:
        gmail = GmailClient().authenticate()
    except (ValueError, Exception) as e:
        print(f"\nError: {e}")
        sys.exit(1)

    # Obtener newsletters
    print(f"📥 Buscando newsletters en '{args.label}'...")
    try:
        newsletters = gmail.get_newsletters(args.label, args.days)
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nUsa --list-labels para ver los labels disponibles")
        sys.exit(1)

    if not newsletters:
        print(f"\nNo se encontraron newsletters en los últimos {args.days} días")
        return

    print(f"✅ Encontrados {len(newsletters)} newsletters\n")

    # Generar resúmenes con Groq
    print("🤖 Clasificando con Groq...")
    summarizer = NewsletterSummarizer()
    result = summarizer.generate_digest(newsletters, max_newsletters=args.max)

    if "error" in result:
        print(f"\n❌ Error procesando: {result['error']}")
        if "raw" in result:
            print(f"Respuesta raw guardada en digest_error.txt")
            Path("digest_error.txt").write_text(result["raw"])
        return

    processed = result.get("newsletters", [])
    print(f"✅ Procesados {len(processed)} newsletters\n")

    # Guardar JSON si se especifica
    output_file = args.output or f"digest_{datetime.now().strftime('%Y-%m-%d')}.json"
    Path(output_file).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"📄 JSON guardado: {output_file}")

    # Enviar a Notion
    if args.dry_run:
        print("\n🔍 Dry run - No se envió a Notion")
        print("\nPreview:")
        for nl in processed[:3]:
            print(f"  - [{nl.get('categoria')}] {nl.get('titulo')}")
        if len(processed) > 3:
            print(f"  ... y {len(processed) - 3} más")
        return

    # Verificar configuración de Notion
    notion = NotionClient()
    if not notion.is_configured():
        print("\n⚠️  Notion no configurado")
        print("Ejecuta: python digest.py --setup-notion")
        print("O usa --dry-run para solo generar el JSON")
        return

    print("\n📤 Enviando a Notion...")
    stats = notion.add_newsletters(processed)

    print(f"\n✨ Completado!")
    print(f"   ✅ Enviados: {stats['success']}")
    print(f"   ⏭️  Saltados: {stats.get('skipped', 0)} (duplicados)")
    print(f"   ❌ Fallidos: {stats['failed']}")

    if stats['errors']:
        print("\n   Errores:")
        for err in stats['errors'][:3]:
            print(f"   - {err[:100]}")


if __name__ == '__main__':
    main()
