"""Carga el prompt editable y prepara los mensajes."""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.parametros import (
    RUTA_PROMPT,
    TIMEZONE,
)


def cargar_prompt():
    """Lee el prompt desde su archivo independiente."""

    return RUTA_PROMPT.read_text(
        encoding="utf-8"
    )


def crear_mensajes():
    """Crea los mensajes iniciales del agente."""

    ahora = datetime.now(
        ZoneInfo(TIMEZONE)
    )

    instrucciones = cargar_prompt()

    instrucciones += (
        "\n\nFECHA Y HORA ACTUAL: "
        + ahora.strftime(
            "%Y-%m-%d %H:%M"
        )
        + f" ({TIMEZONE})"
    )

    return [
        {
            "role": "system",
            "content": instrucciones,
        },
        {
            "role": "user",
            "content": (
                "Revisa el siguiente correo pendiente "
                "del buzón del AMPA y completa las acciones "
                "autorizadas."
            ),
        },
    ]
