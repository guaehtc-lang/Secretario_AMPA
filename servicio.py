"""Mantiene el agente activo y ejecuta un ciclo cada hora."""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

from main import ejecutar_ciclo
from src.parametros import (
    HORA_FIN,
    HORA_INICIO,
    SEGUNDOS_COMPROBACION,
    TIMEZONE,
)


ultima_hora = None

while True:
    ahora = datetime.now(
        ZoneInfo(TIMEZONE)
    )

    hora_actual = ahora.strftime(
        "%Y-%m-%d %H"
    )

    dentro_horario = (
        HORA_INICIO
        <= ahora.hour
        <= HORA_FIN
    )

    if (
        dentro_horario
        and hora_actual != ultima_hora
    ):
        print(ejecutar_ciclo())
        ultima_hora = hora_actual

    time.sleep(
        SEGUNDOS_COMPROBACION
    )
