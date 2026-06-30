"""Conexión única con Gmail y Google Calendar mediante Composio."""

from functools import lru_cache

from composio import (
    Composio,
    SESSION_PRESET_DIRECT_TOOLS,
)
from composio_openai import OpenAIProvider

from src.parametros import (
    COMPOSIO_API_KEY,
    COMPOSIO_USER_ID,
)


HERRAMIENTAS_COMPOSIO = {
    "gmail": {
        "enable": [
            "GMAIL_GET_PROFILE",
            "GMAIL_FETCH_EMAILS",
            "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
            "GMAIL_FETCH_MESSAGE_BY_THREAD_ID",
            "GMAIL_CREATE_EMAIL_DRAFT",
        ]
    },
    "googlecalendar": {
        "enable": [
            "GOOGLECALENDAR_FIND_FREE_SLOTS",
            "GOOGLECALENDAR_CREATE_EVENT",
        ]
    },
}


def crear_cliente_composio():
    """Crea el cliente de Composio."""

    if not COMPOSIO_API_KEY:
        raise ValueError(
            "Falta COMPOSIO_API_KEY en .env."
        )

    return Composio(
        provider=OpenAIProvider(),
        api_key=COMPOSIO_API_KEY,
    )


@lru_cache(maxsize=1)
def obtener_sesion_google():
    """Devuelve una sesión reutilizable y limitada."""

    composio = crear_cliente_composio()

    return composio.create(
        user_id=COMPOSIO_USER_ID,
        toolkits=[
            "gmail",
            "googlecalendar",
        ],
        tools=HERRAMIENTAS_COMPOSIO,
        session_preset=SESSION_PRESET_DIRECT_TOOLS,
    )
