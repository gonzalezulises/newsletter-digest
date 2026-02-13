"""
Módulo para conectarse a Gmail vía IMAP y extraer newsletters.
Usa App Password en lugar de OAuth2 — no expira.
"""

import email
import imaplib
import os
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime

from dotenv import load_dotenv
import html2text

load_dotenv()

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


class GmailClient:
    def __init__(self):
        self.mail = None
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0

    def authenticate(self):
        """Conectar a Gmail vía IMAP con App Password."""
        email_addr = os.getenv("GMAIL_EMAIL")
        app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not email_addr or not app_password:
            raise ValueError(
                "GMAIL_EMAIL y GMAIL_APP_PASSWORD deben estar configurados.\n"
                "Genera un App Password en: https://myaccount.google.com/apppasswords"
            )

        self.mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        self.mail.login(email_addr, app_password)
        return self

    def get_newsletters(self, label_name: str, days_back: int = 7) -> list[dict]:
        """
        Obtener newsletters de un label específico.

        Args:
            label_name: Nombre del label en Gmail
            days_back: Cuántos días hacia atrás buscar

        Returns:
            Lista de diccionarios con subject, from, date, body
        """
        # Seleccionar la carpeta/label
        status, _ = self.mail.select(f'"{label_name}"', readonly=True)
        if status != "OK":
            raise ValueError(f"Label '{label_name}' no encontrado en Gmail")

        # Buscar mensajes desde la fecha límite
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
        status, data = self.mail.search(None, f'(SINCE {since_date})')
        if status != "OK" or not data[0]:
            return []

        msg_ids = data[0].split()
        newsletters = []

        for msg_id in msg_ids:
            newsletter = self._parse_message(msg_id)
            if newsletter:
                newsletters.append(newsletter)

        # Ordenar por fecha (más reciente primero)
        newsletters.sort(key=lambda x: x["date"], reverse=True)
        return newsletters

    def _decode_header_value(self, value: str) -> str:
        """Decodificar un header que puede tener encoding MIME."""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def _parse_message(self, msg_id: bytes) -> dict | None:
        """Parsear un mensaje IMAP."""
        try:
            # Obtener el mensaje completo y el X-GM-MSGID para el link
            status, data = self.mail.fetch(msg_id, "(RFC822 X-GM-MSGID)")
            if status != "OK":
                return None

            # Extraer Gmail message ID del response
            gmail_id = None
            for part in data:
                if isinstance(part, tuple) and b"X-GM-MSGID" in part[0]:
                    # El formato es: b'1 (X-GM-MSGID 1234567890 RFC822 {size}'
                    token = part[0].decode()
                    for segment in token.split():
                        if segment.isdigit() and len(segment) > 10:
                            gmail_id = format(int(segment), "x")
                            break

            # Parsear el email
            raw_email = None
            for part in data:
                if isinstance(part, tuple) and len(part) == 2 and isinstance(part[1], bytes):
                    raw_email = part[1]
                    break

            if raw_email is None:
                return None

            msg = email.message_from_bytes(raw_email)

            subject = self._decode_header_value(msg.get("Subject", "Sin asunto"))
            sender = self._decode_header_value(msg.get("From", "Desconocido"))
            date_str = msg.get("Date")

            date = datetime.now()
            if date_str:
                try:
                    date = parsedate_to_datetime(date_str)
                except Exception:
                    pass

            body = self._extract_body(msg)

            return {
                "id": gmail_id or msg_id.decode(),
                "subject": subject,
                "from": sender,
                "date": date,
                "body": body[:15000],
            }
        except Exception as e:
            print(f"Error parseando mensaje {msg_id}: {e}")
            return None

    def _extract_body(self, msg: email.message.Message) -> str:
        """Extraer el cuerpo del mensaje (preferir HTML, convertir a texto)."""
        html_body = None
        text_body = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Saltar adjuntos
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                except Exception:
                    continue

                if content_type == "text/html" and html_body is None:
                    html_body = text
                elif content_type == "text/plain" and text_body is None:
                    text_body = text
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                    if msg.get_content_type() == "text/html":
                        html_body = text
                    else:
                        text_body = text
            except Exception:
                pass

        if html_body:
            return self.h2t.handle(html_body).strip()
        if text_body:
            return text_body.strip()
        return ""


def list_labels():
    """Utilidad para listar todos los labels/carpetas disponibles."""
    client = GmailClient().authenticate()
    status, folders = client.mail.list()

    if status != "OK":
        print("Error listando carpetas")
        return

    print("\nLabels disponibles en tu Gmail:\n")
    for folder in sorted(folders):
        # El formato es: b'(\\flags) "/" "nombre"'
        parts = folder.decode().split(' "/" ')
        if len(parts) == 2:
            name = parts[1].strip('"')
            print(f"  - {name}")


if __name__ == "__main__":
    list_labels()
