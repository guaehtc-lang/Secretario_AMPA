"""Ejecuta un ciclo del agente Secretario AMPA."""

from src.agente import ejecutar_agente
from src.funciones import funciones
from src.memoria import inicializar_memoria
from src.prompt import crear_mensajes
from src.tools import tools


def ejecutar_ciclo():
    """Prepara las piezas y ejecuta el agente."""

    inicializar_memoria()
    mensajes = crear_mensajes()

    return ejecutar_agente(
        mensajes,
        tools,
        funciones,
    )


if __name__ == "__main__":
    print(ejecutar_ciclo())
