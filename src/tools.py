"""Descripción de las herramientas visibles para el LLM."""

tools = [
    {
        "type": "function",
        "function": {
            "name": "leer_correo_pendiente",
            "description": (
                "Lee el correo no procesado más reciente "
                "y su hilo. Debe ser siempre la primera "
                "herramienta del ciclo."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clasificar_correo",
            "description": (
                "Valida en Python la clasificación propuesta "
                "para el correo actual. Debe ser siempre la "
                "segunda herramienta. La clasificación "
                "devuelta es obligatoria para el resto del ciclo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                    },
                    "clasificacion_propuesta": {
                        "type": "string",
                        "enum": [
                            "informativo",
                            "requiere_respuesta",
                            "solicitud_reunion",
                            "confirmacion_reunion",
                            "rechazo_reunion",
                            "urgencia_seguridad",
                            "revision_manual",
                        ],
                    },
                },
                "required": [
                    "message_id",
                    "clasificacion_propuesta",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_contexto_rag",
            "description": (
                "Busca respuestas históricas enviadas y "
                "suficientemente similares al correo actual. "
                "Usa siempre la clasificación devuelta por "
                "clasificar_correo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                    },
                    "consulta": {
                        "type": "string",
                    },
                    "clasificacion": {
                        "type": "string",
                        "enum": [
                            "requiere_respuesta",
                            "solicitud_reunion",
                            "rechazo_reunion",
                        ],
                    },
                    "limite": {
                        "type": "integer",
                        "default": 3,
                    },
                },
                "required": [
                    "message_id",
                    "consulta",
                    "clasificacion",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_borrador",
            "description": (
                "Crea un borrador, nunca lo envía. "
                "Debe llamarse después del RAG y usando "
                "la clasificación validada."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                    },
                    "asunto": {
                        "type": "string",
                    },
                    "cuerpo": {
                        "type": "string",
                    },
                    "clasificacion": {
                        "type": "string",
                        "enum": [
                            "requiere_respuesta",
                            "solicitud_reunion",
                            "rechazo_reunion",
                        ],
                    },
                },
                "required": [
                    "message_id",
                    "asunto",
                    "cuerpo",
                    "clasificacion",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_disponibilidad",
            "description": (
                "Consulta Calendar para una solicitud de reunión. "
                "En un rechazo solo puede usarse cuando Python haya "
                "validado una contrapropuesta concreta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                    },
                    "clasificacion": {
                        "type": "string",
                        "enum": [
                            "solicitud_reunion",
                            "rechazo_reunion",
                        ],
                    },
                    "opciones": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dia": {
                                    "type": "string",
                                },
                                "fecha": {
                                    "type": "string",
                                },
                                "hora_desde": {
                                    "type": "string",
                                },
                            },
                            "required": [
                                "hora_desde"
                            ],
                        },
                    },
                    "duracion_minutos": {
                        "type": "integer",
                        "default": 60,
                    },
                },
                "required": [
                    "message_id",
                    "clasificacion",
                    "opciones",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_invitacion_calendar",
            "description": (
                "Crea una invitación de Calendar para una "
                "solicitud o una contrapropuesta validada. "
                "Nunca crea eventos para un rechazo simple."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                    },
                    "clasificacion": {
                        "type": "string",
                        "enum": [
                            "solicitud_reunion",
                            "rechazo_reunion",
                        ],
                    },
                    "titulo": {
                        "type": "string",
                    },
                    "opcion": {
                        "type": "object",
                        "properties": {
                            "dia": {
                                "type": "string",
                            },
                            "fecha": {
                                "type": "string",
                            },
                            "hora_desde": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "hora_desde"
                        ],
                    },
                    "duracion_minutos": {
                        "type": "integer",
                        "default": 60,
                    },
                },
                "required": [
                    "message_id",
                    "clasificacion",
                    "titulo",
                    "opcion",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_resultado",
            "description": (
                "Registra el resultado final. Solo acepta "
                "la clasificación previamente validada por "
                "clasificar_correo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                    },
                    "clasificacion": {
                        "type": "string",
                        "enum": [
                            "informativo",
                            "requiere_respuesta",
                            "solicitud_reunion",
                            "confirmacion_reunion",
                            "rechazo_reunion",
                            "urgencia_seguridad",
                            "revision_manual",
                        ],
                    },
                    "resumen": {
                        "type": "string",
                    },
                    "acciones_realizadas": {
                        "type": "string",
                    },
                    "estado_reunion": {
                        "type": "string",
                    },
                    "requiere_revision": {
                        "type": "boolean",
                    },
                },
                "required": [
                    "message_id",
                    "clasificacion",
                    "resumen",
                    "acciones_realizadas",
                ],
            },
        },
    },
]



# Impide que el modelo añada parámetros no definidos.
for tool in tools:
    tool[
        "function"
    ][
        "parameters"
    ][
        "additionalProperties"
    ] = False
