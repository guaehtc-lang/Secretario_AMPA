"""Consulta de disponibilidad en Google Calendar."""

import re
import unicodedata
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from zoneinfo import ZoneInfo

from src.gmail import (
    buscar_valor,
    convertir_resultado,
    obtener_sesion_google,
    resultado_tiene_error,
)
from src.parametros import (
    ALLOW_CREATE_EVENTS,
    CALENDAR_ID,
    DEFAULT_MEETING_MINUTES,
    TIMEZONE,
)


DIAS_SEMANA = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def quitar_acentos(texto):
    """Normaliza un texto para comparar meses y días."""

    texto = unicodedata.normalize(
        "NFD",
        texto or "",
    )

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(
            caracter
        ) != "Mn"
    ).lower().strip()


def parsear_fecha(fecha_texto):
    """Convierte formatos habituales en una fecha."""

    if isinstance(
        fecha_texto,
        datetime,
    ):
        return fecha_texto.date()

    if isinstance(
        fecha_texto,
        date,
    ):
        return fecha_texto

    texto = str(
        fecha_texto
        or ""
    ).strip()

    if not texto:
        return None

    formatos = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(
                texto,
                formato,
            ).date()
        except ValueError:
            continue

    texto_normalizado = quitar_acentos(
        texto
    )

    patrones = [
        r"^(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})$",
        r"^(\d{1,2})\s+([a-z]+)\s+(\d{4})$",
    ]

    for patron in patrones:
        coincidencia = re.match(
            patron,
            texto_normalizado,
        )

        if not coincidencia:
            continue

        dia = int(
            coincidencia.group(1)
        )
        mes = MESES.get(
            coincidencia.group(2)
        )
        anio = int(
            coincidencia.group(3)
        )

        if not mes:
            return None

        try:
            return date(
                anio,
                mes,
                dia,
            )
        except ValueError:
            return None

    return None


def proxima_fecha(
    dia,
    hora_texto,
):
    """Convierte un día en la siguiente fecha."""

    numero_dia = DIAS_SEMANA.get(
        (
            dia
            or ""
        ).strip().lower()
    )

    if numero_dia is None:
        numero_dia = DIAS_SEMANA.get(
            quitar_acentos(
                dia
            )
        )

    if numero_dia is None:
        return None

    ahora = datetime.now(
        ZoneInfo(
            TIMEZONE
        )
    )

    diferencia = (
        numero_dia
        - ahora.weekday()
    ) % 7

    if diferencia == 0:
        hora, minuto = map(
            int,
            hora_texto.split(":")
        )

        propuesta = ahora.replace(
            hour=hora,
            minute=minuto,
            second=0,
            microsecond=0,
        )

        if propuesta <= ahora:
            diferencia = 7

    return (
        ahora
        + timedelta(
            days=diferencia
        )
    ).date()


def normalizar_opciones(
    opciones,
):
    """Valida y normaliza las opciones extraídas por el LLM."""

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
                "hora"
            )
            or ""
        ).strip()

        try:
            datetime.strptime(
                hora,
                "%H:%M",
            )
        except ValueError:
            continue

        dia = (
            opcion.get(
                "dia"
            )
            or ""
        ).strip()

        fecha = parsear_fecha(
            opcion.get(
                "fecha"
            )
        )

        if not fecha:
            fecha = proxima_fecha(
                dia,
                hora,
            )

        if not fecha:
            continue

        normalizadas.append({
            "dia": dia,
            "fecha": fecha.isoformat(),
            "hora": hora,
        })

    return normalizadas


def consultar_disponibilidad(
    opciones,
    duracion_minutos=(
        DEFAULT_MEETING_MINUTES
    ),
):
    """Consulta cada opción en Calendar."""

    opciones = normalizar_opciones(
        opciones
    )

    if not opciones:
        return {
            "ok": True,
            "estado": "sin_opciones_validas",
            "opciones": [],
        }

    sesion = obtener_sesion_google()
    zona = ZoneInfo(
        TIMEZONE
    )
    resultados = []

    for opcion in opciones:
        hora, minuto = map(
            int,
            opcion[
                "hora"
            ].split(":")
        )

        fecha = datetime.strptime(
            opcion[
                "fecha"
            ],
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
            .get(
                "data",
                {},
            )
            .get(
                "calendars",
                {},
            )
            .get(
                CALENDAR_ID,
                {},
            )
            .get(
                "free",
                [],
            )
        )

        resultados.append({
            **opcion,
            "hora_hasta": fin.strftime(
                "%H:%M"
            ),
            "inicio_iso": inicio.isoformat(),
            "disponible": bool(
                libres
            ),
        })

    return {
        "ok": True,
        "estado": "disponibilidad_consultada",
        "opciones": resultados,
    }


