"""Relaciona cada tool con su función Python."""

from src.calendar import (
    consultar_disponibilidad,
    crear_invitacion_calendar,
)
from src.clasificacion import clasificar_correo
from src.gmail import (
    crear_borrador,
    leer_correo_pendiente,
)
from src.memoria import registrar_resultado
from src.rag import buscar_contexto_rag


funciones = {
    "leer_correo_pendiente": leer_correo_pendiente,
    "clasificar_correo": clasificar_correo,
    "buscar_contexto_rag": buscar_contexto_rag,
    "crear_borrador": crear_borrador,
    "consultar_disponibilidad": consultar_disponibilidad,
    "crear_invitacion_calendar": crear_invitacion_calendar,
    "registrar_resultado": registrar_resultado,
}
