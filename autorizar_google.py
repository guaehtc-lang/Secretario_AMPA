"""Autoriza Gmail y Google Calendar en Composio."""

from composio import SESSION_PRESET_DIRECT_TOOLS

from src.composio_cliente import crear_cliente_composio
from src.parametros import COMPOSIO_USER_ID


TOOLKITS = [
    "gmail",
    "googlecalendar",
]

HERRAMIENTAS = {
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


composio = crear_cliente_composio()

sesion = composio.create(
    user_id=COMPOSIO_USER_ID,
    toolkits=TOOLKITS,
    tools=HERRAMIENTAS,
    session_preset=SESSION_PRESET_DIRECT_TOOLS,
)


for toolkit in TOOLKITS:

    cuentas = composio.connected_accounts.list(
        user_ids=[COMPOSIO_USER_ID],
        toolkit_slugs=[toolkit],
        statuses=["ACTIVE"],
    )

    if cuentas.items:
        print(
            toolkit,
            "ya está conectado.",
        )
        continue

    solicitud = sesion.authorize(
        toolkit
    )

    print(
        "\nAutoriza",
        toolkit,
        "en este enlace:",
    )
    print(
        solicitud.redirect_url
    )

    solicitud.wait_for_connection(
        timeout=300
    )

    print(
        toolkit,
        "conectado correctamente.",
    )
