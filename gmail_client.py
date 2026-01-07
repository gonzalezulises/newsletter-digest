"""
Módulo para conectarse a Gmail y extraer newsletters.
"""

import os
import base64
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import html2text

# Permisos necesarios (solo lectura)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailClient:
    def __init__(self):
        self.service = None
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0

    def authenticate(self):
        """Autenticarse con Gmail usando OAuth2."""
        creds = None

        # Token guardado de sesiones anteriores
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # Si no hay credenciales válidas, iniciar flujo de autenticación
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "No se encontró 'credentials.json'. "
                        "Descárgalo desde Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Guardar credenciales para la próxima vez
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        return self

    def get_label_id(self, label_name: str) -> str | None:
        """Obtener el ID de un label por su nombre."""
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        for label in labels:
            if label['name'].lower() == label_name.lower():
                return label['id']
        return None

    def get_newsletters(self, label_name: str, days_back: int = 7) -> list[dict]:
        """
        Obtener newsletters de un label específico.

        Args:
            label_name: Nombre del label en Gmail
            days_back: Cuántos días hacia atrás buscar

        Returns:
            Lista de diccionarios con subject, from, date, body
        """
        label_id = self.get_label_id(label_name)
        if not label_id:
            raise ValueError(f"Label '{label_name}' no encontrado en Gmail")

        # Calcular fecha límite
        after_date = datetime.now() - timedelta(days=days_back)
        query = f"after:{after_date.strftime('%Y/%m/%d')}"

        # Buscar mensajes
        results = self.service.users().messages().list(
            userId='me',
            labelIds=[label_id],
            q=query,
            maxResults=200
        ).execute()

        messages = results.get('messages', [])
        newsletters = []

        for msg in messages:
            newsletter = self._parse_message(msg['id'])
            if newsletter:
                newsletters.append(newsletter)

        # Ordenar por fecha (más reciente primero)
        newsletters.sort(key=lambda x: x['date'], reverse=True)
        return newsletters

    def _parse_message(self, msg_id: str) -> dict | None:
        """Parsear un mensaje de Gmail."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']

            # Extraer headers
            subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                'Sin asunto'
            )
            sender = next(
                (h['value'] for h in headers if h['name'].lower() == 'from'),
                'Desconocido'
            )
            date_str = next(
                (h['value'] for h in headers if h['name'].lower() == 'date'),
                None
            )

            # Parsear fecha
            date = datetime.now()
            if date_str:
                try:
                    date = parsedate_to_datetime(date_str)
                except:
                    pass

            # Extraer cuerpo del mensaje
            body = self._extract_body(message['payload'])

            return {
                'id': msg_id,
                'subject': subject,
                'from': sender,
                'date': date,
                'body': body[:15000]  # Limitar tamaño
            }
        except Exception as e:
            print(f"Error parseando mensaje {msg_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Extraer el cuerpo del mensaje (preferir HTML, convertir a texto)."""
        body = ""

        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        if 'parts' in payload:
            html_body = None
            text_body = None

            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/html' and part['body'].get('data'):
                    html_body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                elif mime_type == 'text/plain' and part['body'].get('data'):
                    text_body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                elif 'parts' in part:
                    # Mensaje multipart anidado
                    nested = self._extract_body(part)
                    if nested:
                        return nested

            # Preferir HTML convertido a texto
            if html_body:
                body = self.h2t.handle(html_body)
            elif text_body:
                body = text_body

        # Si el body es HTML, convertir
        if body and '<html' in body.lower():
            body = self.h2t.handle(body)

        return body.strip()


def list_labels():
    """Utilidad para listar todos los labels disponibles."""
    client = GmailClient().authenticate()
    results = client.service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    print("\nLabels disponibles en tu Gmail:\n")
    for label in sorted(labels, key=lambda x: x['name']):
        print(f"  - {label['name']}")


if __name__ == '__main__':
    list_labels()
