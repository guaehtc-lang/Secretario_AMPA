"""Operaciones permitidas sobre Gmail.

Este archivo no contiene ningún método para enviar correos.
"""

import base64
import re
from email.message import EmailMessage

from src import config


class GmailClient:

    def __init__(self, servicio):
        self.servicio = servicio

    def buscar_correos(self, consulta=None, limite=None):
        """Busca correos y devuelve sus identificadores."""

        consulta = consulta or config.GMAIL_QUERY
        limite = limite or config.MAX_EMAILS_PER_RUN

        respuesta = self.servicio.users().messages().list(
            userId="me",
            q=consulta,
            maxResults=limite,
        ).execute()

        return respuesta.get("messages", [])

    def leer_correo(self, message_id):
        """Lee un correo y devuelve sus datos principales."""

        mensaje = self.servicio.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

        payload = mensaje.get("payload", {})
        headers = payload.get("headers", [])

        datos_headers = {
            header["name"].lower(): header["value"]
            for header in headers
        }

        cuerpo = self._extraer_cuerpo(payload)

        return {
            "message_id": mensaje["id"],
            "thread_id": mensaje.get("threadId"),
            "remitente": datos_headers.get("from", ""),
            "destinatario": datos_headers.get("to", ""),
            "cc": datos_headers.get("cc", ""),
            "asunto": datos_headers.get("subject", ""),
            "fecha": datos_headers.get("date", ""),
            "message_id_header": datos_headers.get("message-id", ""),
            "cuerpo": cuerpo[:config.MAX_BODY_CHARS],
            "labels": mensaje.get("labelIds", []),
        }

    def crear_borrador(self, correo_original, asunto, cuerpo, destinatarios):
        """Crea un borrador relacionado con el hilo original."""

        if not config.ALLOW_CREATE_DRAFTS:
            raise PermissionError(
                "La creación de borradores está desactivada en .env"
            )

        if config.GMAIL_ACCESS_MODE != "gestion":
            raise PermissionError(
                "Para crear borradores, GMAIL_ACCESS_MODE debe ser gestion"
            )

        mensaje = EmailMessage()
        mensaje["To"] = ", ".join(destinatarios)
        mensaje["Subject"] = asunto

        message_id_header = correo_original.get(
            "message_id_header",
            "",
        )

        if message_id_header:
            mensaje["In-Reply-To"] = message_id_header
            mensaje["References"] = message_id_header

        mensaje.set_content(cuerpo)

        raw = base64.urlsafe_b64encode(
            mensaje.as_bytes()
        ).decode("utf-8")

        body = {
            "message": {
                "raw": raw,
                "threadId": correo_original.get("thread_id"),
            }
        }

        borrador = self.servicio.users().drafts().create(
            userId="me",
            body=body,
        ).execute()

        return borrador

    def marcar_como_leido(self, message_id):
        """Quita la etiqueta UNREAD del correo."""

        if not config.ALLOW_MODIFY_LABELS:
            raise PermissionError(
                "La modificación de etiquetas está desactivada en .env"
            )

        if config.GMAIL_ACCESS_MODE != "gestion":
            raise PermissionError(
                "Para modificar etiquetas, GMAIL_ACCESS_MODE debe ser gestion"
            )

        return self.servicio.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    def _extraer_cuerpo(self, payload):
        """Extrae el texto del correo, incluyendo mensajes multipart."""

        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data")

        if data and mime_type == "text/plain":
            return self._decodificar(data)

        textos = []

        for parte in payload.get("parts", []):
            texto = self._extraer_cuerpo(parte)

            if texto:
                textos.append(texto)

        if textos:
            return "\n".join(textos)

        if data:
            texto_html = self._decodificar(data)
            return re.sub(r"<[^>]+>", " ", texto_html)

        return ""

    @staticmethod
    def _decodificar(data):
        """Decodifica el contenido base64 utilizado por Gmail."""

        bytes_texto = base64.urlsafe_b64decode(
            data.encode("utf-8")
        )

        return bytes_texto.decode(
            "utf-8",
            errors="replace",
        )
