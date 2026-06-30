"""Funciones de Google Calendar utilizadas por el agente."""

import re
from datetime import (
    datetime,
    time,
    timedelta,
)
from zoneinfo import ZoneInfo

from src.composio_cliente import obtener_sesion_google

from src.clasificacion import (
    obtener_clasificacion_validada,
    obtener_contrapropuesta_reunion,
)
from src.gmail import obtener_correo_por_id
from src.memoria import (
    evento_existente,
    registrar_accion,
    registrar_evento,
)
from src.parametros import (
    ALLOW_CREATE_EVENTS,
    CALENDAR_ID,
    TIMEZONE,
)
from src.utilidades import (
    buscar_valor,
    convertir_resultado,
    extraer_email,
)


DIAS = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}

CLASIFICACIONES_CALENDAR = {
    "solicitud_reunion",
    "rechazo_reunion",
}

TITULO_REUNION_SEGURO = "Reunión con el AMPA"


PALABRAS_REUNION = [
    "reunión",
    "reunion",
    "cita",
    "entrevista",
    "videollamada",
    "disponibilidad",
    "quedar",
]


def normalizar_texto(texto):
    """Normaliza texto para aplicar controles."""

    return " ".join(
        (texto or "").lower().split()
    )


def correo_permite_calendar(
    correo,
    clasificacion,
    message_id,
):
    """Valida clasificación y contenido antes de usar Calendar."""

    clasificacion_validada = (
        obtener_clasificacion_validada(
            message_id
        )
    )

    if (
        not clasificacion_validada
        or clasificacion
        != clasificacion_validada
    ):
        return False

    if (
        clasificacion
        not in CLASIFICACIONES_CALENDAR
    ):
        return False

    if (
        clasificacion
        == "rechazo_reunion"
        and not obtener_contrapropuesta_reunion(
            message_id
        )
    ):
        return False

    texto = normalizar_texto(
        correo.get(
            "asunto",
            "",
        )
        + " "
        + correo.get(
            "cuerpo",
            "",
        )
    )

    return any(
        palabra in texto
        for palabra in PALABRAS_REUNION
    )

def opcion_aparece_en_correo(
    correo,
    opcion,
):
    """Comprueba que día y hora proceden del correo actual."""

    texto = normalizar_texto(
        correo.get(
            "asunto",
            "",
        )
        + " "
        + correo.get(
            "cuerpo",
            "",
        )
    )

    dia = normalizar_texto(
        opcion.get(
            "dia",
            "",
        )
    )

    fecha = (
        opcion.get(
            "fecha",
            ""
        )
        or ""
    )

    hora = (
        opcion.get(
            "hora_desde"
        )
        or opcion.get(
            "hora"
        )
        or ""
    )

    if dia and dia not in texto:
        return False

    if hora:
        variantes_hora = {
            hora,
            hora.replace(
                ":",
                ".",
            ),
        }

        if not any(
            variante in texto
            for variante in variantes_hora
        ):
            return False

    if fecha and not dia:
        try:
            fecha_obj = datetime.strptime(
                fecha,
                "%Y-%m-%d",
            )

            variantes_fecha = {
                fecha,
                fecha_obj.strftime(
                    "%d/%m/%Y"
                ),
                fecha_obj.strftime(
                    "%-d/%-m/%Y"
                ),
            }

        except (
            ValueError,
            OSError,
        ):
            variantes_fecha = {
                fecha
            }

        if not any(
            variante in texto
            for variante in variantes_fecha
        ):
            return False

    return bool(
        dia or fecha
    ) and bool(
        hora
    )


def proxima_fecha(dia, hora_texto):
    """Convierte un día de la semana en la próxima fecha futura."""

    numero_dia = DIAS.get(
        (dia or "").lower()
    )

    if numero_dia is None:
        return None

    zona = ZoneInfo(
        TIMEZONE
    )

    ahora = datetime.now(
        zona
    )

    diferencia = (
        numero_dia
        - ahora.weekday()
    ) % 7

    if diferencia == 0:
        diferencia = 7

    fecha = (
        ahora.date()
        + timedelta(
            days=diferencia
        )
    )

    hora, minuto = map(
        int,
        hora_texto.split(":"),
    )

    candidato = datetime.combine(
        fecha,
        time(
            hora,
            minuto,
        ),
        tzinfo=zona,
    )

    if candidato <= ahora:
        candidato += timedelta(
            days=7
        )

    return candidato.date()