def crear_evento_reunion(
    correo,
    reunion,
):
    """Crea un evento únicamente para una reunión confirmada."""

    if not ALLOW_CREATE_EVENTS:
        return {
            "ok": False,
            "estado": "eventos_desactivados",
        }

    if not isinstance(
        reunion,
        dict,
    ):
        return {
            "ok": False,
            "estado": "reunion_no_valida",
        }

    if reunion.get(
        "tipo"
    ) != "confirmacion":
        return {
            "ok": False,
            "estado": "reunion_no_confirmada",
        }

    opciones = normalizar_opciones(
        reunion.get(
            "opciones",
            [],
        )
    )

    if len(opciones) != 1:
        return {
            "ok": False,
            "estado": (
                "confirmacion_sin_fecha_unica"
            ),
            "opciones": opciones,
        }

    duracion = reunion.get(
        "duracion_minutos",
        DEFAULT_MEETING_MINUTES,
    )

    try:
        duracion = int(
            duracion
        )
    except (
        TypeError,
        ValueError,
    ):
        duracion = (
            DEFAULT_MEETING_MINUTES
        )

    duracion = max(
        15,
        min(
            duracion,
            180,
        ),
    )

    disponibilidad = consultar_disponibilidad(
        opciones=opciones,
        duracion_minutos=duracion,
    )

    opciones_comprobadas = disponibilidad.get(
        "opciones",
        [],
    )

    if (
        not disponibilidad.get(
            "ok"
        )
        or len(opciones_comprobadas) != 1
        or not opciones_comprobadas[0].get(
            "disponible"
        )
    ):
        return {
            "ok": False,
            "estado": "horario_no_disponible",
            "disponibilidad": disponibilidad,
        }

    opcion = opciones_comprobadas[0]
    remitente = correo.get(
        "remitente",
        "",
    ).strip()

    motivo = (
        reunion.get(
            "motivo"
        )
        or correo.get(
            "asunto"
        )
        or "Reunión confirmada"
    ).strip()

    titulo = (
        "Reunión AMPA - "
        + motivo
    )[:180]

    horas = duracion // 60
    minutos = duracion % 60

    sesion = obtener_sesion_google()

    resultado = convertir_resultado(
        sesion.execute(
            "GOOGLECALENDAR_CREATE_EVENT",
            arguments={
                "calendar_id": CALENDAR_ID,
                "summary": titulo,
                "description": (
                    "Reunión confirmada por correo.\n"
                    f"Remitente: {remitente}\n"
                    f"Asunto: {correo.get('asunto', '')}"
                ),
                "start_datetime": opcion[
                    "inicio_iso"
                ],
                "timezone": TIMEZONE,
                "event_duration_hour": horas,
                "event_duration_minutes": minutos,
                "send_updates": "none",
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

    if resultado_tiene_error(
        resultado
    ):
        return {
            "ok": False,
            "estado": "error_creando_evento",
            "resultado": resultado,
        }

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

    if not event_id:
        return {
            "ok": False,
            "estado": "evento_sin_identificador",
            "resultado": resultado,
        }

    return {
        "ok": True,
        "estado": "evento_creado",
        "event_id": event_id,
        "event_url": event_url or "",
        "titulo": titulo,
        "remitente": remitente,
        "fecha": opcion[
            "fecha"
        ],
        "hora": opcion[
            "hora"
        ],
        "hora_hasta": opcion[
            "hora_hasta"
        ],
        "inicio_iso": opcion[
            "inicio_iso"
        ],
        "duracion_minutos": duracion,
    }

