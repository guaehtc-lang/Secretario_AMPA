"""Catálogo interno de tools controladas por Python.

El LLM no recibe estas tools. Python decide cuándo utilizarlas.
"""


tools = {
    "obtener_correos_no_leidos": {
        "area": "gmail",
        "descripcion": (
            "Obtiene correos no leídos por orden cronológico."
        ),
    },
    "clasificar_correo": {
        "area": "llm",
        "descripcion": (
            "Clasifica en cinco categorías cerradas."
        ),
    },
    "consultar_rag": {
        "area": "rag",
        "descripcion": (
            "Recupera correos enviados similares."
        ),
    },
    "redactar_borrador": {
        "area": "llm",
        "descripcion": (
            "Redacta un borrador con contexto controlado."
        ),
    },
    "crear_borrador": {
        "area": "gmail",
        "descripcion": (
            "Crea un borrador. Nunca envía el correo."
        ),
    },
    "marcar_como_leido": {
        "area": "gmail",
        "descripcion": (
            "Quita la etiqueta UNREAD tras completar la acción."
        ),
    },
    "extraer_reunion": {
        "area": "llm",
        "descripcion": (
            "Extrae tipo, motivo, fechas y horas."
        ),
    },
    "consultar_disponibilidad": {
        "area": "calendar",
        "descripcion": (
            "Consulta huecos sin crear eventos."
        ),
    },
    "crear_resumen_whatsapp": {
        "area": "llm",
        "descripcion": (
            "Resume una urgencia en cinco líneas."
        ),
    },
    "enviar_whatsapp": {
        "area": "whatsapp",
        "descripcion": (
            "Registra una alerta simulada en V0.3."
        ),
    },
    "registrar_correo": {
        "area": "memoria",
        "descripcion": (
            "Guarda el resultado y evita duplicados."
        ),
    },
}
