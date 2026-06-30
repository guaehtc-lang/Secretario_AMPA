"""Conexión con Composio y funciones directas de Gmail."""

import html
import json
import re
import time
from email.utils import parsedate_to_datetime
from functools import lru_cache

from composio import (
    Composio,
    SESSION_PRESET_DIRECT_TOOLS,
)
from composio_openai import OpenAIProvider

from src.memoria import (
    obtener_ids_procesados,
    obtener_registro_correo,
)
from src.parametros import (
    ALLOW_CREATE_DRAFTS,
    ALLOW_EMAIL_SEND,
    ALLOW_MARK_AS_READ,
    COMPOSIO_API_KEY,
    COMPOSIO_USER_ID,
    GMAIL_MARK_READ_ACTION,
    GMAIL_QUERY,
    MAX_EMAILS_PER_RUN,
)


def convertir_resultado(resultado):
    """Convierte una respuesta externa en diccionario."""

    if hasattr(
        resultado,
        "model_dump",
    ):
        resultado = resultado.model_dump()

    if isinstance(
        resultado,
        dict,
    ):
        return resultado

    if isinstance(
        resultado,
        str,
    ):
        try:
            return json.loads(
                resultado
            )
        except json.JSONDecodeError:
            return {
                "texto": resultado
            }

    return {
        "texto": str(
            resultado
        )
    }


def buscar_valor(
    objeto,
    claves,
):
    """Busca recursivamente el primer valor solicitado."""

    if isinstance(
        objeto,
        dict,
    ):
        for clave in claves:
            valor = objeto.get(
                clave
            )

            if valor not in [
                None,
                "",
                [],
                {},
            ]:
                return valor

        for valor in objeto.values():
            encontrado = buscar_valor(
                valor,
                claves,
            )

            if encontrado not in [
                None,
                "",
                [],
                {},
            ]:
                return encontrado

    elif isinstance(
        objeto,
        list,
    ):
        for elemento in objeto:
            encontrado = buscar_valor(
                elemento,
                claves,
            )

            if encontrado not in [
                None,
                "",
                [],
                {},
            ]:
                return encontrado

    return None


def buscar_ids(objeto):
    """Busca identificadores de mensajes de Gmail."""

    ids = []

    if isinstance(
        objeto,
        dict,
    ):
        for clave, valor in objeto.items():
            if (
                clave
                in [
                    "messageId",
                    "message_id",
                ]
                and isinstance(
                    valor,
                    str,
                )
            ):
                ids.append(
                    valor
                )

            elif (
                clave == "id"
                and isinstance(
                    valor,
                    str,
                )
                and not valor.startswith(
                    "log_"
                )
            ):
                ids.append(
                    valor
                )

            elif isinstance(
                valor,
                (
                    dict,
                    list,
                ),
            ):
                ids += buscar_ids(
                    valor
                )

    elif isinstance(
        objeto,
        list,
    ):
        for elemento in objeto:
            ids += buscar_ids(
                elemento
            )

    return list(
        dict.fromkeys(
            ids
        )
    )


def obtener_cabecera(
    headers,
    nombre,
):
    """Obtiene una cabecera de Gmail."""

    for header in headers:
        if (
            header.get(
                "name",
                "",
            ).lower()
            == nombre.lower()
        ):
            return header.get(
                "value",
                "",
            )

    return ""


def extraer_email(texto):
    """Extrae una dirección de correo."""

    coincidencia = re.search(
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}",
        texto
        or "",
    )

    if coincidencia:
        return coincidencia.group(
            0
        )

    return ""


def timestamp_fecha(texto):
    """Convierte una fecha de correo en timestamp."""

    try:
        return parsedate_to_datetime(
            texto
        ).timestamp()
    except (
        TypeError,
        ValueError,
        OverflowError,
    ):
        return 0


def limpiar_texto(texto):
    """Convierte HTML sencillo en texto plano."""

    texto = texto or ""

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

    texto = re.sub(
        r"\r\n?",
        "\n",
        texto,
    )

    texto = re.sub(
        r"\n{3,}",
        "\n\n",
        texto,
    )

    return texto.strip()


def resultado_tiene_error(
    resultado,
):
    """Comprueba errores habituales."""

    resultado = convertir_resultado(
        resultado
    )

    if resultado.get(
        "ok"
    ) is False:
        return True

    if resultado.get(
        "success"
    ) is False:
        return True

    if resultado.get(
        "successful"
    ) is False:
        return True

    if resultado.get(
        "error"
    ) not in [
        None,
        "",
        False,
        {},
    ]:
        return True

    return False


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
    """Crea una sesión para Gmail y Calendar."""

    composio = crear_cliente_composio()

    return composio.create(
        user_id=COMPOSIO_USER_ID,
        toolkits=[
            "gmail",
            "googlecalendar",
        ],
        session_preset=(
            SESSION_PRESET_DIRECT_TOOLS
        ),
    )


