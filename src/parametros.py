"""Parámetros generales y credenciales del proyecto.

Modifica este archivo para cambiar el modelo, temperatura,
límites, horario o configuración del RAG.

Las claves secretas se guardan en .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(override=True)


# LLM
API_KEY = os.getenv(
    "LLM_API_KEY",
    "",
)

BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://api.groq.com/openai/v1",
)

MODELO = os.getenv(
    "LLM_MODEL",
    "llama-3.1-8b-instant",
)

TEMPERATURA = float(
    os.getenv(
        "LLM_TEMPERATURE",
        "0",
    )
)

MAX_TOKENS = int(
    os.getenv(
        "LLM_MAX_TOKENS",
        "700",
    )
)

MAX_PASOS = int(
    os.getenv(
        "MAX_PASOS",
        "8",
    )
)

MOSTRAR_PASOS = (
    os.getenv(
        "MOSTRAR_PASOS",
        "false",
    ).lower()
    == "true"
)


# Composio
COMPOSIO_API_KEY = os.getenv(
    "COMPOSIO_API_KEY",
    "",
)

COMPOSIO_USER_ID = os.getenv(
    "COMPOSIO_USER_ID",
    "secretario_ampa_pruebas",
)


# Gmail
GMAIL_QUERY = os.getenv(
    "GMAIL_QUERY",
    "is:unread in:inbox",
)

MAX_CORREOS_BUSQUEDA = int(
    os.getenv(
        "MAX_CORREOS_BUSQUEDA",
        "10",
    )
)


# Google Calendar
TIMEZONE = os.getenv(
    "TIMEZONE",
    "Europe/Madrid",
)

CALENDAR_ID = os.getenv(
    "CALENDAR_ID",
    "primary",
)


# Acciones permitidas
ALLOW_EMAIL_SEND = False

ALLOW_CREATE_DRAFTS = (
    os.getenv(
        "ALLOW_CREATE_DRAFTS",
        "true",
    ).lower()
    == "true"
)

ALLOW_CREATE_EVENTS = (
    os.getenv(
        "ALLOW_CREATE_EVENTS",
        "true",
    ).lower()
    == "true"
)


# RAG
RAG_ANIOS_HISTORIAL = int(
    os.getenv(
        "RAG_ANIOS_HISTORIAL",
        "1",
    )
)

RAG_MAX_CORREOS = int(
    os.getenv(
        "RAG_MAX_CORREOS",
        "200",
    )
)

RAG_RESULTADOS = int(
    os.getenv(
        "RAG_RESULTADOS",
        "3",
    )
)

RAG_SIMILITUD_MINIMA = float(
    os.getenv(
        "RAG_SIMILITUD_MINIMA",
        "0.25",
    )
)

RAG_SOLO_ENVIADOS = (
    os.getenv(
        "RAG_SOLO_ENVIADOS",
        "true",
    ).lower()
    == "true"
)


# Servicio
HORA_INICIO = int(
    os.getenv(
        "HORA_INICIO",
        "6",
    )
)

HORA_FIN = int(
    os.getenv(
        "HORA_FIN",
        "23",
    )
)

SEGUNDOS_COMPROBACION = int(
    os.getenv(
        "SEGUNDOS_COMPROBACION",
        "60",
    )
)


# Rutas
RUTA_PROMPT = Path(
    "prompts/prompt_agente.txt"
)

RUTA_RAG = Path(
    "data/rag/correos_historicos.jsonl"
)

RUTA_BD = Path(
    "data/memoria/secretario_ampa.db"
)


if ALLOW_EMAIL_SEND:
    raise ValueError(
        "El envío directo de correos debe permanecer bloqueado."
    )
