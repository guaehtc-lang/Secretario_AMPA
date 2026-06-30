"""Funciones de Gmail utilizadas por el agente."""

import html
import re

from src.composio_cliente import obtener_sesion_google
from src.memoria import (
    obtener_ids_procesados,
    registrar_accion,
)
from src.parametros import (
    ALLOW_CREATE_DRAFTS,
    GMAIL_QUERY,
    MAX_CORREOS_BUSQUEDA,
)
from src.utilidades import (
    buscar_ids,
    buscar_mensajes,
    buscar_valor,
    convertir_resultado,
    extraer_email,
    obtener_cabecera,
    timestamp_fecha,
)


CLASIFICACIONES_CON_BORRADOR = {
    "requiere_respuesta",
    "solicitud_reunion",
    "rechazo_reunion",
}

INDICADORES_INFORMATIVOS = [
    "no requiere respuesta",
    "no es necesario responder",
    "únicamente informativo",
    "unicamente informativo",
    "solo informativo",
    "a título informativo",
    "a titulo informativo",
    "para vuestra información",
    "para vuestra informacion",
]

DATOS_DE_RIESGO = [
    "transferencia",
    "efectivo",
    "bizum",
    "domiciliación",
    "domiciliacion",
    "iban",
    "euros",
    "€",
    "sitio web",
    "página web",
    "pagina web",
    "oficina",
    "dni",
    "formulario",
    "certificado",
]


def normalizar_texto(texto):
    """Normaliza un texto para aplicar controles."""

    return " ".join(
        (texto or "").lower().split()
    )


