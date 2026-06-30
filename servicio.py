"""Ejecuta el agente una vez por hora dentro del horario."""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from main import ejecutar_ciclo
from src.parametros import (
    ORDINARY_END_HOUR,
    ORDINARY_START_HOUR,
    SCHEDULER_CHECK_SECONDS,
    TIMEZONE,
)


ultima_hora = None

while True:
    ahora = datetime.now(ZoneInfo(TIMEZONE))
    hora_actual = ahora.strftime("%Y-%m-%d %H")

    dentro_horario = (
        ORDINARY_START_HOUR
        <= ahora.hour
        <= ORDINARY_END_HOUR
    )

    if dentro_horario and hora_actual != ultima_hora:
        print(ejecutar_ciclo())
        ultima_hora = hora_actual

    time.sleep(SCHEDULER_CHECK_SECONDS)