def preparar_correo(resultado):
    """Reduce una respuesta de Gmail."""

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

    cuerpo = (
        datos.get(
            "messageText"
        )
        or datos.get(
            "snippet"
        )
        or ""
    )

    labels = (
        datos.get(
            "labelIds"
        )
        or datos.get(
            "label_ids"
        )
        or buscar_valor(
            respuesta,
            [
                "labelIds",
                "label_ids",
                "labels",
            ],
        )
        or []
    )

    if isinstance(
        labels,
        str,
    ):
        labels = [
            labels
        ]

    return {
        "message_id": (
            datos.get(
                "messageId"
            )
            or datos.get(
                "id"
            )
            or ""
        ),
        "thread_id": (
            datos.get(
                "threadId"
            )
            or datos.get(
                "thread_id"
            )
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
        "cuerpo": limpiar_texto(
            cuerpo
        )[:6000],
        "labels": labels,
    }


def obtener_correo_por_id(
    message_id,
):
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

    correo[
        "message_id"
    ] = (
        correo[
            "message_id"
        ]
        or message_id
    )

    return correo


def obtener_correos_no_leidos():
    """Obtiene correos no leídos por orden cronológico."""

    sesion = obtener_sesion_google()

    listado = sesion.execute(
        "GMAIL_FETCH_EMAILS",
        arguments={
            "ids_only": True,
            "include_payload": False,
            "include_spam_trash": False,
            "label_ids": [
                "INBOX",
                "UNREAD",
            ],
            "max_results": (
                MAX_EMAILS_PER_RUN
            ),
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

    correos = []

    for message_id in ids:
        if message_id in procesados:
            continue

        correo = obtener_correo_por_id(
            message_id
        )

        correo[
            "_registro_previo"
        ] = obtener_registro_correo(
            message_id
        )

        correo[
            "_orden"
        ] = timestamp_fecha(
            correo[
                "fecha"
            ]
        )

        correos.append(
            correo
        )

    correos.sort(
        key=lambda correo: correo[
            "_orden"
        ]
    )

    for correo in correos:
        correo.pop(
            "_orden",
            None,
        )

    return correos


def crear_borrador(
    message_id,
    asunto,
    cuerpo,
):
    """Crea un borrador. Nunca lo envía."""

    if not ALLOW_CREATE_DRAFTS:
        return {
            "ok": False,
            "estado": (
                "borradores_desactivados"
            ),
        }

    if not cuerpo.strip():
        return {
            "ok": False,
            "estado": "cuerpo_vacio",
        }

    correo = obtener_correo_por_id(
        message_id
    )

    destinatario = extraer_email(
        correo[
            "remitente"
        ]
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
        "body": limpiar_texto(
            cuerpo
        ),
        "is_html": False,
        "user_id": "me",
    }

    if correo[
        "thread_id"
    ]:
        argumentos[
            "thread_id"
        ] = correo[
            "thread_id"
        ]

        argumentos[
            "subject"
        ] = ""

    else:
        argumentos[
            "subject"
        ] = asunto

    sesion = obtener_sesion_google()

    resultado = convertir_resultado(
        sesion.execute(
            "GMAIL_CREATE_EMAIL_DRAFT",
            arguments=argumentos,
        )
    )

    if resultado_tiene_error(
        resultado
    ):
        return {
            "ok": False,
            "estado": (
                "error_creando_borrador"
            ),
            "resultado": resultado,
        }

    draft_id = buscar_valor(
        resultado,
        [
            "draft_id",
            "draftId",
            "id",
        ],
    )

    return {
        "ok": True,
        "estado": "borrador_creado",
        "draft_id": draft_id or "",
        "destinatario": destinatario,
    }


def _convertir_tool(tool):
    """Convierte una definición de tool."""

    if hasattr(
        tool,
        "model_dump",
    ):
        tool = tool.model_dump()

    if not isinstance(
        tool,
        dict,
    ):
        return None

    funcion = tool.get(
        "function",
        tool,
    )

    if not isinstance(
        funcion,
        dict,
    ):
        return None

    nombre = (
        funcion.get(
            "name"
        )
        or tool.get(
            "name"
        )
    )

    parametros = funcion.get(
        "parameters",
        {},
    )

    if not nombre:
        return None

    return {
        "nombre": nombre,
        "parametros": parametros,
    }


def _tools_disponibles(sesion):
    """Lee las tools expuestas por la sesión."""

    herramientas = getattr(
        sesion,
        "tools",
        [],
    )

    if callable(
        herramientas
    ):
        return []

    if not isinstance(
        herramientas,
        (
            list,
            tuple,
        ),
    ):
        return []

    tools = []

    for tool in herramientas:
        convertido = _convertir_tool(
            tool
        )

        if convertido:
            tools.append(
                convertido
            )

    return tools


def _argumentos_segun_schema(
    parametros,
    message_id,
):
    """Construye argumentos usando el schema real."""

    propiedades = parametros.get(
        "properties",
        {},
    )

    if not propiedades:
        return None

    argumentos = {}

    if "message_id" in propiedades:
        argumentos[
            "message_id"
        ] = message_id

    elif "email_id" in propiedades:
        argumentos[
            "email_id"
        ] = message_id

    elif "id" in propiedades:
        argumentos[
            "id"
        ] = message_id

    elif "message_ids" in propiedades:
        argumentos[
            "message_ids"
        ] = [
            message_id
        ]

    elif "ids" in propiedades:
        argumentos[
            "ids"
        ] = [
            message_id
        ]

    else:
        return None

    campos_quitar = [
        "remove_label_ids",
        "remove_labels",
        "label_ids_to_remove",
        "labels_to_remove",
        "removeLabelIds",
    ]

    campos_anadir = [
        "add_label_ids",
        "add_labels",
        "label_ids_to_add",
        "labels_to_add",
        "addLabelIds",
    ]

    encontrado = False

    for campo in campos_quitar:
        if campo in propiedades:
            argumentos[
                campo
            ] = [
                "UNREAD"
            ]
            encontrado = True
            break

    for campo in campos_anadir:
        if campo in propiedades:
            argumentos[
                campo
            ] = []
            break

    if "mark_as_read" in propiedades:
        argumentos[
            "mark_as_read"
        ] = True
        encontrado = True

    if "is_read" in propiedades:
        argumentos[
            "is_read"
        ] = True
        encontrado = True

    if "read" in propiedades:
        argumentos[
            "read"
        ] = True
        encontrado = True

    if "user_id" in propiedades:
        argumentos[
            "user_id"
        ] = "me"

    if not encontrado:
        return None

    return argumentos


def _correo_esta_leido(
    message_id,
):
    """Comprueba que Gmail ya no devuelve UNREAD."""

    correo = obtener_correo_por_id(
        message_id
    )

    labels = {
        str(
            label
        ).upper()
        for label in correo.get(
            "labels",
            [],
        )
    }

    return "UNREAD" not in labels


def marcar_como_leido(
    message_id,
):
    """Quita UNREAD y verifica el resultado."""

    if not ALLOW_MARK_AS_READ:
        return {
            "ok": False,
            "estado": (
                "cambio_estado_desactivado"
            ),
        }

    try:
        if _correo_esta_leido(
            message_id
        ):
            return {
                "ok": True,
                "estado": (
                    "correo_ya_estaba_leido"
                ),
                "verificado": True,
            }
    except Exception:
        pass

    sesion = obtener_sesion_google()
    tools_sesion = _tools_disponibles(
        sesion
    )

    candidatos = []

    for tool in tools_sesion:
        nombre = tool[
            "nombre"
        ]
        texto = nombre.upper()

        if (
            "GMAIL" in texto
            and (
                "MODIFY" in texto
                or "LABEL" in texto
            )
            and "THREAD" not in texto
        ):
            argumentos = _argumentos_segun_schema(
                tool[
                    "parametros"
                ],
                message_id,
            )

            if argumentos:
                candidatos.append(
                    (
                        nombre,
                        argumentos,
                    )
                )

    argumentos_posibles = [
        {
            "message_id": message_id,
            "add_label_ids": [],
            "remove_label_ids": [
                "UNREAD"
            ],
            "user_id": "me",
        },
        {
            "message_id": message_id,
            "add_labels": [],
            "remove_labels": [
                "UNREAD"
            ],
            "user_id": "me",
        },
        {
            "message_id": message_id,
            "label_ids_to_add": [],
            "label_ids_to_remove": [
                "UNREAD"
            ],
            "user_id": "me",
        },
        {
            "message_ids": [
                message_id
            ],
            "add_label_ids": [],
            "remove_label_ids": [
                "UNREAD"
            ],
            "user_id": "me",
        },
    ]

    nombres = [
        GMAIL_MARK_READ_ACTION,
        "GMAIL_MODIFY_EMAIL_LABELS",
        "GMAIL_MODIFY_MESSAGE_LABELS",
        "GMAIL_MODIFY_EMAIL",
        "GMAIL_BATCH_MODIFY_MESSAGES",
    ]

    for nombre in nombres:
        for argumentos in argumentos_posibles:
            candidatos.append(
                (
                    nombre,
                    argumentos,
                )
            )

    unicos = []
    vistos = set()

    for nombre, argumentos in candidatos:
        clave = (
            nombre,
            str(
                argumentos
            ),
        )

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        unicos.append(
            (
                nombre,
                argumentos,
            )
        )

    errores = []

    for nombre, argumentos in unicos:
        try:
            resultado = convertir_resultado(
                sesion.execute(
                    nombre,
                    arguments=argumentos,
                )
            )

            if resultado_tiene_error(
                resultado
            ):
                errores.append({
                    "tool": nombre,
                    "resultado": resultado,
                })
                continue

            for _ in range(2):
                time.sleep(
                    0.4
                )

                if _correo_esta_leido(
                    message_id
                ):
                    return {
                        "ok": True,
                        "estado": (
                            "correo_marcado_leido"
                        ),
                        "tool": nombre,
                        "verificado": True,
                    }

            errores.append({
                "tool": nombre,
                "error": (
                    "La llamada terminó, "
                    "pero UNREAD continúa."
                ),
            })

        except Exception as error:
            errores.append({
                "tool": nombre,
                "error": str(
                    error
                ),
            })

    return {
        "ok": False,
        "estado": (
            "no_se_pudo_marcar_leido"
        ),
        "verificado": False,
        "errores": errores[-8:],
    }


def _argumentos_enviar_borrador(
    parametros,
    draft_id,
):
    """Construye argumentos según el schema disponible."""

    propiedades = parametros.get(
        "properties",
        {},
    )
    argumentos = {}

    if "draft_id" in propiedades:
        argumentos[
            "draft_id"
        ] = draft_id

    elif "draftId" in propiedades:
        argumentos[
            "draftId"
        ] = draft_id

    elif "id" in propiedades:
        argumentos[
            "id"
        ] = draft_id

    else:
        return None

    if "user_id" in propiedades:
        argumentos[
            "user_id"
        ] = "me"

    return argumentos


def enviar_borrador(
    draft_id,
):
    """Envía un borrador autorizado desde Telegram."""

    if not ALLOW_EMAIL_SEND:
        return {
            "ok": False,
            "estado": "envio_email_desactivado",
        }

    if not draft_id:
        return {
            "ok": False,
            "estado": "draft_id_vacio",
        }

    sesion = obtener_sesion_google()
    candidatos = []

    for tool in _tools_disponibles(
        sesion
    ):
        nombre = tool[
            "nombre"
        ]

        if (
            nombre.upper()
            == "GMAIL_SEND_DRAFT"
        ):
            argumentos = (
                _argumentos_enviar_borrador(
                    tool[
                        "parametros"
                    ],
                    draft_id,
                )
            )

            if argumentos:
                candidatos.append(
                    (
                        nombre,
                        argumentos,
                    )
                )

    candidatos += [
        (
            "GMAIL_SEND_DRAFT",
            {
                "draft_id": draft_id,
                "user_id": "me",
            },
        ),
        (
            "GMAIL_SEND_DRAFT",
            {
                "id": draft_id,
                "user_id": "me",
            },
        ),
    ]

    errores = []
    vistos = set()

    for nombre, argumentos in candidatos:
        clave = (
            nombre,
            str(
                argumentos
            ),
        )

        if clave in vistos:
            continue

        vistos.add(
            clave
        )

        try:
            resultado = convertir_resultado(
                sesion.execute(
                    nombre,
                    arguments=argumentos,
                )
            )

            if resultado_tiene_error(
                resultado
            ):
                errores.append({
                    "tool": nombre,
                    "resultado": resultado,
                })
                continue

            message_id = buscar_valor(
                resultado,
                [
                    "message_id",
                    "messageId",
                    "id",
                ],
            )

            return {
                "ok": True,
                "estado": "borrador_enviado",
                "draft_id": draft_id,
                "message_id": (
                    message_id
                    or ""
                ),
                "tool": nombre,
            }

        except Exception as error:
            errores.append({
                "tool": nombre,
                "error": str(
                    error
                ),
            })

    return {
        "ok": False,
        "estado": "no_se_pudo_enviar_borrador",
        "draft_id": draft_id,
        "errores": errores,
    }

