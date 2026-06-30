"""WhatsApp simulado para validar el MVP sin envíos reales."""

import json
from datetime import datetime

from src.memoria import (
    alerta_ya_enviada,
    registrar_alerta,
)
from src.parametros import (
    WHATSAPP_LOG_PATH,
    WHATSAPP_MODE,
    WHATSAPP_RECIPIENTS,
)


def enviar_whatsapp(
    message_id,
    resumen,
    tipo_riesgo,
):
    """Registra una alerta simulada o bloquea el modo real."""

    if alerta_ya_enviada(message_id):
        return {
            "ok": True,
            "estado": "alerta_ya_registrada",
            "duplicada": True,
        }

    if WHATSAPP_MODE != "simulado":
        return {
            "ok": False,
            "estado": "whatsapp_real_no_configurado",
            "mensaje": (
                "V0.3 solo implementa el modo simulado."
            ),
        }

    resultado = {
        "ok": True,
        "estado": "whatsapp_simulado",
        "fecha": datetime.now().isoformat(
            timespec="seconds"
        ),
        "destinatarios": WHATSAPP_RECIPIENTS,
        "tipo_riesgo": tipo_riesgo,
        "resumen": resumen,
        "duplicada": False,
    }

    WHATSAPP_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with WHATSAPP_LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as archivo:
        archivo.write(
            json.dumps(
                resultado,
                ensure_ascii=False,
            )
            + "\n"
        )

    registrar_alerta(
        message_id=message_id,
        tipo_riesgo=tipo_riesgo,
        resumen=resumen,
        modo=WHATSAPP_MODE,
        resultado=resultado,
    )

    print("\n[WHATSAPP SIMULADO]")
    print("Destinatarios:", ", ".join(WHATSAPP_RECIPIENTS))
    print(resumen)

    return resultado
