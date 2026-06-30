"""Registro de funciones disponibles para el agente."""

from src.calendar import consultar_disponibilidad
from src.clasificador import clasificar_correo
from src.gmail import (
    crear_borrador,
    marcar_como_leido,
    obtener_correos_no_leidos,
)
from src.memoria import registrar_correo
from src.rag import consultar_rag
from src.redactor import redactar_borrador
from src.reuniones import extraer_reunion
from src.urgencias import crear_resumen_whatsapp
from src.whatsapp import enviar_whatsapp


funciones = {
    "obtener_correos_no_leidos": (
        obtener_correos_no_leidos
    ),
    "clasificar_correo": clasificar_correo,
    "consultar_rag": consultar_rag,
    "redactar_borrador": redactar_borrador,
    "crear_borrador": crear_borrador,
    "marcar_como_leido": marcar_como_leido,
    "extraer_reunion": extraer_reunion,
    "consultar_disponibilidad": (
        consultar_disponibilidad
    ),
    "crear_resumen_whatsapp": (
        crear_resumen_whatsapp
    ),
    "enviar_whatsapp": enviar_whatsapp,
    "registrar_correo": registrar_correo,
}
