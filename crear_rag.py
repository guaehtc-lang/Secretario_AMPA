"""Crea el RAG local a partir de los correos enviados de Gmail."""

import json

from email_reply_parser import EmailReplyParser

from src.gmail import (
    buscar_ids,
    buscar_valor,
    convertir_resultado,
    obtener_sesion_google,
    preparar_correo,
)
from src.parametros import RAG_PATH


RAG_MAX_EMAILS = 1000
RESULTADOS_POR_PAGINA = 50
QUERY_GMAIL = "in:sent"


# ==========================================
# 1. FUNCIONES INTERNAS
# ==========================================

def obtener_ids_enviados():
    """Obtiene los identificadores de los correos enviados."""

    sesion = obtener_sesion_google()
    ids = []
    page_token = ""

    while len(ids) < RAG_MAX_EMAILS:
        resultado = convertir_resultado(
            sesion.execute(
                "GMAIL_FETCH_EMAILS",
                arguments={
                    "ids_only": True,
                    "include_payload": False,
                    "include_spam_trash": False,
                    "label_ids": ["SENT"],
                    "max_results": min(
                        RESULTADOS_POR_PAGINA,
                        RAG_MAX_EMAILS - len(ids),
                    ),
                    "page_token": page_token,
                    "query": QUERY_GMAIL,
                    "user_id": "me",
                    "verbose": False,
                },
            )
        )

        for message_id in buscar_ids(resultado):
            if message_id not in ids:
                ids.append(message_id)

        siguiente = buscar_valor(
            resultado,
            [
                "nextPageToken",
                "next_page_token",
            ],
        )

        if not siguiente:
            break

        page_token = siguiente

    return ids[:RAG_MAX_EMAILS]


def limpiar_cuerpo(cuerpo):
    """Elimina del correo el historial citado del hilo."""

    cuerpo = EmailReplyParser.parse_reply(
        cuerpo or ""
    )

    return cuerpo.strip()


def guardar_documentos(documentos):
    """Guarda los correos preparados en formato JSONL."""

    RAG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RAG_PATH.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        for documento in documentos:
            archivo.write(
                json.dumps(
                    documento,
                    ensure_ascii=False,
                )
                + "\n"
            )


# ==========================================
# 2. CREACIÓN DEL RAG
# ==========================================

def crear_rag():
    """Descarga correos enviados, los limpia y crea el RAG."""

    sesion = obtener_sesion_google()
    ids = obtener_ids_enviados()

    documentos = []
    correos_vistos = set()

    print(
        "Correos enviados encontrados:",
        len(ids),
    )

    for numero, message_id in enumerate(
        ids,
        start=1,
    ):
        try:
            resultado = sesion.execute(
                "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
                arguments={
                    "format": "full",
                    "message_id": message_id,
                    "user_id": "me",
                },
            )

            correo = preparar_correo(resultado)
            labels = set(
                correo.get(
                    "labels",
                    [],
                )
            )

            if "DRAFT" in labels:
                continue

            if labels and "SENT" not in labels:
                continue

            cuerpo = limpiar_cuerpo(
                correo.get(
                    "cuerpo",
                    "",
                )
            )

            if not cuerpo:
                continue

            asunto = correo.get(
                "asunto",
                "",
            ).strip()

            firma = (
                asunto.lower(),
                cuerpo.lower(),
            )

            if firma in correos_vistos:
                continue

            correos_vistos.add(firma)

            documentos.append({
                "message_id": (
                    correo.get(
                        "message_id"
                    )
                    or message_id
                ),
                "thread_id": correo.get(
                    "thread_id",
                    "",
                ),
                "fecha": correo.get(
                    "fecha",
                    "",
                ),
                "remitente": correo.get(
                    "remitente",
                    "",
                ),
                "destinatario": correo.get(
                    "destinatario",
                    "",
                ),
                "asunto": asunto,
                "cuerpo": cuerpo,
                "tipo": "enviado",
            })

            if (
                numero % 25 == 0
                or numero == len(ids)
            ):
                print(
                    f"Procesados: {numero}/{len(ids)} | "
                    f"Guardados: {len(documentos)}"
                )

        except Exception as error:
            print(
                f"Error en {message_id}: {error}"
            )

    guardar_documentos(documentos)

    resultado = {
        "ok": True,
        "correos_encontrados": len(ids),
        "correos_guardados": len(documentos),
        "archivo": str(RAG_PATH),
    }

    print("\n===== RAG CREADO =====")
    print(
        json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2,
        )
    )

    return resultado


# ==========================================
# 3. EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    crear_rag()
