"""Redacción de borradores con información controlada."""

import json

from src.llm import preguntar_json
from src.utilidades import limpiar_texto


RESPUESTA_NEUTRAL = (
    "Buenos días:\n\n"
    "Gracias por tu consulta. Estamos comprobando la "
    "información necesaria para poder darte una respuesta "
    "correcta.\n\n"
    "Te responderemos cuando dispongamos de los datos "
    "confirmados.\n\n"
    "Un saludo.\nAMPA"
)


def redactar_borrador(
    correo,
    prompts,
    tipo="respuesta",
    contexto_rag=None,
    disponibilidad=None,
):
    """Crea el asunto y el cuerpo de un borrador."""

    contexto_rag = contexto_rag or {
        "resultados": []
    }
    disponibilidad = disponibilidad or {
        "opciones": []
    }

    if (
        tipo == "respuesta"
        and not contexto_rag.get("resultados")
    ):
        return {
            "asunto": "Re: " + correo.get("asunto", ""),
            "cuerpo": RESPUESTA_NEUTRAL,
            "modo": "neutral_sin_rag",
        }

    prompt = (
        prompts["reglas"]
        + "\n\n"
        + prompts["redaccion"]
    )

    contenido = json.dumps(
        {
            "tipo": tipo,
            "correo": {
                "remitente": correo.get(
                    "remitente",
                    "",
                ),
                "asunto": correo.get("asunto", ""),
                "cuerpo": correo.get("cuerpo", ""),
            },
            "contexto_rag": contexto_rag.get(
                "resultados",
                [],
            ),
            "disponibilidad": disponibilidad.get(
                "opciones",
                [],
            ),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(prompt, contenido)

    if not isinstance(datos, dict):
        return {
            "asunto": "Re: " + correo.get("asunto", ""),
            "cuerpo": RESPUESTA_NEUTRAL,
            "modo": "neutral_error_llm",
        }

    asunto = (
        datos.get("asunto")
        or "Re: " + correo.get("asunto", "")
    ).strip()
    cuerpo = limpiar_texto(
        datos.get("cuerpo") or ""
    )

    if not cuerpo:
        cuerpo = RESPUESTA_NEUTRAL

    return {
        "asunto": asunto,
        "cuerpo": cuerpo,
        "modo": "llm",
    }
