"""Extracción de datos de reuniones mediante LLM."""

import json

from src.llm import preguntar_json
from src.parametros import DEFAULT_MEETING_MINUTES


TIPOS_REUNION = {
    "solicitud",
    "cambio",
    "confirmacion",
    "rechazo",
    "no_claro",
}


def extraer_reunion(correo, prompts):
    """Extrae tipo, motivo y opciones de una reunión."""

    prompt = (
        prompts["reglas"]
        + "\n\n"
        + prompts["reunion"]
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
            "tipo": "no_claro",
            "motivo": "",
            "duracion_minutos": (
                DEFAULT_MEETING_MINUTES
            ),
            "opciones": [],
        }

    tipo = (datos.get("tipo") or "").strip().lower()

    if tipo not in TIPOS_REUNION:
        tipo = "no_claro"

    duracion = datos.get(
        "duracion_minutos",
        DEFAULT_MEETING_MINUTES,
    )

    try:
        duracion = int(duracion)
    except (TypeError, ValueError):
        duracion = DEFAULT_MEETING_MINUTES

    return {
        "tipo": tipo,
        "motivo": (
            datos.get("motivo")
            or ""
        ).strip(),
        "duracion_minutos": max(15, min(duracion, 180)),
        "opciones": (
            datos.get("opciones")
            if isinstance(datos.get("opciones"), list)
            else []
        ),
    }
