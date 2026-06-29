"""Análisis de correos mediante el modelo LLM."""

import json
from pathlib import Path

from openai import OpenAI

from src import config


def crear_cliente_llm():
    """Crea el cliente de Groq."""

    if not config.LLM_API_KEY:
        raise ValueError(
            "Falta LLM_API_KEY en el archivo .env"
        )

    return OpenAI(
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL,
    )


def cargar_system_prompt():
    """Carga las instrucciones del agente desde el archivo Markdown."""

    ruta = Path(config.SYSTEM_PROMPT_PATH)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el prompt: {ruta}"
        )

    return ruta.read_text(encoding="utf-8")


def analizar_correo(correo):
    """Clasifica un correo y prepara una propuesta de actuación."""

    cliente = crear_cliente_llm()
    system_prompt = cargar_system_prompt()

    mensaje_usuario = f"""
Analiza este correo recibido.

REMITENTE:
{correo.get("remitente", "")}

DESTINATARIO:
{correo.get("destinatario", "")}

ASUNTO:
{correo.get("asunto", "")}

FECHA:
{correo.get("fecha", "")}

CUERPO:
{correo.get("cuerpo", "")}

Devuelve únicamente el objeto JSON indicado en el system prompt.
"""

    respuesta = cliente.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": mensaje_usuario,
            },
        ],
        temperature=config.LLM_TEMPERATURE,
        max_tokens=config.LLM_MAX_TOKENS,
    )

    texto = respuesta.choices[0].message.content.strip()

    # Algunos modelos añaden bloques ```json aunque se les pida JSON puro.
    if texto.startswith("```"):
        texto = texto.replace("```json", "")
        texto = texto.replace("```", "")
        texto = texto.strip()

    try:
        resultado = json.loads(texto)

    except json.JSONDecodeError as error:
        raise ValueError(
            "El modelo no ha devuelto un JSON válido:\n"
            f"{texto}"
        ) from error

    return resultado, respuesta.usage
