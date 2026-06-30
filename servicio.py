"""Ejecuta Gmail por hora y revisa Telegram periódicamente."""

import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from main import ejecutar_ciclo
from src.agente import (
    procesar_actualizaciones_telegram,
)
from src.funciones import funciones
from src.memoria import inicializar_memoria
from src.parametros import (
    ORDINARY_END_HOUR,
    ORDINARY_START_HOUR,
    SCHEDULER_CHECK_SECONDS,
    TIMEZONE,
)


def ejecutar_servicio():
    """Mantiene activos Gmail y Telegram."""

    inicializar_memoria()
    ultima_hora = None

    while True:
        ahora = datetime.now(
            ZoneInfo(
                TIMEZONE
            )
        )
        hora_actual = ahora.strftime(
            "%Y-%m-%d %H"
        )

        resultado_telegram = (
            procesar_actualizaciones_telegram(
                funciones
            )
        )

        if resultado_telegram.get(
            "procesadas",
            0,
        ):
            print(
                json.dumps(
                    resultado_telegram,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
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
            resultado = ejecutar_ciclo(
                procesar_telegram=False
            )

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
