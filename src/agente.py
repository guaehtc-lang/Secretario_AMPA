"""Agente con flujo determinista y una herramienta por paso."""

import json
import re
from inspect import Parameter, signature
from uuid import uuid4

from openai import (
    BadRequestError,
    OpenAI,
)

from src.parametros import (
    API_KEY,
    BASE_URL,
    MAX_PASOS,
    MAX_TOKENS,
    MODELO,
    MOSTRAR_PASOS,
    TEMPERATURA,
)


cliente = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


def ejecutar_funcion(
    nombre,
    argumentos,
    funciones,
):
    """Ejecuta una función registrada y controla errores."""

    funcion = funciones.get(
        nombre
    )

    if funcion is None:
        return {
            "ok": False,
            "estado": "herramienta_inexistente",
            "error": (
                f"La herramienta '{nombre}' "
                "no existe."
            ),
        }

    try:
        return funcion(
            **argumentos
        )

    except Exception as error:
        return {
            "ok": False,
            "estado": "error_herramienta",
            "error": str(error),
        }


def obtener_failed_generation(error):
    """Obtiene la llamada fallida incluida por Groq."""

    cuerpo = getattr(
        error,
        "body",
        None,
    )

    if isinstance(
        cuerpo,
        dict,
    ):
        datos_error = cuerpo.get(
            "error",
            cuerpo,
        )

        if isinstance(
            datos_error,
            dict,
        ):
            return datos_error.get(
                "failed_generation",
                "",
            )

    coincidencia = re.search(
        r"'failed_generation':\s*'([^']+)'",
        str(error),
    )

    if coincidencia:
        return coincidencia.group(
            1
        )

    return ""


def normalizar_json_embebido(valor):
    """Convierte listas o diccionarios enviados como texto JSON."""

    if isinstance(
        valor,
        str,
    ):
        texto = valor.strip()

        if (
            texto.startswith("[")
            or texto.startswith("{")
        ):
            try:
                convertido = json.loads(
                    texto
                )

                return normalizar_json_embebido(
                    convertido
                )

            except json.JSONDecodeError:
                return valor

        return valor

    if isinstance(
        valor,
        list,
    ):
        return [
            normalizar_json_embebido(
                elemento
            )
            for elemento in valor
        ]

    if isinstance(
        valor,
        dict,
    ):
        return {
            clave: normalizar_json_embebido(
                contenido
            )
            for clave, contenido
            in valor.items()
        }

    return valor


def extraer_llamada_de_texto(
    texto,
    funciones,
    nombre_esperado="",
):
    """Extrae una llamada concreta de un texto generado por Groq."""

    nombres = []

    if nombre_esperado:
        nombres.append(
            nombre_esperado
        )

    for nombre in re.findall(
        r"<function=([A-Za-z_][A-Za-z0-9_]*)>",
        texto,
    ):
        if nombre not in nombres:
            nombres.append(
                nombre
            )

    decoder = json.JSONDecoder()

    for nombre in nombres:
        if nombre not in funciones:
            continue

        marca = (
            f"<function={nombre}>"
        )

        posicion = texto.find(
            marca
        )

        if posicion == -1:
            continue

        fragmento = texto[
            posicion + len(marca):
        ].lstrip()

        try:
            argumentos, _ = decoder.raw_decode(
                fragmento
            )

        except json.JSONDecodeError:
            continue

        if not isinstance(
            argumentos,
            dict,
        ):
            continue

        return {
            "nombre": nombre,
            "argumentos": normalizar_json_embebido(
                argumentos
            ),
        }

    return None


def recuperar_llamada_fallida(
    error,
    funciones,
    nombre_esperado="",
):
    """Recupera únicamente la tool prevista en tool_use_failed."""

    texto = obtener_failed_generation(
        error
    )

    return extraer_llamada_de_texto(
        texto=texto,
        funciones=funciones,
        nombre_esperado=nombre_esperado,
    )


def seleccionar_tool(
    tools,
    nombre,
):
    """Devuelve únicamente el esquema de la siguiente tool."""

    return [
        tool
        for tool in tools
        if tool.get(
            "function",
            {},
        ).get(
            "name"
        )
        == nombre
    ]


def hay_opcion_disponible(resultado):
    """Comprueba si Calendar devolvió algún hueco libre."""

    return any(
        opcion.get(
            "disponible"
        )
        for opcion in resultado.get(
            "opciones",
            [],
        )
    )


