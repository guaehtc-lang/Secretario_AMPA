"""Ejecuta el agente una vez por hora dentro del horario."""

import json
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


def ejecutar_servicio():
    """Mantiene activo el ciclo horario."""

    ultima_hora = None

    while True:
        ahora = datetime.now(
            ZoneInfo(TIMEZONE)
        )
        hora_actual = ahora.strftime(
            "%Y-%m-%d %H"
        )

        dentro_horario = (
            ORDINARY_START_HOUR
            <= ahora.hour
            <= ORDINARY_END_HOUR
        )

        if (
            dentro_horario
            and hora_actual != ultima_hora
        ):
            resultado = ejecutar_ciclo()

            print(
                json.dumps(
                    resultado,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )

            ultima_hora = hora_actual

        time.sleep(
            SCHEDULER_CHECK_SECONDS
        )


if __name__ == "__main__":
    ejecutar_servicio()