def preparar_correo(resultado):
    """Reduce la respuesta de Gmail a los campos necesarios."""

    respuesta = convertir_resultado(
        resultado
    )

    datos = respuesta.get(
        "data",
        respuesta,
    )

    payload = datos.get(
        "payload",
        {},
    )

    headers = payload.get(
        "headers",
        [],
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
        "cuerpo": (
            datos.get("messageText")
            or datos.get("snippet")
            or ""
        )[:5000],
        "labels": datos.get(
            "labelIds",
            [],
        ),
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

    correo = preparar_correo(
        resultado
    )

    correo["message_id"] = (
        correo["message_id"]
        or message_id
    )

    return correo


def obtener_hilo(thread_id, limite=5):
    """Recupera el contexto reciente del hilo."""

    if not thread_id:
        return []

    sesion = obtener_sesion_google()

    resultado = sesion.execute(
        "GMAIL_FETCH_MESSAGE_BY_THREAD_ID",
        arguments={
            "thread_id": thread_id,
            "user_id": "me",
            "page_token": "",
        },
    )

    mensajes = buscar_mensajes(
        convertir_resultado(
            resultado
        )
    )

    contexto = []

    for mensaje in mensajes:

        if (
            "DRAFT"
            in mensaje.get(
                "labelIds",
                [],
            )
        ):
            continue

        payload = mensaje.get(
            "payload",
            {},
        )

        headers = payload.get(
            "headers",
            [],
        )

        fecha = obtener_cabecera(
            headers,
            "Date",
        )

        contexto.append({
            "message_id": (
                mensaje.get("messageId")
                or mensaje.get("id")
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
            "fecha": fecha,
            "asunto": obtener_cabecera(
                headers,
                "Subject",
            ),
            "cuerpo": (
                mensaje.get("messageText")
                or mensaje.get("snippet")
                or ""
            )[:1800],
            "labels": mensaje.get(
                "labelIds",
                [],
            ),
            "_orden": timestamp_fecha(
                fecha
            ),
        })

    contexto.sort(
        key=lambda mensaje: mensaje[
            "_orden"
        ]
    )

    for mensaje in contexto:
        mensaje.pop(
            "_orden",
            None,
        )

    return contexto[
        -limite:
    ]


def leer_correo_pendiente():
    """Lee el correo no procesado más reciente y su hilo."""

    sesion = obtener_sesion_google()

    listado = sesion.execute(
        "GMAIL_FETCH_EMAILS",
        arguments={
            "ids_only": True,
            "include_payload": False,
            "include_spam_trash": False,
            "label_ids": ["INBOX"],
            "max_results": MAX_CORREOS_BUSQUEDA,
            "page_token": "",
            "query": GMAIL_QUERY,
            "user_id": "me",
            "verbose": False,
        },
    )

    ids = buscar_ids(
        convertir_resultado(
            listado
        )
    )

    procesados = set(
        obtener_ids_procesados()
    )

    pendientes = [
        message_id
        for message_id in ids
        if message_id
        not in procesados
    ]

    correos = []

    for message_id in pendientes:
        correo = obtener_correo_por_id(
            message_id
        )

        correo["_orden"] = timestamp_fecha(
            correo["fecha"]
        )

        correos.append(
            correo
        )

    if not correos:
        return {
            "ok": True,
            "estado": "sin_correos_pendientes",
        }

    correos.sort(
        key=lambda correo: correo[
            "_orden"
        ],
        reverse=True,
    )

    correo = correos[0]
    correo.pop(
        "_orden",
        None,
    )

    correo["hilo"] = obtener_hilo(
        correo["thread_id"]
    )

    return {
        "ok": True,
        "estado": "correo_encontrado",
        "correo": correo,
    }


def respuesta_neutral():
    """Devuelve una respuesta segura cuando no hay evidencia."""

    return (
        "Buenos días:\n\n"
        "Gracias por tu consulta. Estamos comprobando "
        "la información necesaria para poder darte una "
        "respuesta correcta sobre la documentación, la "
        "cuota y las formas de pago.\n\n"
        "Te responderemos cuando dispongamos de los "
        "datos confirmados.\n\n"
        "Un saludo.\n"
        "AMPA"
    )



def limpiar_borrador_propuesto(texto):
    """Convierte la propuesta en texto plano y elimina citas."""

    texto = texto or ""

    cortes = [
        '<div class="gmail_quote">',
        '<div class="gmail_attr">',
        '<blockquote',
        " wrote:",
        " escribió:",
    ]

    posicion_corte = len(texto)

    for corte in cortes:
        posicion = texto.lower().find(
            corte.lower()
        )

        if (
            posicion != -1
            and posicion < posicion_corte
        ):
            posicion_corte = posicion

    texto = texto[
        :posicion_corte
    ]

    texto = re.sub(
        r"<br\s*/?>",
        "\n",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"<[^>]+>",
        "",
        texto,
    )

    texto = html.unescape(
        texto
    )

    lineas = [
        linea.rstrip()
        for linea in texto.splitlines()
    ]

    texto = "\n".join(
        lineas
    )

    texto = re.sub(
        r"\n{3,}",
        "\n\n",
        texto,
    )

    return texto.strip()


def obtener_elementos_control(texto):
    """Extrae números, enlaces y correos de un texto."""

    return {
        "numeros": set(
            re.findall(
                r"\b\d+(?:[.,]\d+)?\b",
                texto or "",
            )
        ),
        "urls": set(
            re.findall(
                r"https?://\S+",
                texto or "",
                flags=re.IGNORECASE,
            )
        ),
        "emails": set(
            re.findall(
                r"[A-Za-z0-9._%+-]+"
                r"@[A-Za-z0-9.-]+"
                r"\.[A-Za-z]{2,}",
                texto or "",
            )
        ),
    }


def borrador_no_respaldado(
    cuerpo,
    evidencia,
):
    """Detecta datos concretos que no aparecen en el histórico."""

    cuerpo_normalizado = normalizar_texto(
        cuerpo
    )

    evidencia_normalizada = normalizar_texto(
        evidencia
    )

    elementos_cuerpo = obtener_elementos_control(
        cuerpo
    )

    elementos_evidencia = obtener_elementos_control(
        evidencia
    )

    for tipo in [
        "numeros",
        "urls",
        "emails",
    ]:
        if not elementos_cuerpo[
            tipo
        ].issubset(
            elementos_evidencia[
                tipo
            ]
        ):
            return True

    for dato in DATOS_DE_RIESGO:
        if (
            dato in cuerpo_normalizado
            and dato
            not in evidencia_normalizada
        ):
            return True

    return False


def crear_borrador(
    message_id,
    asunto,
    cuerpo,
    clasificacion,
):
    """Crea un borrador con barreras contra invenciones."""

    clasificacion = (
        clasificacion
        or ""
    ).strip().lower()

    if (
        clasificacion
        not in CLASIFICACIONES_CON_BORRADOR
    ):
        return {
            "ok": False,
            "estado": (
                "borrador_bloqueado_"
                "por_clasificacion"
            ),
            "clasificacion": clasificacion,
        }

    if not ALLOW_CREATE_DRAFTS:
        return {
            "ok": False,
            "estado": "borradores_desactivados",
        }

    correo = obtener_correo_por_id(
        message_id
    )

    texto_original = normalizar_texto(
        correo["cuerpo"]
    )

    if any(
        indicador in texto_original
        for indicador in INDICADORES_INFORMATIVOS
    ):
        return {
            "ok": False,
            "estado": (
                "borrador_bloqueado_"
                "correo_informativo"
            ),
        }

    from src.rag import obtener_contexto_rag

    contexto = obtener_contexto_rag(
        message_id
    )

    if contexto is None:
        return {
            "ok": False,
            "estado": "rag_no_consultado",
            "mensaje": (
                "Antes de crear el borrador debe "
                "consultarse el RAG para este correo."
            ),
        }

    resultados = contexto.get(
        "resultados",
        [],
    )

    resultados_validos = [
        resultado
        for resultado in resultados
        if resultado.get(
            "fuente_validada"
        ) is True
    ]

    evidencia = "\n\n".join(
        resultado.get(
            "cuerpo",
            "",
        )
        for resultado in resultados_validos
    )

    cuerpo_propuesto = limpiar_borrador_propuesto(
        cuerpo
    )

    usar_respuesta_neutral = (
        not resultados_validos
        or not cuerpo_propuesto
        or normalizar_texto(
            cuerpo_propuesto
        )
        == texto_original
        or borrador_no_respaldado(
            cuerpo_propuesto,
            evidencia,
        )
    )

    if usar_respuesta_neutral:
        cuerpo_final = respuesta_neutral()
        modo = "neutral_sin_evidencia"

    else:
        cuerpo_final = cuerpo_propuesto
        modo = "basado_en_historico"

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
        "body": cuerpo_final,
        "is_html": False,
        "user_id": "me",
    }

    if correo["thread_id"]:
        argumentos["thread_id"] = (
            correo["thread_id"]
        )
        argumentos["subject"] = ""

    else:
        argumentos["subject"] = (
            asunto
        )

    sesion = obtener_sesion_google()

    resultado = convertir_resultado(
        sesion.execute(
            "GMAIL_CREATE_EMAIL_DRAFT",
            arguments=argumentos,
        )
    )

    draft_id = buscar_valor(
        resultado,
        [
            "draft_id",
            "draftId",
            "id",
        ],
    )

    registrar_accion(
        message_id=message_id,
        tipo="borrador_creado",
        detalle=modo,
    )

    return {
        "ok": True,
        "estado": "borrador_creado",
        "modo": modo,
        "fuentes_rag_validas": len(
            resultados_validos
        ),
        "draft_id": draft_id or "",
        "destinatario": destinatario,
        "clasificacion": clasificacion,
        "cuerpo_utilizado": cuerpo_final,
    }