def siguiente_herramienta(
    ejecutadas,
    clasificacion,
    contrapropuesta_reunion,
    resultados,
):
    """Decide el siguiente paso sin dejarlo al LLM."""

    if (
        "leer_correo_pendiente"
        not in ejecutadas
    ):
        return "leer_correo_pendiente"

    if (
        "clasificar_correo"
        not in ejecutadas
    ):
        return "clasificar_correo"

    if clasificacion in {
        "informativo",
        "confirmacion_reunion",
        "urgencia_seguridad",
        "revision_manual",
    }:
        return "registrar_resultado"

    if (
        clasificacion
        == "rechazo_reunion"
        and not contrapropuesta_reunion
    ):
        return "registrar_resultado"

    if clasificacion == "requiere_respuesta":
        if (
            "buscar_contexto_rag"
            not in ejecutadas
        ):
            return "buscar_contexto_rag"

        if (
            "crear_borrador"
            not in ejecutadas
        ):
            return "crear_borrador"

        return "registrar_resultado"

    if (
        clasificacion
        == "solicitud_reunion"
        or (
            clasificacion
            == "rechazo_reunion"
            and contrapropuesta_reunion
        )
    ):
        if (
            "consultar_disponibilidad"
            not in ejecutadas
        ):
            return "consultar_disponibilidad"

        disponibilidad = resultados.get(
            "consultar_disponibilidad",
            {},
        )

        if (
            disponibilidad.get(
                "ok"
            )
            and hay_opcion_disponible(
                disponibilidad
            )
            and "crear_invitacion_calendar"
            not in ejecutadas
        ):
            return "crear_invitacion_calendar"

        return "registrar_resultado"

    return "registrar_resultado"


def preparar_argumentos(
    nombre,
    argumentos,
    message_id,
    clasificacion,
):
    """Fija identificadores y clasificación validados."""

    argumentos = normalizar_json_embebido(
        argumentos
    )

    if not isinstance(
        argumentos,
        dict,
    ):
        argumentos = {}

    if (
        nombre
        == "clasificar_correo"
        and message_id
    ):
        argumentos[
            "message_id"
        ] = message_id

    if nombre in {
        "buscar_contexto_rag",
        "crear_borrador",
        "consultar_disponibilidad",
        "crear_invitacion_calendar",
        "registrar_resultado",
    }:
        argumentos[
            "message_id"
        ] = message_id

        argumentos[
            "clasificacion"
        ] = clasificacion

    return argumentos



def filtrar_argumentos_funcion(
    nombre,
    argumentos,
    funciones,
):
    """Elimina argumentos que la función Python no admite."""

    funcion = funciones.get(
        nombre
    )

    if (
        funcion is None
        or not isinstance(
            argumentos,
            dict,
        )
    ):
        return argumentos, []

    parametros = signature(
        funcion
    ).parameters

    admite_kwargs = any(
        parametro.kind
        == Parameter.VAR_KEYWORD
        for parametro in parametros.values()
    )

    if admite_kwargs:
        return argumentos, []

    argumentos_limpios = {
        clave: valor
        for clave, valor in argumentos.items()
        if clave in parametros
    }

    descartados = [
        clave
        for clave in argumentos
        if clave not in parametros
    ]

    return (
        argumentos_limpios,
        descartados,
    )


def añadir_resultado_herramienta(
    mensajes,
    nombre,
    argumentos,
    resultado,
    tool_call_id,
):
    """Añade la llamada y su resultado al historial."""

    mensajes.append({
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": nombre,
                    "arguments": json.dumps(
                        argumentos,
                        ensure_ascii=False,
                    ),
                },
            }
        ],
    })

    mensajes.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": nombre,
        "content": json.dumps(
            resultado,
            ensure_ascii=False,
            default=str,
        ),
    })


