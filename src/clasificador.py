"""Clasificación de correos mediante una llamada simple al LLM."""

import json

from src.llm import preguntar_json


CLASIFICACIONES = {
    "informativo",
    "necesita_respuesta",
    "reunion",
    "urgente_seguridad",
    "no_clasificado",
}


def clasificar_correo(correo, prompts):
    """Clasifica un correo en una de las cinco categorías."""

    prompt = (
        prompts["reglas"]
        + "\n\n"
        + prompts["clasificacion"]
    )

    contenido = json.dumps(
        {
            "remitente": correo.get("remitente", ""),
            "asunto": correo.get("asunto", ""),
            "cuerpo": correo.get("cuerpo", ""),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(prompt, contenido)

    if not isinstance(datos, dict):
        return {
            "clasificacion": "no_clasificado",
            "resumen": "El LLM no devolvió JSON válido.",
        }

    clasificacion = (
        datos.get("clasificacion")
        or ""
    ).strip().lower()

    if clasificacion not in CLASIFICACIONES:
        clasificacion = "no_clasificado"

    return {
        "clasificacion": clasificacion,
        "resumen": (
            datos.get("resumen")
            or "Correo sin resumen"
        ).strip(),
    }
