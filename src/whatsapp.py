"""WhatsApp simulado para validar el MVP."""

from datetime import datetime

from src.memoria import (
    alerta_ya_enviada,
    registrar_alerta,
)
from src.parametros import (
    WHATSAPP_MODE,
    WHATSAPP_RECIPIENTS,
)


def enviar_whatsapp(
    message_id,
    resumen,
    tipo_riesgo,
):
    """Registra una alerta simulada."""

    if alerta_ya_enviada(
        message_id
    ):
        return {
            "ok": True,
            "estado": (
                "alerta_ya_registrada"
            ),
            "duplicada": True,
        }

    if WHATSAPP_MODE != "simulado":
        return {
            "ok": False,
            "estado": (
                "whatsapp_real_no_configurado"
            ),
            "mensaje": (
                "V3.5 solo implementa "
                "el modo simulado."
            ),
        }

    resultado = {
        "ok": True,
        "estado": "whatsapp_simulado",
        "fecha": datetime.now().isoformat(
            timespec="seconds",
        ),
        "destinatarios": (
            WHATSAPP_RECIPIENTS
        ),
        "tipo_riesgo": tipo_riesgo,
        "resumen": resumen,
        "duplicada": False,
    }

    registrar_alerta(
        message_id=message_id,
        tipo_riesgo=tipo_riesgo,
        resumen=resumen,
        modo=WHATSAPP_MODE,
        resultado=resultado,
    )

    print("\n[WHATSAPP SIMULADO]")
    print(
        "Destinatarios:",
        ", ".join(
            WHATSAPP_RECIPIENTS
        ),
    )
    print(
        resumen
    )

    return resultado
