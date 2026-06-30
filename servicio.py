"""Mantiene Telegram activo y revisa Gmail periódicamente."""

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
    GMAIL_CHECK_SECONDS,
    ORDINARY_END_HOUR,
    ORDINARY_START_HOUR,
    SERVICE_LOOP_SECONDS,
    TELEGRAM_CHECK_SECONDS,
    TIMEZONE,
)


def mostrar_json(
    resultado,
):
    """Muestra un resultado de forma legible."""

    print(
        json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        flush=True,
    )


def dentro_horario(
    hora,
):
    """Comprueba el horario, incluso si cruza medianoche."""

    if (
        ORDINARY_START_HOUR
        <= ORDINARY_END_HOUR
    ):
        return (
            ORDINARY_START_HOUR
            <= hora
            <= ORDINARY_END_HOUR
        )

    return (
        hora >= ORDINARY_START_HOUR
        or hora <= ORDINARY_END_HOUR
    )


def ejecutar_servicio():
    """Mantiene activos Gmail y Telegram sin detenerse por un fallo puntual."""

    inicializar_memoria()
    zona_horaria = ZoneInfo(
        TIMEZONE
    )

    ultima_revision_gmail = None
    ultima_revision_telegram = None
    estado_horario_anterior = None

    print(
        "[SERVICIO] Secretario AMPA iniciado",
        flush=True,
    )
    print(
        "[SERVICIO] Gmail cada "
        + str(
            GMAIL_CHECK_SECONDS
        )
        + " segundos, entre "
        + str(
            ORDINARY_START_HOUR
        )
        + ":00 y "
        + str(
            ORDINARY_END_HOUR
        )
        + ":59",
        flush=True,
    )
    print(
        "[SERVICIO] Telegram cada "
        + str(
            TELEGRAM_CHECK_SECONDS
        )
        + " segundos",
        flush=True,
    )

    try:
        while True:
            instante = time.monotonic()
            ahora = datetime.now(
                zona_horaria
            )

            revisar_telegram = (
                ultima_revision_telegram
                is None
                or instante
                - ultima_revision_telegram
                >= TELEGRAM_CHECK_SECONDS
            )

            if revisar_telegram:
                ultima_revision_telegram = (
                    instante
                )

                try:
                    resultado_telegram = (
                        procesar_actualizaciones_telegram(
                            funciones
                        )
                    )

                    if (
                        not resultado_telegram.get(
                            "ok",
                            False,
                        )
                        or resultado_telegram.get(
                            "procesadas",
                            0,
                        )
                    ):
                        mostrar_json(
                            resultado_telegram
                        )

                except Exception as error:
                    print(
                        "[ERROR TELEGRAM] "
                        + type(
                            error
                        ).__name__
                        + ": "
                        + str(
                            error
                        ),
                        flush=True,
                    )

            horario_activo = dentro_horario(
                ahora.hour
            )

            if (
                horario_activo
                != estado_horario_anterior
            ):
                estado_horario_anterior = (
                    horario_activo
                )
                estado = (
                    "activo"
                    if horario_activo
                    else "en pausa"
                )
                print(
                    "[SERVICIO] Horario Gmail: "
                    + estado,
                    flush=True,
                )

            if not horario_activo:
                ultima_revision_gmail = None

            revisar_gmail = (
                horario_activo
                and (
                    ultima_revision_gmail
                    is None
                    or instante
                    - ultima_revision_gmail
                    >= GMAIL_CHECK_SECONDS
                )
            )

            if revisar_gmail:
                ultima_revision_gmail = instante

                try:
                    resultado_gmail = ejecutar_ciclo(
                        procesar_telegram=False
                    )
                    mostrar_json(
                        resultado_gmail
                    )

                except Exception as error:
                    print(
                        "[ERROR GMAIL] "
                        + type(
                            error
                        ).__name__
                        + ": "
                        + str(
                            error
                        ),
                        flush=True,
                    )

            time.sleep(
                SERVICE_LOOP_SECONDS
            )

    except KeyboardInterrupt:
        print(
            "\n[SERVICIO] Detenido por el usuario",
            flush=True,
        )


if __name__ == "__main__":
    ejecutar_servicio()
