"""Flujo principal controlado por Python."""

from src.parametros import SHOW_STEPS


def mostrar(
    bloque,
    mensaje,
):
    """Muestra los pasos del agente."""

    if SHOW_STEPS:
        print(
            f"[{bloque}] {mensaje}"
        )


def registrar(
    funciones,
    correo,
    clasificacion,
    resumen,
    accion,
    estado_gmail,
    draft_id="",
    requiere_revision=False,
    error="",
    resultado=None,
):
    """Registra un correo en SQLite."""

    return funciones[
        "registrar_correo"
    ](
        message_id=correo[
            "message_id"
        ],
        clasificacion=clasificacion,
        resumen=resumen,
        accion=accion,
        estado_gmail=estado_gmail,
        draft_id=draft_id,
        requiere_revision=(
            requiere_revision
        ),
        error=error,
        resultado=resultado,
    )


def procesar_pendiente_lectura(
    correo,
    funciones,
):
    """Reintenta únicamente marcar como leído."""

    registro = correo.get(
        "_registro_previo"
    )

    mostrar(
        "GMAIL",
        "Reintentando marcar como leído",
    )

    leido = funciones[
        "marcar_como_leido"
    ](
        correo[
            "message_id"
        ]
    )

    if leido.get(
        "ok"
    ):
        accion = (
            registro.get(
                "accion",
                "",
            ).replace(
                "_pendiente_leido",
                "",
            )
        )
        estado_gmail = "leido"
        error = ""

    else:
        accion = registro.get(
            "accion",
            "pendiente_marcar_leido",
        )
        estado_gmail = (
            "pendiente_marcar_leido"
        )
        error = str(
            leido
        )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion=registro.get(
            "clasificacion",
            "no_clasificado",
        ),
        resumen=registro.get(
            "resumen",
            "",
        ),
        accion=accion,
        estado_gmail=estado_gmail,
        draft_id=registro.get(
            "draft_id",
            "",
        ),
        requiere_revision=registro.get(
            "requiere_revision",
            False,
        ),
        error=error,
        resultado={
            "reintento_marcar_leido": (
                leido
            ),
        },
    )


def procesar_informativo(
    correo,
    clasificacion,
    funciones,
):
    """Registra un informativo y lo mantiene no leído."""

    mostrar(
        "ACCIÓN",
        "Informativo: se mantiene no leído",
    )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="informativo",
        resumen=clasificacion[
            "resumen"
        ],
        accion="registrado_sin_accion",
        estado_gmail="no_leido",
        requiere_revision=False,
    )


def procesar_no_clasificado(
    correo,
    clasificacion,
    funciones,
):
    """Deja el correo para revisión humana."""

    mostrar(
        "ACCIÓN",
        "No clasificado: revisión humana",
    )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="no_clasificado",
        resumen=clasificacion[
            "resumen"
        ],
        accion="pendiente_revision",
        estado_gmail="no_leido",
        requiere_revision=True,
    )


def procesar_respuesta(
    correo,
    clasificacion,
    funciones,
    prompts,
):
    """Consulta el RAG y crea un borrador."""

    mostrar(
        "RAG",
        "Consultando antecedentes",
    )

    consulta = (
        correo.get(
            "asunto",
            "",
        )
        + "\n"
        + correo.get(
            "cuerpo",
            "",
        )
    )

    contexto = funciones[
        "consultar_antecedentes_gmail"
    ](
        consulta
    )

    mostrar(
        "LLM",
        "Redactando borrador",
    )

    borrador = funciones[
        "redactar_borrador"
    ](
        correo=correo,
        prompts=prompts,
        tipo="respuesta",
        contexto_rag=contexto,
    )

    mostrar(
        "GMAIL",
        "Creando borrador",
    )

    creado = funciones[
        "crear_borrador"
    ](
        message_id=correo[
            "message_id"
        ],
        asunto=borrador[
            "asunto"
        ],
        cuerpo=borrador[
            "cuerpo"
        ],
    )

    if not creado.get(
        "ok"
    ):
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion=(
                "necesita_respuesta"
            ),
            resumen=clasificacion[
                "resumen"
            ],
            accion="error_borrador",
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(
                creado
            ),
            resultado={
                "rag": contexto,
                "borrador": borrador,
                "gmail": creado,
            },
        )

    mostrar(
        "GMAIL",
        "Marcando correo como leído",
    )

    leido = funciones[
        "marcar_como_leido"
    ](
        correo[
            "message_id"
        ]
    )

    if leido.get(
        "ok"
    ):
        accion = "borrador_creado"
        estado_gmail = "leido"
        error = ""

    else:
        accion = (
            "borrador_creado_pendiente_leido"
        )
        estado_gmail = (
            "pendiente_marcar_leido"
        )
        error = str(
            leido
        )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion=(
            "necesita_respuesta"
        ),
        resumen=clasificacion[
            "resumen"
        ],
        accion=accion,
        estado_gmail=estado_gmail,
        draft_id=creado.get(
            "draft_id",
            "",
        ),
        requiere_revision=True,
        error=error,
        resultado={
            "rag": contexto,
            "borrador": borrador,
            "gmail": creado,
            "marcar_leido": leido,
        },
    )


