"""Autorización OAuth para acceder a Gmail.

No utiliza ni guarda la contraseña del correo.
La primera vez abre el navegador para que el usuario autorice la cuenta.
"""

import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src import config


SCOPES_LECTURA = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

SCOPES_GESTION = [
    "https://www.googleapis.com/auth/gmail.modify"
]


def obtener_scopes():
    """Devuelve los permisos correspondientes al modo configurado."""

    if config.GMAIL_ACCESS_MODE == "gestion":
        return SCOPES_GESTION

    return SCOPES_LECTURA


def crear_servicio_gmail():
    """Autoriza la cuenta y devuelve el servicio de Gmail."""

    credentials_path = Path(config.GOOGLE_CREDENTIALS_FILE)
    token_path = Path(config.GMAIL_TOKEN_FILE)
    scopes = obtener_scopes()

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"No existe {credentials_path}. "
            "Debes descargar credentials.json desde Google Cloud."
        )

    credenciales = None

    if token_path.exists():
        credenciales = Credentials.from_authorized_user_file(
            str(token_path),
            scopes,
        )

        if not credenciales.has_scopes(scopes):
            raise ValueError(
                "El token actual no tiene los permisos necesarios. "
                "Borra token_gmail.json y vuelve a autorizar la cuenta."
            )

    if not credenciales or not credenciales.valid:

        if (
            credenciales
            and credenciales.expired
            and credenciales.refresh_token
        ):
            credenciales.refresh(Request())

        else:
            flujo = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                scopes,
            )

            credenciales = flujo.run_local_server(port=0)

        token_path.write_text(
            credenciales.to_json(),
            encoding="utf-8",
        )

    servicio = build(
        "gmail",
        "v1",
        credentials=credenciales,
    )

    perfil = servicio.users().getProfile(
        userId="me"
    ).execute()

    correo_autorizado = perfil["emailAddress"].lower()

    if (
        config.EXPECTED_GMAIL_ADDRESS
        and correo_autorizado != config.EXPECTED_GMAIL_ADDRESS
    ):
        raise ValueError(
            "Se ha autorizado una cuenta distinta. "
            f"Esperada: {config.EXPECTED_GMAIL_ADDRESS}. "
            f"Autorizada: {correo_autorizado}."
        )

    return servicio, perfil
