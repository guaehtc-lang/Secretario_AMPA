"""Parámetros del proyecto cargados desde .env."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(override=True)


# LLM
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "https://api.groq.com/openai/v1",
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "llama-3.1-8b-instant",
)
LLM_TEMPERATURE = float(
    os.getenv("LLM_TEMPERATURE", "0")
)
LLM_MAX_TOKENS = int(
    os.getenv("LLM_MAX_TOKENS", "1200")
)

# Composio
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")
COMPOSIO_USER_ID = os.getenv(
    "COMPOSIO_USER_ID",
    "secretario_ampa_pruebas",
)
EXPECTED_GMAIL_ADDRESS = os.getenv(
    "EXPECTED_GMAIL_ADDRESS",
    "",
)

# Gmail
GMAIL_QUERY = os.getenv(
    "GMAIL_QUERY",
    "is:unread in:inbox",
)
MAX_EMAILS_PER_RUN = int(
    os.getenv("MAX_EMAILS_PER_RUN", "20")
)
ALLOW_CREATE_DRAFTS = (
    os.getenv("ALLOW_CREATE_DRAFTS", "true").lower()
    == "true"
)
ALLOW_MARK_AS_READ = (
    os.getenv("ALLOW_MARK_AS_READ", "true").lower()
    == "true"
)
ALLOW_EMAIL_SEND = (
    os.getenv("ALLOW_EMAIL_SEND", "false").lower()
    == "true"
)
GMAIL_MARK_READ_ACTION = os.getenv(
    "GMAIL_MARK_READ_ACTION",
    "GMAIL_MODIFY_EMAIL_LABELS",
)

# Calendar
TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid")
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")
DEFAULT_MEETING_MINUTES = int(
    os.getenv("DEFAULT_MEETING_MINUTES", "60")
)
ALLOW_CREATE_EVENTS = (
    os.getenv("ALLOW_CREATE_EVENTS", "false").lower()
    == "true"
)

# RAG
RAG_YEARS = int(os.getenv("RAG_YEARS", "1"))
RAG_MAX_EMAILS = int(
    os.getenv("RAG_MAX_EMAILS", "200")
)
RAG_RESULTS = int(os.getenv("RAG_RESULTS", "3"))
RAG_MIN_SIMILARITY = float(
    os.getenv("RAG_MIN_SIMILARITY", "0.20")
)

# WhatsApp
WHATSAPP_MODE = os.getenv(
    "WHATSAPP_MODE",
    "simulado",
).lower()
WHATSAPP_RECIPIENTS = [
    elemento.strip()
    for elemento in os.getenv(
        "WHATSAPP_RECIPIENTS",
        "Presidencia,Secretaría",
    ).split(",")
    if elemento.strip()
]

# Servicio
ORDINARY_START_HOUR = int(
    os.getenv("ORDINARY_START_HOUR", "6")
)
ORDINARY_END_HOUR = int(
    os.getenv("ORDINARY_END_HOUR", "23")
)
SCHEDULER_CHECK_SECONDS = int(
    os.getenv("SCHEDULER_CHECK_SECONDS", "60")
)

# Salida
SHOW_STEPS = (
    os.getenv("SHOW_STEPS", "true").lower()
    == "true"
)

# Rutas
PROMPTS_DIR = Path("prompts")
DATABASE_PATH = Path(
    "data/memoria/secretario_ampa.db"
)
RAG_PATH = Path(
    "data/rag/correos_historicos.jsonl"
)
WHATSAPP_LOG_PATH = Path(
    "data/whatsapp/alertas_simuladas.jsonl"
)


if ALLOW_EMAIL_SEND:
    raise ValueError(
        "ALLOW_EMAIL_SEND debe permanecer en false."
    )

if ALLOW_CREATE_EVENTS:
    raise ValueError(
        "V0.3 no crea eventos. "
        "ALLOW_CREATE_EVENTS debe permanecer en false."
    )