def procesar_reunion(
    correo,
    clasificacion,
    funciones,
    prompts,
):
    """Consulta Calendar y crea un borrador."""

    mostrar(
        "LLM",
        "Extrayendo datos de la reunión",
    )

    reunion = funciones[
        "extraer_reunion"
    ](
        correo,
        prompts,
    )

    if reunion[
        "tipo"
    ] in [
        "confirmacion",
        "rechazo",
    ]:
        mostrar(
            "REUNIÓN",
            (
                reunion[
                    "tipo"
                ]
                + " registrada "
                "sin crear evento"
            ),
        )

        mostrar(
            "GMAIL",
            "Marcando correo como leído",
        )

        leido = funciones[
            "marcar_como_leido"
        ](
            correo[
                "message_id"
            ]
        )

        if leido.get(
            "ok"
        ):
            accion = (
                "reunion_"
                + reunion[
                    "tipo"
                ]
            )
            estado_gmail = "leido"
            error = ""

        else:
            accion = (
                "reunion_"
                + reunion[
                    "tipo"
                ]
                + "_pendiente_leido"
            )
            estado_gmail = (
                "pendiente_marcar_leido"
            )
            error = str(
                leido
            )

        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="reunion",
            resumen=clasificacion[
                "resumen"
            ],
            accion=accion,
            estado_gmail=estado_gmail,
            requiere_revision=False,
            error=error,
            resultado={
                "reunion": reunion,
                "marcar_leido": leido,
            },
        )

    if (
        reunion[
            "tipo"
        ] == "no_claro"
        or not reunion[
            "opciones"
        ]
    ):
        mostrar(
            "REUNIÓN",
            "Faltan datos para consultar Calendar",
        )

        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="reunion",
            resumen=clasificacion[
                "resumen"
            ],
            accion=(
                "reunion_pendiente_revision"
            ),
            estado_gmail="no_leido",
            requiere_revision=True,
            resultado={
                "reunion": reunion,
            },
        )

    mostrar(
        "CALENDAR",
        "Consultando disponibilidad",
    )

    disponibilidad = funciones[
        "consultar_disponibilidad"
    ](
        opciones=reunion[
            "opciones"
        ],
        duracion_minutos=reunion[
            "duracion_minutos"
        ],
    )

    if not disponibilidad.get(
        "ok",
        False,
    ):
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="reunion",
            resumen=clasificacion[
                "resumen"
            ],
            accion="error_calendar",
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(
                disponibilidad
            ),
            resultado={
                "reunion": reunion,
                "disponibilidad": (
                    disponibilidad
                ),
            },
        )

    mostrar(
        "LLM",
        "Redactando propuesta de reunión",
    )

    borrador = funciones[
        "redactar_borrador"
    ](
        correo=correo,
        prompts=prompts,
        tipo="reunion",
        disponibilidad=disponibilidad,
    )

    mostrar(
        "GMAIL",
        "Creando borrador de reunión",
    )

    creado = funciones[
        "crear_borrador"
    ](
        message_id=correo[
            "message_id"
        ],
        asunto=borrador[
            "asunto"
        ],
        cuerpo=borrador[
            "cuerpo"
        ],
    )

    if not creado.get(
        "ok"
    ):
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="reunion",
            resumen=clasificacion[
                "resumen"
            ],
            accion=(
                "error_borrador_reunion"
            ),
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(
                creado
            ),
            resultado={
                "reunion": reunion,
                "disponibilidad": (
                    disponibilidad
                ),
                "borrador": borrador,
                "gmail": creado,
            },
        )

    mostrar(
        "GMAIL",
        "Marcando correo como leído",
    )

    leido = funciones[
        "marcar_como_leido"
    ](
        correo[
            "message_id"
        ]
    )

    if leido.get(
        "ok"
    ):
        accion = (
            "borrador_reunion_creado"
        )
        estado_gmail = "leido"
        error = ""

    else:
        accion = (
            "borrador_reunion_creado_"
            "pendiente_leido"
        )
        estado_gmail = (
            "pendiente_marcar_leido"
        )
        error = str(
            leido
        )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="reunion",
        resumen=clasificacion[
            "resumen"
        ],
        accion=accion,
        estado_gmail=estado_gmail,
        draft_id=creado.get(
            "draft_id",
            "",
        ),
        requiere_revision=True,
        error=error,
        resultado={
            "reunion": reunion,
            "disponibilidad": (
                disponibilidad
            ),
            "borrador": borrador,
            "gmail": creado,
            "marcar_leido": leido,
        },
    )


