"""Funciones de alto nivel y registro del agente."""

import json

from src.calendar import (
    consultar_disponibilidad,
)
from src.gmail import (
    crear_borrador,
    limpiar_texto,
    marcar_como_leido,
    obtener_correos_no_leidos,
)
from src.llm import preguntar_json
from src.memoria import registrar_correo
from src.parametros import (
    DEFAULT_MEETING_MINUTES,
)
from src.rag import (
    consultar_antecedentes_gmail,
)
from src.whatsapp import enviar_whatsapp


CLASIFICACIONES = {
    "informativo",
    "necesita_respuesta",
    "reunion",
    "urgente_seguridad",
    "no_clasificado",
}

TIPOS_REUNION = {
    "solicitud",
    "cambio",
    "confirmacion",
    "rechazo",
    "no_claro",
}

RESPUESTA_NEUTRAL = (
    "Buenos días:\n\n"
    "Gracias por tu consulta. Estamos comprobando "
    "la información necesaria para poder darte "
    "una respuesta correcta.\n\n"
    "Te responderemos cuando dispongamos "
    "de los datos confirmados.\n\n"
    "Un saludo.\n"
    "AMPA"
)


def clasificar_correo(
    correo,
    prompts,
):
    """Clasifica un correo en cinco categorías."""

    prompt = (
        prompts[
            "reglas"
        ]
        + "\n\n"
        + prompts[
            "clasificacion"
        ]
    )

    contenido = json.dumps(
        {
            "remitente": correo.get(
                "remitente",
                "",
            ),
            "asunto": correo.get(
                "asunto",
                "",
            ),
            "cuerpo": correo.get(
                "cuerpo",
                "",
            ),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(
        prompt,
        contenido,
    )

    if not isinstance(
        datos,
        dict,
    ):
        return {
            "clasificacion": (
                "no_clasificado"
            ),
            "resumen": (
                "El LLM no devolvió "
                "JSON válido."
            ),
        }

    clasificacion = (
        datos.get(
            "clasificacion"
        )
        or ""
    ).strip().lower()

    if (
        clasificacion
        not in CLASIFICACIONES
    ):
        clasificacion = (
            "no_clasificado"
        )

    return {
        "clasificacion": clasificacion,
        "resumen": (
            datos.get(
                "resumen"
            )
            or "Correo sin resumen"
        ).strip(),
    }


def contexto_rag_disponible(
    contexto_rag,
):
    """Indica si el RAG devolvió antecedentes."""

    if not contexto_rag:
        return False

    inicios_sin_contexto = [
        "No hay antecedentes",
        "No se encontraron correos",
        "No se pudo procesar",
    ]

    return not any(
        contexto_rag.startswith(
            inicio
        )
        for inicio
        in inicios_sin_contexto
    )


def redactar_borrador(
    correo,
    prompts,
    tipo="respuesta",
    contexto_rag="",
    disponibilidad=None,
):
    """Crea el asunto y el cuerpo de un borrador."""

    disponibilidad = (
        disponibilidad
        or {
            "opciones": []
        }
    )

    if (
        tipo == "respuesta"
        and not contexto_rag_disponible(
            contexto_rag
        )
    ):
        return {
            "asunto": (
                "Re: "
                + correo.get(
                    "asunto",
                    "",
                )
            ),
            "cuerpo": RESPUESTA_NEUTRAL,
            "modo": "neutral_sin_rag",
        }

    prompt = (
        prompts[
            "reglas"
        ]
        + "\n\n"
        + prompts[
            "redaccion"
        ]
    )

    contenido = json.dumps(
        {
            "tipo": tipo,
            "correo": {
                "remitente": correo.get(
                    "remitente",
                    "",
                ),
                "asunto": correo.get(
                    "asunto",
                    "",
                ),
                "cuerpo": correo.get(
                    "cuerpo",
                    "",
                ),
            },
            "contexto_rag": (
                contexto_rag
            ),
            "disponibilidad": (
                disponibilidad.get(
                    "opciones",
                    [],
                )
            ),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(
        prompt,
        contenido,
    )

    if not isinstance(
        datos,
        dict,
    ):
        return {
            "asunto": (
                "Re: "
                + correo.get(
                    "asunto",
                    "",
                )
            ),
            "cuerpo": RESPUESTA_NEUTRAL,
            "modo": "neutral_error_llm",
        }

    asunto = (
        datos.get(
            "asunto"
        )
        or (
            "Re: "
            + correo.get(
                "asunto",
                "",
            )
        )
    ).strip()

    cuerpo = limpiar_texto(
        datos.get(
            "cuerpo"
        )
        or ""
    )

    if not cuerpo:
        cuerpo = RESPUESTA_NEUTRAL

    return {
        "asunto": asunto,
        "cuerpo": cuerpo,
        "modo": "llm",
    }


def extraer_reunion(
    correo,
    prompts,
):
    """Extrae tipo, motivo y opciones."""

    prompt = (
        prompts[
            "reglas"
        ]
        + "\n\n"
        + prompts[
            "reunion"
        ]
    )

    contenido = json.dumps(
        {
            "asunto": correo.get(
                "asunto",
                "",
            ),
            "cuerpo": correo.get(
                "cuerpo",
                "",
            ),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(
        prompt,
        contenido,
    )

    if not isinstance(
        datos,
        dict,
    ):
        return {
            "tipo": "no_claro",
            "motivo": "",
            "duracion_minutos": (
                DEFAULT_MEETING_MINUTES
            ),
            "opciones": [],
        }

    tipo = (
        datos.get(
            "tipo"
        )
        or ""
    ).strip().lower()

    if tipo not in TIPOS_REUNION:
        tipo = "no_claro"

    duracion = datos.get(
        "duracion_minutos",
        DEFAULT_MEETING_MINUTES,
    )

    try:
        duracion = int(
            duracion
        )
    except (
        TypeError,
        ValueError,
    ):
        duracion = (
            DEFAULT_MEETING_MINUTES
        )

    opciones = datos.get(
        "opciones"
    )

    if not isinstance(
        opciones,
        list,
    ):
        opciones = []

    return {
        "tipo": tipo,
        "motivo": (
            datos.get(
                "motivo"
            )
            or ""
        ).strip(),
        "duracion_minutos": max(
            15,
            min(
                duracion,
                180,
            ),
        ),
        "opciones": opciones,
    }


def crear_resumen_whatsapp(
    correo,
    prompts,
):
    """Genera un resumen máximo de cinco líneas."""

    prompt = (
        prompts[
            "reglas"
        ]
        + "\n\n"
        + prompts[
            "whatsapp"
        ]
    )

    contenido = json.dumps(
        {
            "asunto": correo.get(
                "asunto",
                "",
            ),
            "cuerpo": correo.get(
                "cuerpo",
                "",
            ),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(
        prompt,
        contenido,
    )

    if not isinstance(
        datos,
        dict,
    ):
        return {
            "tipo_riesgo": (
                "no_especificado"
            ),
            "resumen": (
                "Posible incidencia de seguridad. "
                "Revisar el correo original."
            ),
        }

    resumen = (
        datos.get(
            "resumen"
        )
        or (
            "Posible incidencia de seguridad. "
            "Revisar el correo original."
        )
    ).strip()

    lineas = resumen.splitlines()[
        :5
    ]

    return {
        "tipo_riesgo": (
            datos.get(
                "tipo_riesgo"
            )
            or "no_especificado"
        ).strip(),
        "resumen": "\n".join(
            lineas
        ),
    }


funciones = {
    "obtener_correos_no_leidos": (
        obtener_correos_no_leidos
    ),
    "clasificar_correo": (
        clasificar_correo
    ),
    "consultar_antecedentes_gmail": (
        consultar_antecedentes_gmail
    ),
    "redactar_borrador": (
        redactar_borrador
    ),
    "crear_borrador": (
        crear_borrador
    ),
    "marcar_como_leido": (
        marcar_como_leido
    ),
    "extraer_reunion": (
        extraer_reunion
    ),
    "consultar_disponibilidad": (
        consultar_disponibilidad
    ),
    "crear_resumen_whatsapp": (
        crear_resumen_whatsapp
    ),
    "enviar_whatsapp": (
        enviar_whatsapp
    ),
    "registrar_correo": (
        registrar_correo
    ),
}
