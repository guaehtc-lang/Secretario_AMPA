"""Catálogo interno de tools controladas por Python.

El LLM no recibe estas tools.
"""

tools = {
    "obtener_correos_no_leidos": {
        "area": "gmail",
        "descripcion": (
            "Obtiene correos no leídos "
            "por orden cronológico."
        ),
    },
    "clasificar_correo": {
        "area": "llm",
        "descripcion": (
            "Clasifica el correo "
            "en cinco categorías."
        ),
    },
    "consultar_antecedentes_gmail": {
        "area": "rag",
        "descripcion": (
            "Busca correos históricos "
            "similares en el RAG local."
        ),
    },
    "redactar_borrador": {
        "area": "llm",
        "descripcion": (
            "Redacta un borrador "
            "con contexto controlado."
        ),
    },
    "crear_borrador": {
        "area": "gmail",
        "descripcion": (
            "Crea un borrador sin enviarlo."
        ),
    },
    "enviar_borrador": {
        "area": "gmail",
        "descripcion": (
            "Envía un borrador únicamente "
            "tras autorización en Telegram."
        ),
    },
    "marcar_como_leido": {
        "area": "gmail",
        "descripcion": (
            "Quita la etiqueta UNREAD "
            "tras completar la acción."
        ),
    },
    "extraer_reunion": {
        "area": "llm",
        "descripcion": (
            "Extrae tipo, motivo, "
            "fechas y horas."
        ),
    },
    "consultar_disponibilidad": {
        "area": "calendar",
        "descripcion": (
            "Consulta huecos "
            "sin crear eventos."
        ),
    },
    "crear_evento_reunion": {
        "area": "calendar",
        "descripcion": (
            "Crea un evento interno únicamente "
            "cuando la reunión está confirmada."
        ),
    },
    "crear_resumen_telegram": {
        "area": "llm",
        "descripcion": (
            "Resume una urgencia "
            "en un máximo de dos líneas."
        ),
    },
    "enviar_alerta_telegram": {
        "area": "telegram",
        "descripcion": (
            "Envía la alerta y abre "
            "el flujo de autorización."
        ),
    },
    "enviar_borrador_telegram": {
        "area": "telegram",
        "descripcion": (
            "Envía el borrador y solicita "
            "la autorización final."
        ),
    },
    "enviar_confirmacion_telegram": {
        "area": "telegram",
        "descripcion": (
            "Confirma por Telegram "
            "el resultado de la decisión."
        ),
    },
    "obtener_actualizaciones": {
        "area": "telegram",
        "descripcion": (
            "Consulta las pulsaciones "
            "pendientes del bot."
        ),
    },
    "callback_autorizado": {
        "area": "telegram",
        "descripcion": (
            "Comprueba que el botón procede "
            "del chat autorizado."
        ),
    },
    "datos_callback": {
        "area": "telegram",
        "descripcion": (
            "Extrae la acción y el código "
            "de una pulsación."
        ),
    },
    "responder_callback": {
        "area": "telegram",
        "descripcion": (
            "Cierra la espera visual "
            "del botón pulsado."
        ),
    },
    "retirar_botones": {
        "area": "telegram",
        "descripcion": (
            "Retira botones ya utilizados."
        ),
    },
    "obtener_alerta_por_codigo": {
        "area": "memoria",
        "descripcion": (
            "Busca la urgencia pendiente "
            "relacionada con un botón."
        ),
    },
    "actualizar_alerta": {
        "area": "memoria",
        "descripcion": (
            "Actualiza el estado persistente "
            "de una urgencia."
        ),
    },
    "obtener_estado": {
        "area": "memoria",
        "descripcion": (
            "Obtiene el offset persistente "
            "de Telegram."
        ),
    },
    "guardar_estado": {
        "area": "memoria",
        "descripcion": (
            "Guarda el offset persistente "
            "de Telegram."
        ),
    },
    "obtener_registro_correo": {
        "area": "memoria",
        "descripcion": (
            "Obtiene el estado guardado "
            "de un correo."
        ),
    },
    "registrar_correo": {
        "area": "memoria",
        "descripcion": (
            "Guarda el resultado "
            "y evita duplicados."
        ),
    },
}
