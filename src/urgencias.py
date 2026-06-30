"""Creación del resumen de una urgencia."""

import json

from src.llm import preguntar_json


def crear_resumen_whatsapp(correo, prompts):
    """Genera un resumen máximo de cinco líneas."""

    prompt = (
        prompts["reglas"]
        + "\n\n"
        + prompts["whatsapp"]
    )

    contenido = json.dumps(
        {
            "asunto": correo.get("asunto", ""),
            "cuerpo": correo.get("cuerpo", ""),
        },
        ensure_ascii=False,
    )

    datos = preguntar_json(prompt, contenido)

    if not isinstance(datos, dict):
        return {
            "tipo_riesgo": "no_especificado",
            "resumen": (
                "Posible incidencia de seguridad. "
                "Revisar el correo original."
            ),
        }

    resumen = (
        datos.get("resumen")
        or "Posible incidencia de seguridad. "
        "Revisar el correo original."
    ).strip()

    lineas = resumen.splitlines()[:5]

    return {
        "tipo_riesgo": (
            datos.get("tipo_riesgo")
            or "no_especificado"
        ).strip(),
        "resumen": "\n".join(lineas),
    }
