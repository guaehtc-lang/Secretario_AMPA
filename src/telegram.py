"""Envío y recepción de autorizaciones mediante Telegram."""

import hashlib
import json

import requests

from src.memoria import (
    obtener_alerta,
    registrar_alerta,
)
from src.parametros import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ENABLED,
    TELEGRAM_POLLING_TIMEOUT,
    TELEGRAM_REQUEST_TIMEOUT,
)


def _url(
    metodo,
):
    """Construye una URL de Telegram Bot API."""

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "Falta TELEGRAM_BOT_TOKEN en .env."
        )

    return (
        "https://api.telegram.org/bot"
        + TELEGRAM_BOT_TOKEN
        + "/"
        + metodo
    )


def _peticion(
    metodo,
    datos=None,
):
    """Ejecuta una petición y normaliza la respuesta."""

    if not TELEGRAM_ENABLED:
        return {
            "ok": False,
            "estado": "telegram_desactivado",
        }

    try:
        respuesta = requests.post(
            _url(
                metodo
            ),
            json=datos or {},
            timeout=TELEGRAM_REQUEST_TIMEOUT,
        )

        contenido = respuesta.json()

    except Exception as error:
        return {
            "ok": False,
            "estado": "error_telegram",
            "error": str(
                error
            ),
        }

    if not respuesta.ok:
        return {
            "ok": False,
            "estado": "error_http_telegram",
            "codigo_http": respuesta.status_code,
            "resultado": contenido,
        }

    if not contenido.get(
        "ok"
    ):
        return {
            "ok": False,
            "estado": "telegram_rechazo_peticion",
            "resultado": contenido,
        }

    return {
        "ok": True,
        "estado": "telegram_ok",
        "resultado": contenido.get(
            "result"
        ),
    }


def crear_codigo_alerta(
    message_id,
):
    """Crea un código breve asociado al correo."""

    codigo = hashlib.sha1(
        message_id.encode(
            "utf-8"
        )
    ).hexdigest()[
        :6
    ].upper()

    return "URG-" + codigo


def enviar_mensaje(
    texto,
    botones=None,
):
    """Envía un mensaje al chat autorizado."""

    if not TELEGRAM_CHAT_ID:
        return {
            "ok": False,
            "estado": "telegram_chat_id_vacio",
        }

    datos = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
    }

    if botones:
        datos[
            "reply_markup"
        ] = {
            "inline_keyboard": botones,
        }

    respuesta = _peticion(
        "sendMessage",
        datos,
    )

    if not respuesta.get(
        "ok"
    ):
        return respuesta

    resultado = respuesta.get(
        "resultado",
        {},
    )

    return {
        "ok": True,
        "estado": "mensaje_telegram_enviado",
        "message_id": resultado.get(
            "message_id",
            "",
        ),
        "chat_id": (
            resultado.get(
                "chat",
                {},
            ).get(
                "id",
                "",
            )
        ),
    }


def enviar_alerta_telegram(
    message_id,
    resumen,
    tipo_riesgo,
    draft_id,
    asunto_borrador,
    cuerpo_borrador,
):
    """Envía la alerta inicial y guarda el flujo pendiente."""

    alerta_existente = obtener_alerta(
        message_id
    )

    if alerta_existente:
        return {
            "ok": True,
            "estado": "alerta_ya_registrada",
            "duplicada": True,
            "codigo": (
                alerta_existente[
                    "resultado"
                ].get(
                    "codigo",
                    "",
                )
            ),
        }

    codigo = crear_codigo_alerta(
        message_id
    )

    texto = (
        "🚨 URGENCIA AMPA · "
        + codigo
        + "\n\n"
        + resumen
        + "\n\n"
        + "Se ha creado un borrador de respuesta."
    )

    botones = [
        [
            {
                "text": "Ver borrador",
                "callback_data": (
                    "ver:"
                    + codigo
                ),
            },
            {
                "text": "Dejar pendiente",
                "callback_data": (
                    "pendiente:"
                    + codigo
                ),
            },
        ]
    ]

    enviado = enviar_mensaje(
        texto,
        botones,
    )

    if not enviado.get(
        "ok"
    ):
        return enviado

    resultado = {
        "estado": (
            "esperando_revision_borrador"
        ),
        "codigo": codigo,
        "draft_id": draft_id,
        "asunto_borrador": asunto_borrador,
        "cuerpo_borrador": cuerpo_borrador,
        "telegram_alerta": enviado,
    }

    registrar_alerta(
        message_id=message_id,
        tipo_riesgo=tipo_riesgo,
        resumen=resumen,
        modo="telegram",
        resultado=resultado,
    )

    return {
        "ok": True,
        "estado": "alerta_telegram_enviada",
        "codigo": codigo,
        "duplicada": False,
        "telegram": enviado,
    }