def ejecutar_agente(
    mensajes,
    tools,
    funciones,
    max_pasos=MAX_PASOS,
    verbose=MOSTRAR_PASOS,
):
    """Ejecuta el flujo previsto con una tool por paso."""

    ejecutadas = []
    resultados = {}
    message_id = ""
    clasificacion = ""
    contrapropuesta_reunion = False

    for paso in range(
        1,
        max_pasos + 1,
    ):
        nombre_esperado = siguiente_herramienta(
            ejecutadas=ejecutadas,
            clasificacion=clasificacion,
            contrapropuesta_reunion=(
                contrapropuesta_reunion
            ),
            resultados=resultados,
        )

        tools_paso = seleccionar_tool(
            tools,
            nombre_esperado,
        )

        if not tools_paso:
            return json.dumps(
                {
                    "ok": False,
                    "estado": "tool_no_configurada",
                    "tool": nombre_esperado,
                },
                ensure_ascii=False,
            )

        ejecucion_directa = (
            nombre_esperado
            == "leer_correo_pendiente"
        )

        if ejecucion_directa:
            nombre = nombre_esperado
            argumentos = {}
            llamada = None
            recuperada = False

        else:
            try:
                respuesta = cliente.chat.completions.create(
                    model=MODELO,
                    messages=mensajes,
                    tools=tools_paso,
                    tool_choice={
                        "type": "function",
                        "function": {
                            "name": nombre_esperado,
                        },
                    },
                    temperature=TEMPERATURA,
                    max_tokens=MAX_TOKENS,
                )

                msg = respuesta.choices[
                    0
                ].message

                if not msg.tool_calls:
                    return json.dumps(
                        {
                            "ok": False,
                            "estado": "tool_no_generada",
                            "tool_esperada": nombre_esperado,
                            "respuesta": msg.content or "",
                        },
                        ensure_ascii=False,
                    )

                llamada = msg.tool_calls[
                    0
                ]

                nombre = llamada.function.name

                try:
                    argumentos = json.loads(
                        llamada.function.arguments
                        or "{}"
                    )

                except json.JSONDecodeError:
                    argumentos = {}

                recuperada = False

            except BadRequestError as error:
                llamada_recuperada = (
                    recuperar_llamada_fallida(
                        error=error,
                        funciones=funciones,
                        nombre_esperado=nombre_esperado,
                    )
                )

                if llamada_recuperada is None:
                    return json.dumps(
                        {
                            "ok": False,
                            "estado": (
                                "error_function_calling"
                            ),
                            "error": str(error),
                        },
                        ensure_ascii=False,
                    )

                nombre = llamada_recuperada[
                    "nombre"
                ]

                argumentos = llamada_recuperada[
                    "argumentos"
                ]

                llamada = None
                recuperada = True
        if nombre != nombre_esperado:
            return json.dumps(
                {
                    "ok": False,
                    "estado": "tool_fuera_de_flujo",
                    "tool_esperada": nombre_esperado,
                    "tool_recibida": nombre,
                },
                ensure_ascii=False,
            )

        argumentos = preparar_argumentos(
            nombre=nombre,
            argumentos=argumentos,
            message_id=message_id,
            clasificacion=clasificacion,
        )

        (
            argumentos,
            argumentos_descartados,
        ) = filtrar_argumentos_funcion(
            nombre=nombre,
            argumentos=argumentos,
            funciones=funciones,
        )

        resultado = ejecutar_funcion(
            nombre,
            argumentos,
            funciones,
        )

        tool_call_id = (
            llamada.id
            if llamada is not None
            else (
                "call_recuperada_"
                + uuid4().hex[:12]
            )
        )

        añadir_resultado_herramienta(
            mensajes=mensajes,
            nombre=nombre,
            argumentos=argumentos,
            resultado=resultado,
            tool_call_id=tool_call_id,
        )

        ejecutadas.append(
            nombre
        )

        resultados[
            nombre
        ] = resultado

        if (
            nombre
            == "leer_correo_pendiente"
            and resultado.get(
                "estado"
            )
            == "correo_encontrado"
        ):
            message_id = (
                resultado.get(
                    "correo",
                    {},
                ).get(
                    "message_id",
                    "",
                )
            )

        if (
            nombre
            == "clasificar_correo"
            and resultado.get(
                "ok"
            )
        ):
            clasificacion = resultado.get(
                "clasificacion",
                "",
            )

            contrapropuesta_reunion = bool(
                resultado.get(
                    "contrapropuesta_reunion",
                    False,
                )
            )

        if verbose:
            if ejecucion_directa:
                marca = " [DIRECTA]"

            elif recuperada:
                marca = " [RECUPERADA]"

            else:
                marca = ""

            print(
                f"[Paso {paso}] "
                f"{nombre}({argumentos})"
                f"{marca}"
            )

            if argumentos_descartados:
                print(
                    "  ARGUMENTOS DESCARTADOS:",
                    argumentos_descartados,
                )

            if not resultado.get(
                "ok",
                True,
            ):
                print(
                    "  ERROR TOOL:",
                    json.dumps(
                        resultado,
                        ensure_ascii=False,
                        default=str,
                    ),
                )

        if (
            nombre
            == "leer_correo_pendiente"
            and resultado.get(
                "estado"
            )
            == "sin_correos_pendientes"
        ):
            return json.dumps(
                resultado,
                ensure_ascii=False,
            )

        if (
            nombre
            in {
                "leer_correo_pendiente",
                "clasificar_correo",
            }
            and not resultado.get(
                "ok",
                False,
            )
        ):
            return json.dumps(
                resultado,
                ensure_ascii=False,
                default=str,
            )

        if (
            nombre
            == "registrar_resultado"
        ):
            return json.dumps(
                resultado,
                ensure_ascii=False,
                default=str,
            )

    return json.dumps(
        {
            "ok": False,
            "estado": "limite_pasos_alcanzado",
            "max_pasos": max_pasos,
        },
        ensure_ascii=False,
    )
