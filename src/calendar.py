"""Consulta de disponibilidad en Google Calendar."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.composio_cliente import obtener_sesion_google
from src.parametros import (
    CALENDAR_ID,
    DEFAULT_MEETING_MINUTES,
    TIMEZONE,
)
from src.utilidades import convertir_resultado


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


def proxima_fecha(dia, hora_texto):
    """Convierte un día de la semana en la siguiente fecha."""

    numero_dia = DIAS_SEMANA.get(
        (dia or "").strip().lower()
    )

    if numero_dia is None:
        return None

    ahora = datetime.now(ZoneInfo(TIMEZONE))
    diferencia = (numero_dia - ahora.weekday()) % 7

    if diferencia == 0:
        hora, minuto = map(int, hora_texto.split(":"))
        propuesta = ahora.replace(
            hour=hora,
            minute=minuto,
            second=0,
            microsecond=0,
        )
        if propuesta <= ahora:
            diferencia = 7

    return (ahora + timedelta(days=diferencia)).date()


def normalizar_opciones(opciones):
    """Valida y completa las opciones extraídas por el LLM."""

    normalizadas = []

    if not isinstance(opciones, list):
        return normalizadas

    for opcion in opciones:
        if not isinstance(opcion, dict):
            continue

        hora = (opcion.get("hora") or "").strip()

        try:
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            continue

        dia = (opcion.get("dia") or "").strip()
        fecha_texto = (opcion.get("fecha") or "").strip()

        if fecha_texto:
            try:
                fecha = datetime.strptime(
                    fecha_texto,
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                continue
        else:
            fecha = proxima_fecha(dia, hora)

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
    duracion_minutos=DEFAULT_MEETING_MINUTES,
):
    """Consulta cada opción en Google Calendar."""

    opciones = normalizar_opciones(opciones)

    if not opciones:
        return {
            "ok": True,
            "estado": "sin_opciones_validas",
            "opciones": [],
        }

    sesion = obtener_sesion_google()
    zona = ZoneInfo(TIMEZONE)
    resultados = []

    for opcion in opciones:
        hora, minuto = map(
            int,
            opcion["hora"].split(":"),
        )
        fecha = datetime.strptime(
            opcion["fecha"],
            "%Y-%m-%d",
        ).date()

        inicio = datetime.combine(
            fecha,
            time(hora, minuto),
            tzinfo=zona,
        )
        fin = inicio + timedelta(
            minutes=duracion_minutos
        )

        respuesta = convertir_resultado(
            sesion.execute(
                "GOOGLECALENDAR_FIND_FREE_SLOTS",
                arguments={
                    "items": [CALENDAR_ID],
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
            "hora_hasta": fin.strftime("%H:%M"),
            "inicio_iso": inicio.isoformat(),
            "disponible": bool(libres),
        })

    return {
        "ok": True,
        "estado": "disponibilidad_consultada",
        "opciones": resultados,
    }
