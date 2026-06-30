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

    resultado_previo = registro.get(
        "resultado",
        {},
    )

    if not isinstance(
        resultado_previo,
        dict,
    ):
        resultado_previo = {}

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
            **resultado_previo,
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
    ] == "confirmacion":
        mostrar(
            "CALENDAR",
            "Creando evento confirmado",
        )

        evento = funciones[
            "crear_evento_reunion"
        ](
            correo=correo,
            reunion=reunion,
        )

        if not evento.get(
            "ok"
        ):
            mostrar(
                "REUNIÓN",
                "No se creó el evento; "
                "el correo permanece no leído",
            )

            return registrar(
                funciones=funciones,
                correo=correo,
                clasificacion="reunion",
                resumen=clasificacion[
                    "resumen"
                ],
                accion=(
                    "reunion_confirmada_"
                    "pendiente_evento"
                ),
                estado_gmail="no_leido",
                requiere_revision=True,
                error=str(
                    evento
                ),
                resultado={
                    "reunion": reunion,
                    "evento": evento,
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
                "reunion_confirmada_"
                "evento_creado"
            )
            estado_gmail = "leido"
            requiere_revision = False
            error = ""

        else:
            accion = (
                "reunion_confirmada_"
                "evento_creado_"
                "pendiente_leido"
            )
            estado_gmail = (
                "pendiente_marcar_leido"
            )
            requiere_revision = True
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
            requiere_revision=(
                requiere_revision
            ),
            error=error,
            resultado={
                "reunion": reunion,
                "evento": evento,
                "marcar_leido": leido,
            },
        )

    if reunion[
        "tipo"
    ] == "rechazo":
        mostrar(
            "REUNIÓN",
            "Rechazo registrado sin crear evento",
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
            accion = "reunion_rechazo"
            estado_gmail = "leido"
            error = ""

        else:
            accion = (
                "reunion_rechazo_"
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
    """Crea borrador y solicita autorización por Telegram."""

    mostrar(
        "LLM",
        "Generando resumen de Telegram",
    )

    alerta = funciones[
        "crear_resumen_telegram"
    ](
        correo,
        prompts,
    )

    mostrar(
        "LLM",
        "Redactando borrador urgente",
    )

    borrador = funciones[
        "redactar_borrador"
    ](
        correo=correo,
        prompts=prompts,
        tipo="urgente",
    )

    mostrar(
        "GMAIL",
        "Creando borrador urgente",
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
                "urgente_seguridad"
            ),
            resumen=clasificacion[
                "resumen"
            ],
            accion="error_borrador_urgente",
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(
                creado
            ),
            resultado={
                "alerta": alerta,
                "borrador": borrador,
                "gmail": creado,
            },
        )

    mostrar(
        "TELEGRAM",
        "Enviando alerta y solicitud de revisión",
    )

    enviado = funciones[
        "enviar_alerta_telegram"
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
        draft_id=creado.get(
            "draft_id",
            "",
        ),
        asunto_borrador=borrador[
            "asunto"
        ],
        cuerpo_borrador=borrador[
            "cuerpo"
        ],
    )

    if not enviado.get(
        "ok"
    ):
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion=(
                "urgente_seguridad"
            ),
            resumen=clasificacion[
                "resumen"
            ],
            accion="error_telegram",
            estado_gmail="no_leido",
            draft_id=creado.get(
                "draft_id",
                "",
            ),
            requiere_revision=True,
            error=str(
                enviado
            ),
            resultado={
                "alerta": alerta,
                "borrador": borrador,
                "gmail": creado,
                "telegram": enviado,
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
            "borrador_urgente_creado_"
            "alerta_telegram_enviada"
        )
        estado_gmail = "leido"
        error = ""

    else:
        accion = (
            "borrador_urgente_creado_"
            "alerta_telegram_enviada_"
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
        clasificacion=(
            "urgente_seguridad"
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
            "alerta": alerta,
            "borrador": borrador,
            "gmail": creado,
            "telegram": enviado,
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


def actualizar_correo_desde_telegram(
    funciones,
    alerta,
    accion,
    requiere_revision,
    resultado_extra,
):
    """Actualiza el registro del correo tras una decisión."""

    registro = funciones[
        "obtener_registro_correo"
    ](
        alerta[
            "message_id"
        ]
    )

    if not registro:
        return {
            "ok": False,
            "estado": "correo_no_encontrado",
        }

    resultado = registro.get(
        "resultado",
        {},
    )

    if not isinstance(
        resultado,
        dict,
    ):
        resultado = {}

    resultado.update(
        resultado_extra
        or {}
    )

    return funciones[
        "registrar_correo"
    ](
        message_id=alerta[
            "message_id"
        ],
        clasificacion=registro.get(
            "clasificacion",
            "urgente_seguridad",
        ),
        resumen=registro.get(
            "resumen",
            "",
        ),
        accion=accion,
        estado_gmail=registro.get(
            "estado_gmail",
            "leido",
        ),
        draft_id=registro.get(
            "draft_id",
            "",
        ),
        requiere_revision=(
            requiere_revision
        ),
        error="",
        resultado=resultado,
    )


def procesar_actualizaciones_telegram(
    funciones,
):
    """Procesa botones pendientes del bot."""

    offset = funciones[
        "obtener_estado"
    ](
        "telegram_offset",
        "0",
    )

    consulta = funciones[
        "obtener_actualizaciones"
    ](
        offset
    )

    if not consulta.get(
        "ok"
    ):
        return {
            "ok": False,
            "estado": "error_consultando_telegram",
            "procesadas": 0,
            "error": consulta,
            "resultados": [],
        }

    resultados = []
    siguiente_offset = int(
        offset
        or 0
    )

    for actualizacion in consulta.get(
        "actualizaciones",
        [],
    ):
        update_id = int(
            actualizacion.get(
                "update_id",
                0,
            )
        )

        siguiente_offset = max(
            siguiente_offset,
            update_id + 1,
        )

        datos = funciones[
            "datos_callback"
        ](
            actualizacion
        )

        callback_id = datos.get(
            "callback_query_id",
            "",
        )

        if not callback_id:
            continue

        if not funciones[
            "callback_autorizado"
        ](
            actualizacion
        ):
            funciones[
                "responder_callback"
            ](
                callback_id,
                "Chat no autorizado.",
            )
            continue

        alerta = funciones[
            "obtener_alerta_por_codigo"
        ](
            datos.get(
                "codigo",
                "",
            )
        )

        if not alerta:
            funciones[
                "responder_callback"
            ](
                callback_id,
                "La alerta ya no está pendiente.",
            )
            funciones[
                "retirar_botones"
            ](
                datos.get(
                    "chat_id"
                ),
                datos.get(
                    "message_id"
                ),
            )
            continue

        estado = alerta.get(
            "resultado",
            {},
        ).get(
            "estado",
            "",
        )
        accion = datos.get(
            "accion",
            "",
        )
        codigo = datos.get(
            "codigo",
            "",
        )

        if accion in {
            "pendiente",
            "no",
        }:
            actualizado = funciones[
                "actualizar_alerta"
            ](
                message_id=alerta[
                    "message_id"
                ],
                estado="envio_rechazado",
                cambios={
                    "decision": accion,
                },
            )

            confirmacion = funciones[
                "enviar_confirmacion_telegram"
            ](
                codigo,
                (
                    "No se enviará el correo. "
                    "El borrador permanece en Gmail "
                    "para revisión manual."
                ),
            )

            actualizar_correo_desde_telegram(
                funciones=funciones,
                alerta=alerta,
                accion=(
                    "envio_urgente_rechazado"
                ),
                requiere_revision=True,
                resultado_extra={
                    "telegram_decision": actualizado,
                    "telegram_confirmacion": (
                        confirmacion
                    ),
                },
            )

            funciones[
                "responder_callback"
            ](
                callback_id,
                "Correo no autorizado.",
            )
            funciones[
                "retirar_botones"
            ](
                datos.get(
                    "chat_id"
                ),
                datos.get(
                    "message_id"
                ),
            )

            resultados.append({
                "codigo": codigo,
                "estado": "envio_rechazado",
            })
            continue

        if (
            accion == "ver"
            and estado
            == "esperando_revision_borrador"
        ):
            enviado = funciones[
                "enviar_borrador_telegram"
            ](
                alerta
            )

            if enviado.get(
                "ok"
            ):
                actualizado = funciones[
                    "actualizar_alerta"
                ](
                    message_id=alerta[
                        "message_id"
                    ],
                    estado=(
                        "esperando_autorizacion_envio"
                    ),
                    cambios={
                        "telegram_borrador": enviado,
                    },
                )

                actualizar_correo_desde_telegram(
                    funciones=funciones,
                    alerta=alerta,
                    accion=(
                        "borrador_urgente_"
                        "enviado_telegram"
                    ),
                    requiere_revision=True,
                    resultado_extra={
                        "telegram_revision": (
                            actualizado
                        ),
                    },
                )

                funciones[
                    "responder_callback"
                ](
                    callback_id,
                    "Borrador enviado.",
                )
                funciones[
                    "retirar_botones"
                ](
                    datos.get(
                        "chat_id"
                    ),
                    datos.get(
                        "message_id"
                    ),
                )

                resultados.append({
                    "codigo": codigo,
                    "estado": (
                        "esperando_autorizacion_envio"
                    ),
                })

            else:
                funciones[
                    "responder_callback"
                ](
                    callback_id,
                    "No se pudo enviar el borrador.",
                )

                resultados.append({
                    "codigo": codigo,
                    "estado": (
                        "error_enviando_borrador_telegram"
                    ),
                    "error": enviado,
                })

            continue

        if (
            accion == "enviar"
            and estado
            == "esperando_autorizacion_envio"
        ):
            enviado = funciones[
                "enviar_borrador"
            ](
                alerta.get(
                    "resultado",
                    {},
                ).get(
                    "draft_id",
                    "",
                )
            )

            if enviado.get(
                "ok"
            ):
                actualizado = funciones[
                    "actualizar_alerta"
                ](
                    message_id=alerta[
                        "message_id"
                    ],
                    estado="correo_enviado",
                    cambios={
                        "gmail_envio": enviado,
                    },
                )

                confirmacion = funciones[
                    "enviar_confirmacion_telegram"
                ](
                    codigo,
                    "Correo enviado correctamente.",
                )

                actualizar_correo_desde_telegram(
                    funciones=funciones,
                    alerta=alerta,
                    accion="correo_urgente_enviado",
                    requiere_revision=False,
                    resultado_extra={
                        "telegram_autorizacion": (
                            actualizado
                        ),
                        "telegram_confirmacion": (
                            confirmacion
                        ),
                    },
                )

                funciones[
                    "responder_callback"
                ](
                    callback_id,
                    "Correo enviado.",
                )
                funciones[
                    "retirar_botones"
                ](
                    datos.get(
                        "chat_id"
                    ),
                    datos.get(
                        "message_id"
                    ),
                )

                resultados.append({
                    "codigo": codigo,
                    "estado": "correo_enviado",
                })

            else:
                funciones[
                    "responder_callback"
                ](
                    callback_id,
                    "No se pudo enviar el correo.",
                )

                resultados.append({
                    "codigo": codigo,
                    "estado": "error_enviando_correo",
                    "error": enviado,
                })

            continue

        funciones[
            "responder_callback"
        ](
            callback_id,
            "Acción no válida para el estado actual.",
        )

    funciones[
        "guardar_estado"
    ](
        "telegram_offset",
        siguiente_offset,
    )

    return {
        "ok": True,
        "estado": "telegram_procesado",
        "procesadas": len(
            resultados
        ),
        "resultados": resultados,
    }


def ejecutar_agente(
    tools,
    funciones,
    prompts,
    procesar_telegram=True,
):
    """Procesa Telegram y todos los correos pendientes."""

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

    if procesar_telegram:
        mostrar(
            "TELEGRAM",
            "Consultando autorizaciones pendientes",
        )

        resultado_telegram = (
            procesar_actualizaciones_telegram(
                funciones
            )
        )

    else:
        resultado_telegram = {
            "ok": True,
            "estado": "consulta_telegram_omitida",
            "procesadas": 0,
            "resultados": [],
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
            "telegram": resultado_telegram,
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
        "telegram": resultado_telegram,
        "resultados": resultados,
    }