def procesar_urgencia(
    correo,
    clasificacion,
    funciones,
    prompts,
):
    """Genera una alerta y marca leído si funciona."""

    mostrar(
        "LLM",
        "Generando resumen de WhatsApp",
    )

    alerta = funciones[
        "crear_resumen_whatsapp"
    ](
        correo,
        prompts,
    )

    mostrar(
        "WHATSAPP",
        "Registrando alerta simulada",
    )

    enviado = funciones[
        "enviar_whatsapp"
    ](
        message_id=correo[
            "message_id"
        ],
        resumen=alerta[
            "resumen"
        ],
        tipo_riesgo=alerta[
            "tipo_riesgo"
        ],
    )

    if enviado.get(
        "ok"
    ):
        mostrar(
            "GMAIL",
            "Marcando correo como leído",
        )

        leido = funciones[
            "marcar_como_leido"
        ](
            correo[
                "message_id"
            ]
        )

    else:
        leido = {
            "ok": False,
            "estado": (
                "no_marcado_por_fallo_whatsapp"
            ),
        }

    if (
        enviado.get(
            "ok"
        )
        and leido.get(
            "ok"
        )
    ):
        accion = (
            "alerta_whatsapp_registrada"
        )
        estado_gmail = "leido"
        error = ""

    elif enviado.get(
        "ok"
    ):
        accion = (
            "alerta_whatsapp_registrada_"
            "pendiente_leido"
        )
        estado_gmail = (
            "pendiente_marcar_leido"
        )
        error = str(
            leido
        )

    else:
        accion = "error_whatsapp"
        estado_gmail = "no_leido"
        error = str(
            enviado
        )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion=(
            "urgente_seguridad"
        ),
        resumen=clasificacion[
            "resumen"
        ],
        accion=accion,
        estado_gmail=estado_gmail,
        requiere_revision=(
            not enviado.get(
                "ok"
            )
        ),
        error=error,
        resultado={
            "alerta": alerta,
            "whatsapp": enviado,
            "marcar_leido": leido,
        },
    )


def procesar_correo(
    correo,
    tools,
    funciones,
    prompts,
):
    """Clasifica y aplica un único flujo."""

    registro_previo = correo.get(
        "_registro_previo"
    )

    if (
        registro_previo
        and registro_previo.get(
            "estado_gmail"
        )
        == "pendiente_marcar_leido"
    ):
        return procesar_pendiente_lectura(
            correo,
            funciones,
        )

    mostrar(
        "CORREO",
        correo.get(
            "asunto",
            "(sin asunto)",
        ),
    )

    mostrar(
        "LLM",
        "Clasificando correo",
    )

    clasificacion = funciones[
        "clasificar_correo"
    ](
        correo,
        prompts,
    )

    categoria = clasificacion[
        "clasificacion"
    ]

    mostrar(
        "CLASIFICACIÓN",
        categoria,
    )

    try:
        if categoria == "informativo":
            return procesar_informativo(
                correo,
                clasificacion,
                funciones,
            )

        if (
            categoria
            == "necesita_respuesta"
        ):
            return procesar_respuesta(
                correo,
                clasificacion,
                funciones,
                prompts,
            )

        if categoria == "reunion":
            return procesar_reunion(
                correo,
                clasificacion,
                funciones,
                prompts,
            )

        if (
            categoria
            == "urgente_seguridad"
        ):
            return procesar_urgencia(
                correo,
                clasificacion,
                funciones,
                prompts,
            )

        return procesar_no_clasificado(
            correo,
            clasificacion,
            funciones,
        )

    except Exception as error:
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion=categoria,
            resumen=clasificacion.get(
                "resumen",
                (
                    "Error durante "
                    "el procesamiento"
                ),
            ),
            accion=(
                "error_"
                + categoria
            ),
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(
                error
            ),
        )


def ejecutar_agente(
    tools,
    funciones,
    prompts,
):
    """Procesa todos los correos pendientes."""

    faltan = [
        nombre
        for nombre in tools
        if nombre not in funciones
    ]

    if faltan:
        return {
            "ok": False,
            "estado": "faltan_funciones",
            "funciones": faltan,
        }

    mostrar(
        "GMAIL",
        "Buscando correos no leídos",
    )

    correos = funciones[
        "obtener_correos_no_leidos"
    ]()

    if not correos:
        return {
            "ok": True,
            "estado": "sin_correos_nuevos",
            "procesados": 0,
            "resultados": [],
        }

    resultados = []

    for numero, correo in enumerate(
        correos,
        start=1,
    ):
        print(
            f"\n===== CORREO "
            f"{numero}/{len(correos)} ====="
        )

        try:
            resultado = procesar_correo(
                correo=correo,
                tools=tools,
                funciones=funciones,
                prompts=prompts,
            )

        except Exception as error:
            resultado = registrar(
                funciones=funciones,
                correo=correo,
                clasificacion=(
                    "no_clasificado"
                ),
                resumen=(
                    "Error durante "
                    "el procesamiento"
                ),
                accion=(
                    "error_procesamiento"
                ),
                estado_gmail="no_leido",
                requiere_revision=True,
                error=str(
                    error
                ),
            )

        resultados.append(
            resultado
        )

    return {
        "ok": True,
        "estado": "ciclo_completado",
        "procesados": len(
            resultados
        ),
        "resultados": resultados,
    }