def normalizar_opciones(
    opciones,
    correo=None,
):
    """Convierte días o fechas en opciones exactas.

    Cuando el correo indica un día de la semana, la fecha la calcula
    Python. Se ignora cualquier fecha calculada por el LLM.
    """

    normalizadas = []

    if not isinstance(
        opciones,
        list,
    ):
        return normalizadas

    for opcion in opciones:
        if not isinstance(
            opcion,
            dict,
        ):
            continue

        hora = (
            opcion.get(
                "hora_desde"
            )
            or opcion.get(
                "hora"
            )
        )

        if not re.fullmatch(
            r"([01]\d|2[0-3]):[0-5]\d",
            hora or "",
        ):
            continue

        dia = (
            opcion.get(
                "dia"
            )
            or ""
        ).strip().lower()

        fecha = (
            opcion.get(
                "fecha"
            )
            or ""
        ).strip()

        if dia:
            fecha_obj = proxima_fecha(
                dia,
                hora,
            )

        elif fecha:
            try:
                fecha_obj = datetime.strptime(
                    fecha,
                    "%Y-%m-%d",
                ).date()

            except ValueError:
                continue

        else:
            continue

        if not fecha_obj:
            continue

        normalizadas.append({
            "dia": dia,
            "fecha": fecha_obj.isoformat(),
            "hora_desde": hora,
        })

    return normalizadas

def consultar_disponibilidad(
    message_id,
    clasificacion,
    opciones,
    duracion_minutos=60,
):
    """Consulta Calendar solo para una solicitud real."""

    clasificacion = (
        clasificacion
        or ""
    ).strip().lower()

    correo = obtener_correo_por_id(
        message_id
    )

    if not correo_permite_calendar(
        correo,
        clasificacion,
        message_id,
    ):
        return {
            "ok": False,
            "estado": (
                "calendar_bloqueado_"
                "flujo_no_autorizado"
            ),
            "clasificacion": clasificacion,
        }

    opciones_respaldadas = [
        opcion
        for opcion in opciones or []
        if opcion_aparece_en_correo(
            correo,
            opcion,
        )
    ]

    if not opciones_respaldadas:
        return {
            "ok": False,
            "estado": (
                "calendar_bloqueado_"
                "fecha_no_respaldada"
            ),
            "mensaje": (
                "La fecha y la hora deben aparecer "
                "en el correo actual."
            ),
        }

    sesion = obtener_sesion_google()
    zona = ZoneInfo(
        TIMEZONE
    )

    resultados = []

    for opcion in normalizar_opciones(
        opciones_respaldadas,
        correo,
    ):
        hora, minuto = map(
            int,
            opcion[
                "hora_desde"
            ].split(":"),
        )

        fecha = datetime.strptime(
            opcion["fecha"],
            "%Y-%m-%d",
        ).date()

        inicio = datetime.combine(
            fecha,
            time(
                hora,
                minuto,
            ),
            tzinfo=zona,
        )

        fin = inicio + timedelta(
            minutes=duracion_minutos
        )

        respuesta = convertir_resultado(
            sesion.execute(
                "GOOGLECALENDAR_FIND_FREE_SLOTS",
                arguments={
                    "items": [
                        CALENDAR_ID
                    ],
                    "time_min": inicio.isoformat(),
                    "time_max": fin.isoformat(),
                    "timezone": TIMEZONE,
                },
            )
        )

        libres = (
            respuesta
            .get("data", {})
            .get("calendars", {})
            .get(CALENDAR_ID, {})
            .get("free", [])
        )

        resultados.append({
            **opcion,
            "hora_hasta": fin.strftime(
                "%H:%M"
            ),
            "inicio_iso": inicio.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "disponible": bool(
                libres
            ),
        })

    return {
        "ok": True,
        "estado": "disponibilidad_consultada",
        "opciones": resultados,
    }


