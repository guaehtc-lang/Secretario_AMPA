"""Configuración central del proyecto Secretario AMPA.

Lee las variables del archivo .env y las deja disponibles para
el resto de la aplicación.
"""

import os
from dotenv import load_dotenv


load_dotenv(override=True)


def leer_bool(nombre, valor_defecto=False):
    """Convierte una variable del .env en True o False."""

    valor = os.getenv(nombre, str(valor_defecto))
    return valor.strip().lower() == "true"


# Entorno
APP_ENV = os.getenv("APP_ENV", "pruebas")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Madrid")

# Modelo LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or "https://api.groq.com/openai/v1"
)
LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "llama-3.3-70b-versatile",
)
LLM_TEMPERATURE = float(
    os.getenv("LLM_TEMPERATURE", "0.2")
)
LLM_MAX_TOKENS = int(
    os.getenv("LLM_MAX_TOKENS", "1200")
)

# Gmail
EXPECTED_GMAIL_ADDRESS = os.getenv(
    "EXPECTED_GMAIL_ADDRESS",
    "",
).lower()

GOOGLE_CREDENTIALS_FILE = os.getenv(
    "GOOGLE_CREDENTIALS_FILE",
    "credentials.json",
)

GMAIL_TOKEN_FILE = os.getenv(
    "GMAIL_TOKEN_FILE",
    "token_gmail.json",
)

GMAIL_ACCESS_MODE = os.getenv(
    "GMAIL_ACCESS_MODE",
    "lectura",
).lower()

GMAIL_QUERY = os.getenv(
    "GMAIL_QUERY",
    "is:unread in:inbox",
)

MAX_EMAILS_PER_RUN = int(
    os.getenv("MAX_EMAILS_PER_RUN", "5")
)

# Acciones permitidas
ALLOW_EMAIL_SEND = leer_bool(
    "ALLOW_EMAIL_SEND",
    False,
)

ALLOW_CREATE_DRAFTS = leer_bool(
    "ALLOW_CREATE_DRAFTS",
    False,
)

ALLOW_MODIFY_LABELS = leer_bool(
    "ALLOW_MODIFY_LABELS",
    False,
)

# Archivos locales
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "data/secretario_ampa.db",
)

SYSTEM_PROMPT_PATH = os.getenv(
    "SYSTEM_PROMPT_PATH",
    "prompts/system_prompt_secretario.md",
)

MAX_BODY_CHARS = int(
    os.getenv("MAX_BODY_CHARS", "8000")
)


# Protección crítica: esta aplicación nunca envía correos.
if ALLOW_EMAIL_SEND:
    raise ValueError(
        "ALLOW_EMAIL_SEND debe permanecer en false. "
        "El agente no puede enviar correos."
    )

if GMAIL_ACCESS_MODE not in ["lectura", "gestion"]:
    raise ValueError(
        "GMAIL_ACCESS_MODE debe ser lectura o gestion"
    )
