"""Llamadas simples al modelo LLM."""

from functools import lru_cache

from openai import OpenAI

from src.parametros import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    LLM_TEMPERATURE,
)
from src.utilidades import extraer_json


@lru_cache(maxsize=1)
def obtener_cliente_llm():
    """Crea un cliente OpenAI compatible."""

    if not LLM_API_KEY:
        raise ValueError(
            "Falta LLM_API_KEY en el archivo .env."
        )

    return OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )


def preguntar_llm(prompt_sistema, contenido_usuario):
    """Realiza una llamada normal al LLM."""

    cliente = obtener_cliente_llm()

    respuesta = cliente.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt_sistema,
            },
            {
                "role": "user",
                "content": contenido_usuario,
            },
        ],
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    return respuesta.choices[0].message.content or ""


def preguntar_json(prompt_sistema, contenido_usuario):
    """Pide JSON al LLM y lo convierte a datos Python."""

    texto = preguntar_llm(
        prompt_sistema,
        contenido_usuario,
    )

    return extraer_json(texto)