def crear_invitacion_calendar(
    message_id,
    clasificacion,
    titulo,
    opcion,
    duracion_minutos=60,
):
    """Crea una invitación solo para una solicitud real."""

    clasificacion = (
        clasificacion
        or ""
    ).strip().lower()

    if not ALLOW_CREATE_EVENTS:
        return {
            "ok": False,
            "estado": "eventos_desactivados",
        }

    correo = obtener_correo_por_id(
        message_id
    )

    if not correo_permite_calendar(
        correo,
        clasificacion,
        message_id,
    ):
        return {
            "ok": False,
            "estado": (
                "invitacion_bloqueada_"
                "flujo_no_autorizado"
            ),
        }

    if not opcion_aparece_en_correo(
        correo,
        opcion,
    ):
        return {
            "ok": False,
            "estado": (
                "invitacion_bloqueada_"
                "fecha_no_respaldada"
            ),
        }

    existente = evento_existente(
        message_id
    )

    if existente:
        return {
            "ok": True,
            "estado": "evento_ya_existente",
            "evento": existente,
        }

    invitado = extraer_email(
        correo["remitente"]
    )

    if not invitado:
        return {
            "ok": False,
            "estado": "sin_invitado",
        }

    comprobacion = consultar_disponibilidad(
        message_id=message_id,
        clasificacion=clasificacion,
        opciones=[opcion],
        duracion_minutos=duracion_minutos,
    )

    opciones = comprobacion.get(
        "opciones",
        [],
    )

    if (
        not comprobacion.get(
            "ok"
        )
        or not opciones
        or not opciones[0][
            "disponible"
        ]
    ):
        return {
            "ok": False,
            "estado": "horario_no_disponible",
        }

    opcion = opciones[0]

    horas = (
        duracion_minutos
        // 60
    )

    minutos = (
        duracion_minutos
        % 60
    )

    titulo_seguro = (
        titulo
        or ""
    ).strip()

    titulo_normalizado = normalizar_texto(
        titulo_seguro
    )

    if (
        len(titulo_seguro) < 5
        or "reunin" in titulo_normalizado
    ):
        titulo_seguro = (
            TITULO_REUNION_SEGURO
        )

    sesion = obtener_sesion_google()

    resultado = convertir_resultado(
        sesion.execute(
            "GOOGLECALENDAR_CREATE_EVENT",
            arguments={
                "calendar_id": CALENDAR_ID,
                "summary": titulo_seguro,
                "description": (
                    "Reunión propuesta por el "
                    "agente Secretario AMPA."
                ),
                "start_datetime": opcion[
                    "inicio_iso"
                ],
                "timezone": TIMEZONE,
                "event_duration_hour": horas,
                "event_duration_minutes": minutos,
                "attendees": [
                    invitado
                ],
                "send_updates": "all",
                "create_meeting_room": False,
                "eventType": "default",
                "visibility": "default",
                "transparency": "opaque",
                "exclude_organizer": False,
                "guestsCanModify": False,
                "guestsCanInviteOthers": False,
                "guestsCanSeeOtherGuests": True,
            },
        )
    )

    event_id = buscar_valor(
        resultado,
        [
            "event_id",
            "eventId",
            "id",
        ],
    )

    event_url = buscar_valor(
        resultado,
        [
            "htmlLink",
            "html_link",
            "display_url",
        ],
    )

    registrar_evento(
        message_id=message_id,
        event_id=event_id or "",
        inicio=opcion["inicio_iso"],
        invitado=invitado,
        estado="needsAction",
    )

    registrar_accion(
        message_id=message_id,
        tipo="invitacion_calendar_creada",
        detalle=opcion["inicio_iso"],
    )

    return {
        "ok": True,
        "estado": "invitacion_enviada",
        "event_id": event_id or "",
        "event_url": event_url or "",
        "inicio": opcion["inicio_iso"],
        "invitado": invitado,
        "respuesta_invitado": "needsAction",
    }
