"""Ejecución principal del agente Secretario AMPA.

Ejemplos:

python main.py --probar-conexion
python main.py --revisar
python main.py --revisar --limite 3
python main.py --revisar --reprocesar
"""

import argparse
import json

from src import config
from src.agente import analizar_correo
from src.gmail_client import GmailClient
from src.google_oauth import crear_servicio_gmail
from src.memoria import esta_procesado, guardar_resultado


def probar_conexion():
    """Comprueba OAuth y muestra la cuenta autorizada."""

    _, perfil = crear_servicio_gmail()

    print("Conexión correcta")
    print("Cuenta:", perfil["emailAddress"])
    print("Mensajes totales:", perfil.get("messagesTotal"))
    print("Hilos totales:", perfil.get("threadsTotal"))
    print("Modo Gmail:", config.GMAIL_ACCESS_MODE)


def revisar_correos(limite, reprocesar=False):
    """Lee, analiza y muestra los correos encontrados."""

    servicio, perfil = crear_servicio_gmail()
    gmail = GmailClient(servicio)

    print("Cuenta autorizada:", perfil["emailAddress"])
    print("Consulta Gmail:", config.GMAIL_QUERY)
    print("Límite:", limite)

    mensajes = gmail.buscar_correos(
        limite=limite,
    )

    if not mensajes:
        print("No se han encontrado correos.")
        return

    for posicion, referencia in enumerate(mensajes, start=1):

        message_id = referencia["id"]

        if esta_procesado(message_id) and not reprocesar:
            print(
                f"\n[{posicion}] Correo omitido: "
                "ya estaba procesado."
            )
            continue

        correo = gmail.leer_correo(message_id)

        print("\n" + "=" * 70)
        print(f"[{posicion}] {correo['asunto']}")
        print("De:", correo["remitente"])
        print("=" * 70)

        resultado, uso = analizar_correo(correo)

        print(
            json.dumps(
                resultado,
                indent=2,
                ensure_ascii=False,
            )
        )

        print(
            "Tokens:",
            uso.prompt_tokens,
            "+",
            uso.completion_tokens,
            "=",
            uso.total_tokens,
        )

        draft_id = None
        clasificacion = resultado.get("clasificacion")
        borrador = resultado.get("borrador", {})

        if (
            clasificacion
            in ["requiere_respuesta", "solicitud_reunion"]
            and borrador.get("necesario")
            and config.ALLOW_CREATE_DRAFTS
        ):
            destinatarios = borrador.get("destinatarios") or [
                correo["remitente"]
            ]

            borrador_creado = gmail.crear_borrador(
                correo_original=correo,
                asunto=borrador.get("asunto") or correo["asunto"],
                cuerpo=borrador.get("cuerpo", ""),
                destinatarios=destinatarios,
            )

            draft_id = borrador_creado["id"]
            print("Borrador creado:", draft_id)

        if (
            clasificacion
            in ["requiere_respuesta", "solicitud_reunion"]
            and draft_id
            and config.ALLOW_MODIFY_LABELS
        ):
            gmail.marcar_como_leido(message_id)
            print("Correo marcado como leído.")

        # Los informativos y los casos de revisión manual permanecen
        # sin modificar en Gmail.
        guardar_resultado(
            message_id,
            resultado,
            draft_id,
        )


def crear_parser():
    """Crea los argumentos disponibles en la terminal."""

    parser = argparse.ArgumentParser(
        description="Agente Secretario AMPA"
    )

    parser.add_argument(
        "--probar-conexion",
        action="store_true",
        help="Autoriza Gmail y comprueba la cuenta",
    )

    parser.add_argument(
        "--revisar",
        action="store_true",
        help="Analiza los correos de la consulta configurada",
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=config.MAX_EMAILS_PER_RUN,
        help="Número máximo de correos a analizar",
    )

    parser.add_argument(
        "--reprocesar",
        action="store_true",
        help="Vuelve a analizar correos ya guardados",
    )

    return parser


if __name__ == "__main__":

    argumentos = crear_parser().parse_args()

    if argumentos.probar_conexion:
        probar_conexion()

    elif argumentos.revisar:
        revisar_correos(
            limite=argumentos.limite,
            reprocesar=argumentos.reprocesar,
        )

    else:
        print("Usa una opción:")
        print("python main.py --probar-conexion")
        print("python main.py --revisar")