def enviar_borrador_telegram(
    alerta,
):
    """Envía el borrador y muestra la autorización final."""

    datos = alerta.get(
        "resultado",
        {},
    )
    codigo = datos.get(
        "codigo",
        "",
    )
    asunto = datos.get(
        "asunto_borrador",
        "",
    )
    cuerpo = datos.get(
        "cuerpo_borrador",
        "",
    )

    texto = (
        "BORRADOR DE RESPUESTA · "
        + codigo
        + "\n\n"
        + "Asunto: "
        + asunto
        + "\n\n"
        + cuerpo
        + "\n\n"
        + "¿Autorizas el envío de este correo?"
    )

    botones = [
        [
            {
                "text": "Enviar correo",
                "callback_data": (
                    "enviar:"
                    + codigo
                ),
            },
            {
                "text": "No enviar",
                "callback_data": (
                    "no:"
                    + codigo
                ),
            },
        ]
    ]

    return enviar_mensaje(
        texto,
        botones,
    )


def enviar_confirmacion_telegram(
    codigo,
    texto,
):
    """Envía el resultado de una decisión."""

    return enviar_mensaje(
        codigo
        + "\n"
        + texto
    )


def obtener_actualizaciones(
    offset=0,
):
    """Obtiene mensajes y pulsaciones pendientes."""

    datos = {
        "offset": int(
            offset
            or 0
        ),
        "timeout": max(
            0,
            TELEGRAM_POLLING_TIMEOUT,
        ),
        "allowed_updates": [
            "callback_query",
        ],
    }

    respuesta = _peticion(
        "getUpdates",
        datos,
    )

    if not respuesta.get(
        "ok"
    ):
        return {
            **respuesta,
            "actualizaciones": [],
        }

    return {
        "ok": True,
        "estado": "actualizaciones_consultadas",
        "actualizaciones": (
            respuesta.get(
                "resultado"
            )
            or []
        ),
    }


def responder_callback(
    callback_query_id,
    texto="",
):
    """Cierra el indicador de carga del botón."""

    return _peticion(
        "answerCallbackQuery",
        {
            "callback_query_id": (
                callback_query_id
            ),
            "text": texto,
        },
    )


def retirar_botones(
    chat_id,
    message_id,
):
    """Retira los botones del mensaje ya procesado."""

    if not chat_id or not message_id:
        return {
            "ok": False,
            "estado": "mensaje_telegram_incompleto",
        }

    return _peticion(
        "editMessageReplyMarkup",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {
                "inline_keyboard": [],
            },
        },
    )


def callback_autorizado(
    actualizacion,
):
    """Comprueba que el botón procede del chat configurado."""

    callback = actualizacion.get(
        "callback_query",
        {},
    )

    chat_id = (
        callback.get(
            "message",
            {},
        )
        .get(
            "chat",
            {},
        )
        .get(
            "id"
        )
    )

    return str(
        chat_id
    ) == str(
        TELEGRAM_CHAT_ID
    )


def datos_callback(
    actualizacion,
):
    """Reduce una actualización de botón."""

    callback = actualizacion.get(
        "callback_query",
        {},
    )
    mensaje = callback.get(
        "message",
        {},
    )
    datos = callback.get(
        "data",
        "",
    )

    if ":" in datos:
        accion, codigo = datos.split(
            ":",
            1,
        )
    else:
        accion = datos
        codigo = ""

    return {
        "update_id": actualizacion.get(
            "update_id",
            0,
        ),
        "callback_query_id": callback.get(
            "id",
            "",
        ),
        "accion": accion.strip().lower(),
        "codigo": codigo.strip().upper(),
        "chat_id": (
            mensaje.get(
                "chat",
                {},
            ).get(
                "id",
                "",
            )
        ),
        "message_id": mensaje.get(
            "message_id",
            "",
        ),
    }
