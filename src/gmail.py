"""Funciones directas de Gmail."""

from src.composio_cliente import obtener_sesion_google
from src.memoria import obtener_ids_procesados
from src.parametros import (
    ALLOW_CREATE_DRAFTS,
    ALLOW_MARK_AS_READ,
    GMAIL_MARK_READ_ACTION,
    GMAIL_QUERY,
    MAX_EMAILS_PER_RUN,
)
from src.utilidades import (
    buscar_ids,
    buscar_valor,
    convertir_resultado,
    extraer_email,
    limpiar_texto,
    obtener_cabecera,
    resultado_tiene_error,
    timestamp_fecha,
)


def preparar_correo(resultado):
    """Reduce una respuesta de Gmail a los campos necesarios."""

    respuesta = convertir_resultado(resultado)
    datos = respuesta.get("data", respuesta)
    payload = datos.get("payload", {})
    headers = payload.get("headers", [])

    cuerpo = (
        datos.get("messageText")
        or datos.get("snippet")
        or ""
    )

    return {
        "message_id": (
            datos.get("messageId")
            or datos.get("id")
            or ""
        ),
        "thread_id": (
            datos.get("threadId")
            or datos.get("thread_id")
            or ""
        ),
        "remitente": obtener_cabecera(
            headers,
            "From",
        ),
        "destinatario": obtener_cabecera(
            headers,
            "To",
        ),
        "fecha": obtener_cabecera(
            headers,
            "Date",
        ),
        "asunto": obtener_cabecera(
            headers,
            "Subject",
        ),
        "cuerpo": limpiar_texto(cuerpo)[:6000],
        "labels": datos.get("labelIds", []),
    }


def obtener_correo_por_id(message_id):
    """Lee un correo concreto."""

    sesion = obtener_sesion_google()

    resultado = sesion.execute(
        "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
        arguments={
            "format": "full",
            "message_id": message_id,
            "user_id": "me",
        },
    )

    correo = preparar_correo(resultado)
    correo["message_id"] = (
        correo["message_id"] or message_id
    )

    return correo


def obtener_correos_no_leidos():
    """Obtiene correos no leídos, del más antiguo al más reciente."""

    sesion = obtener_sesion_google()

    listado = sesion.execute(
        "GMAIL_FETCH_EMAILS",
        arguments={
            "ids_only": True,
            "include_payload": False,
            "include_spam_trash": False,
            "label_ids": ["INBOX", "UNREAD"],
            "max_results": MAX_EMAILS_PER_RUN,
            "page_token": "",
            "query": GMAIL_QUERY,
            "user_id": "me",
            "verbose": False,
        },
    )

    ids = buscar_ids(
        convertir_resultado(listado)
    )

    procesados = set(
        obtener_ids_procesados()
    )

    correos = []

    for message_id in ids:
        if message_id in procesados:
            continue

        correo = obtener_correo_por_id(message_id)
        correo["_orden"] = timestamp_fecha(
            correo["fecha"]
        )
        correos.append(correo)

    correos.sort(
        key=lambda correo: correo["_orden"]
    )

    for correo in correos:
        correo.pop("_orden", None)

    return correos


def crear_borrador(message_id, asunto, cuerpo):
    """Crea un borrador de respuesta. Nunca lo envía."""

    if not ALLOW_CREATE_DRAFTS:
        return {
            "ok": False,
            "estado": "borradores_desactivados",
        }

    if not cuerpo.strip():
        return {
            "ok": False,
            "estado": "cuerpo_vacio",
        }

    correo = obtener_correo_por_id(message_id)
    destinatario = extraer_email(
        correo["remitente"]
    )

    if not destinatario:
        return {
            "ok": False,
            "estado": "sin_destinatario",
        }

    argumentos = {
        "recipient_email": destinatario,
        "extra_recipients": [],
        "cc": [],
        "bcc": [],
        "body": limpiar_texto(cuerpo),
        "is_html": False,
        "user_id": "me",
    }

    if correo["thread_id"]:
        argumentos["thread_id"] = correo["thread_id"]
        argumentos["subject"] = ""
    else:
        argumentos["subject"] = asunto

    sesion = obtener_sesion_google()

    resultado = convertir_resultado(
        sesion.execute(
            "GMAIL_CREATE_EMAIL_DRAFT",
            arguments=argumentos,
        )
    )

    if resultado_tiene_error(resultado):
        return {
            "ok": False,
            "estado": "error_creando_borrador",
            "resultado": resultado,
        }

    draft_id = buscar_valor(
        resultado,
        ["draft_id", "draftId", "id"],
    )

    return {
        "ok": True,
        "estado": "borrador_creado",
        "draft_id": draft_id or "",
        "destinatario": destinatario,
    }


def _nombres_tools_sesion(sesion):
    """Obtiene nombres de tools disponibles cuando la sesión los expone."""

    nombres = []
    herramientas = getattr(sesion, "tools", [])

    for tool in herramientas or []:
        if not isinstance(tool, dict):
            continue

        nombre = tool.get("name")

        if not nombre:
            nombre = tool.get(
                "function",
                {},
            ).get("name")

        if nombre:
            nombres.append(nombre)

    return nombres


def marcar_como_leido(message_id):
    """Quita la etiqueta UNREAD después de procesar el correo."""

    if not ALLOW_MARK_AS_READ:
        return {
            "ok": False,
            "estado": "cambio_estado_desactivado",
        }

    sesion = obtener_sesion_google()
    nombres_disponibles = _nombres_tools_sesion(
        sesion
    )

    candidatos = [GMAIL_MARK_READ_ACTION]

    for nombre in nombres_disponibles:
        texto = nombre.upper()
        if (
            "GMAIL" in texto
            and "MODIFY" in texto
            and "LABEL" in texto
            and "BATCH" not in texto
            and "THREAD" not in texto
        ):
            candidatos.insert(0, nombre)

    candidatos += [
        "GMAIL_MODIFY_EMAIL_LABELS",
        "GMAIL_MODIFY_EMAIL",
    ]
    candidatos = list(dict.fromkeys(candidatos))

    argumentos_posibles = [
        {
            "message_id": message_id,
            "add_label_ids": [],
            "remove_label_ids": ["UNREAD"],
            "user_id": "me",
        },
        {
            "message_id": message_id,
            "add_labels": [],
            "remove_labels": ["UNREAD"],
            "user_id": "me",
        },
        {
            "message_id": message_id,
            "label_ids_to_add": [],
            "label_ids_to_remove": ["UNREAD"],
            "user_id": "me",
        },
    ]

    errores = []

    for nombre in candidatos:
        for argumentos in argumentos_posibles:
            try:
                resultado = convertir_resultado(
                    sesion.execute(
                        nombre,
                        arguments=argumentos,
                    )
                )

                if resultado_tiene_error(resultado):
                    errores.append({
                        "tool": nombre,
                        "resultado": resultado,
                    })
                    continue

                return {
                    "ok": True,
                    "estado": "correo_marcado_leido",
                    "tool": nombre,
                }

            except Exception as error:
                errores.append({
                    "tool": nombre,
                    "error": str(error),
                })

    return {
        "ok": False,
        "estado": "no_se_pudo_marcar_leido",
        "errores": errores[-5:],
    }
