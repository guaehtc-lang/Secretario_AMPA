"""Flujo principal controlado completamente por Python."""

from src.parametros import SHOW_STEPS


def mostrar(paso, texto):
    """Muestra el avance cuando está activado."""

    if SHOW_STEPS:
        print(f"[{paso}] {texto}")


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
    """Atajo para guardar el resultado del correo."""

    return funciones["registrar_correo"](
        message_id=correo["message_id"],
        clasificacion=clasificacion,
        resumen=resumen,
        accion=accion,
        estado_gmail=estado_gmail,
        draft_id=draft_id,
        requiere_revision=requiere_revision,
        error=error,
        resultado=resultado,
    )


def procesar_informativo(
    correo,
    clasificacion,
    funciones,
):
    """Registra un informativo y lo conserva no leído."""

    mostrar("ACCIÓN", "Informativo: se mantiene no leído")

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="informativo",
        resumen=clasificacion["resumen"],
        accion="registrado_sin_accion",
        estado_gmail="no_leido",
    )


def procesar_no_clasificado(
    correo,
    clasificacion,
    funciones,
):
    """Deja el correo pendiente de revisión humana."""

    mostrar(
        "ACCIÓN",
        "No clasificado: revisión humana y no leído",
    )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="no_clasificado",
        resumen=clasificacion["resumen"],
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
    """Consulta el RAG, crea borrador y marca leído."""

    consulta = " ".join([
        correo.get("asunto", ""),
        correo.get("cuerpo", ""),
    ])

    mostrar("RAG", "Consultando antecedentes")
    contexto = funciones["consultar_rag"](consulta)

    mostrar("LLM", "Redactando borrador")
    borrador = funciones["redactar_borrador"](
        correo=correo,
        prompts=prompts,
        tipo="respuesta",
        contexto_rag=contexto,
    )

    mostrar("GMAIL", "Creando borrador")
    creado = funciones["crear_borrador"](
        message_id=correo["message_id"],
        asunto=borrador["asunto"],
        cuerpo=borrador["cuerpo"],
    )

    if not creado.get("ok"):
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="necesita_respuesta",
            resumen=clasificacion["resumen"],
            accion="error_creando_borrador",
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(creado),
            resultado={
                "rag": contexto,
                "borrador": borrador,
                "gmail": creado,
            },
        )

    mostrar("GMAIL", "Marcando correo como leído")
    leido = funciones["marcar_como_leido"](
        correo["message_id"]
    )

    estado_gmail = (
        "leido"
        if leido.get("ok")
        else "no_leido"
    )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="necesita_respuesta",
        resumen=clasificacion["resumen"],
        accion="borrador_creado",
        estado_gmail=estado_gmail,
        draft_id=creado.get("draft_id", ""),
        requiere_revision=True,
        error=("" if leido.get("ok") else str(leido)),
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
    """Procesa reuniones sin crear eventos automáticos."""

    mostrar("LLM", "Extrayendo datos de la reunión")
    reunion = funciones["extraer_reunion"](
        correo,
        prompts,
    )

    if reunion["tipo"] in ["confirmacion", "rechazo"]:
        mostrar(
            "REUNIÓN",
            f"{reunion['tipo']} registrada sin crear evento",
        )

        leido = funciones["marcar_como_leido"](
            correo["message_id"]
        )

        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="reunion",
            resumen=clasificacion["resumen"],
            accion=f"reunion_{reunion['tipo']}",
            estado_gmail=(
                "leido"
                if leido.get("ok")
                else "no_leido"
            ),
            requiere_revision=False,
            error=(
                ""
                if leido.get("ok")
                else str(leido)
            ),
            resultado={
                "reunion": reunion,
                "marcar_leido": leido,
            },
        )

    mostrar("CALENDAR", "Consultando disponibilidad")
    disponibilidad = funciones[
        "consultar_disponibilidad"
    ](
        opciones=reunion["opciones"],
        duracion_minutos=(
            reunion["duracion_minutos"]
        ),
    )

    mostrar("LLM", "Redactando propuesta de reunión")
    borrador = funciones["redactar_borrador"](
        correo=correo,
        prompts=prompts,
        tipo="reunion",
        disponibilidad=disponibilidad,
    )

    mostrar("GMAIL", "Creando borrador de reunión")
    creado = funciones["crear_borrador"](
        message_id=correo["message_id"],
        asunto=borrador["asunto"],
        cuerpo=borrador["cuerpo"],
    )

    if not creado.get("ok"):
        return registrar(
            funciones=funciones,
            correo=correo,
            clasificacion="reunion",
            resumen=clasificacion["resumen"],
            accion="error_borrador_reunion",
            estado_gmail="no_leido",
            requiere_revision=True,
            error=str(creado),
            resultado={
                "reunion": reunion,
                "disponibilidad": disponibilidad,
                "borrador": borrador,
                "gmail": creado,
            },
        )

    leido = funciones["marcar_como_leido"](
        correo["message_id"]
    )

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="reunion",
        resumen=clasificacion["resumen"],
        accion="borrador_reunion_creado",
        estado_gmail=(
            "leido"
            if leido.get("ok")
            else "no_leido"
        ),
        draft_id=creado.get("draft_id", ""),
        requiere_revision=True,
        error=("" if leido.get("ok") else str(leido)),
        resultado={
            "reunion": reunion,
            "disponibilidad": disponibilidad,
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
    """Genera la alerta de WhatsApp y marca leído si funciona."""

    mostrar("LLM", "Generando resumen de WhatsApp")
    alerta = funciones["crear_resumen_whatsapp"](
        correo,
        prompts,
    )

    mostrar("WHATSAPP", "Enviando alerta")
    enviado = funciones["enviar_whatsapp"](
        message_id=correo["message_id"],
        resumen=alerta["resumen"],
        tipo_riesgo=alerta["tipo_riesgo"],
    )

    if enviado.get("ok"):
        leido = funciones["marcar_como_leido"](
            correo["message_id"]
        )
    else:
        leido = {
            "ok": False,
            "estado": "no_marcado_por_fallo_whatsapp",
        }

    return registrar(
        funciones=funciones,
        correo=correo,
        clasificacion="urgente_seguridad",
        resumen=clasificacion["resumen"],
        accion=(
            "alerta_whatsapp_enviada"
            if enviado.get("ok")
            else "error_whatsapp"
        ),
        estado_gmail=(
            "leido"
            if leido.get("ok")
            else "no_leido"
        ),
        requiere_revision=(
            not enviado.get("ok")
        ),
        error=(
            ""
            if enviado.get("ok") and leido.get("ok")
            else str({
                "whatsapp": enviado,
                "marcar_leido": leido,
            })
        ),
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
    """Clasifica un correo y aplica un único flujo."""

    mostrar(
        "CORREO",
        correo.get("asunto", "(sin asunto)"),
    )

    mostrar("LLM", "Clasificando correo")
    clasificacion = funciones["clasificar_correo"](
        correo,
        prompts,
    )

    categoria = clasificacion["clasificacion"]
    mostrar("CLASIFICACIÓN", categoria)

    if categoria == "informativo":
        return procesar_informativo(
            correo,
            clasificacion,
            funciones,
        )

    if categoria == "necesita_respuesta":
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

    if categoria == "urgente_seguridad":
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


def ejecutar_agente(tools, funciones, prompts):
    """Procesa todos los correos no leídos pendientes."""

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

    mostrar("GMAIL", "Buscando correos no leídos")
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

    for numero, correo in enumerate(correos, start=1):
        print(
            f"\n===== CORREO {numero}/{len(correos)} ====="
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
                clasificacion="no_clasificado",
                resumen="Error durante el procesamiento",
                accion="error_procesamiento",
                estado_gmail="no_leido",
                requiere_revision=True,
                error=str(error),
            )

        resultados.append(resultado)

    return {
        "ok": True,
        "estado": "ciclo_completado",
        "procesados": len(resultados),
        "resultados": resultados,
    }
