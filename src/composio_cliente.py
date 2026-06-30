"""Conexión reutilizable con Gmail y Google Calendar."""

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


def crear_cliente_composio():
    """Crea el cliente de Composio."""

    if not COMPOSIO_API_KEY:
        raise ValueError(
            "Falta COMPOSIO_API_KEY en el archivo .env."
        )

    return Composio(
        provider=OpenAIProvider(),
        api_key=COMPOSIO_API_KEY,
    )


@lru_cache(maxsize=1)
def obtener_sesion_google():
    """Crea una sesión directa para Gmail y Calendar."""

    composio = crear_cliente_composio()

    return composio.create(
        user_id=COMPOSIO_USER_ID,
        toolkits=[
            "gmail",
            "googlecalendar",
        ],
        session_preset=SESSION_PRESET_DIRECT_TOOLS,
    )
