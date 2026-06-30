"""RAG local separado, construido con correos enviados."""

import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.composio_cliente import obtener_sesion_google
from src.gmail import preparar_correo
from src.parametros import (
    RAG_MAX_EMAILS,
    RAG_MIN_SIMILARITY,
    RAG_PATH,
    RAG_RESULTS,
    RAG_YEARS,
)
from src.utilidades import (
    buscar_ids,
    buscar_valor,
    convertir_resultado,
)


def cargar_documentos():
    """Lee los documentos guardados en el RAG."""

    if not RAG_PATH.exists():
        return []

    documentos = []

    with RAG_PATH.open(encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea:
                documentos.append(json.loads(linea))

    return documentos


def consultar_rag(consulta, limite=RAG_RESULTS):
    """Busca antecedentes similares sin modificar el RAG."""

    documentos = cargar_documentos()

    if not documentos:
        return {
            "ok": True,
            "estado": "rag_vacio",
            "resultados": [],
        }

    textos = [
        " ".join([
            documento.get("asunto", ""),
            documento.get("cuerpo", ""),
        ]).strip()
        for documento in documentos
    ]

    try:
        vectorizador = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
        )
        matriz = vectorizador.fit_transform(
            textos + [consulta]
        )
    except ValueError:
        return {
            "ok": True,
            "estado": "rag_sin_vocabulario",
            "resultados": [],
        }

    similitudes = cosine_similarity(
        matriz[-1],
        matriz[:-1],
    )[0]

    indices = similitudes.argsort()[::-1]
    resultados = []

    for indice in indices:
        similitud = float(similitudes[int(indice)])

        if similitud < RAG_MIN_SIMILARITY:
            continue

        documento = documentos[int(indice)]

        resultados.append({
            "message_id": documento.get(
                "message_id",
                "",
            ),
            "fecha": documento.get("fecha", ""),
            "asunto": documento.get("asunto", ""),
            "destinatario": documento.get(
                "destinatario",
                "",
            ),
            "cuerpo": documento.get(
                "cuerpo",
                "",
            )[:1800],
            "similitud": round(similitud, 3),
        })

        if len(resultados) >= max(1, int(limite)):
            break

    return {
        "ok": True,
        "estado": (
            "contexto_recuperado"
            if resultados
            else "sin_antecedentes_relevantes"
        ),
        "resultados": resultados,
    }


def actualizar_rag():
    """Descarga únicamente correos enviados y reconstruye el RAG."""

    sesion = obtener_sesion_google()
    dias = 365 * RAG_YEARS
    query = f"in:sent newer_than:{dias}d"

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
                        50,
                        RAG_MAX_EMAILS - len(ids),
                    ),
                    "page_token": page_token,
                    "query": query,
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
            ["nextPageToken", "next_page_token"],
        )

        if not siguiente:
            break

        page_token = siguiente

    documentos = []

    for message_id in ids[:RAG_MAX_EMAILS]:
        resultado = sesion.execute(
            "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
            arguments={
                "format": "full",
                "message_id": message_id,
                "user_id": "me",
            },
        )

        correo = preparar_correo(resultado)
        labels = set(correo.get("labels", []))

        if "DRAFT" in labels:
            continue

        if labels and "SENT" not in labels:
            continue

        if not correo.get("cuerpo"):
            continue

        documentos.append({
            "message_id": (
                correo.get("message_id")
                or message_id
            ),
            "thread_id": correo.get("thread_id", ""),
            "fecha": correo.get("fecha", ""),
            "remitente": correo.get("remitente", ""),
            "destinatario": correo.get(
                "destinatario",
                "",
            ),
            "asunto": correo.get("asunto", ""),
            "cuerpo": correo.get("cuerpo", ""),
            "tipo": "enviado",
        })

    RAG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RAG_PATH.open("w", encoding="utf-8") as archivo:
        for documento in documentos:
            archivo.write(
                json.dumps(
                    documento,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return {
        "ok": True,
        "correos_guardados": len(documentos),
        "archivo": str(RAG_PATH),
    }
