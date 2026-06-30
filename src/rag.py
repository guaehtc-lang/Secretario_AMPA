"""Consulta del RAG local ya construido."""

import json

from sklearn.feature_extraction.text import (
    TfidfVectorizer,
)
from sklearn.metrics.pairwise import (
    cosine_similarity,
)

from src.parametros import (
    RAG_MIN_SIMILARITY,
    RAG_PATH,
    RAG_RESULTS,
)


# ==========================================
# 1. CARGA DEL RAG
# ==========================================

def cargar_documentos():
    """Lee los correos históricos guardados."""

    if not RAG_PATH.exists():
        return []

    documentos = []

    with RAG_PATH.open(
        encoding="utf-8",
    ) as archivo:
        for linea in archivo:
            linea = linea.strip()

            if not linea:
                continue

            try:
                documento = json.loads(
                    linea
                )
            except json.JSONDecodeError:
                continue

            if isinstance(
                documento,
                dict,
            ):
                documentos.append(
                    documento
                )

    return documentos


# ==========================================
# 2. CONSULTA PARA EL AGENTE
# ==========================================

def consultar_antecedentes_gmail(
    termino_busqueda,
    limite=RAG_RESULTS,
):
    """Busca correos anteriores similares.

    Devuelve un bloque de texto preparado para el LLM.
    No modifica ni actualiza el RAG.
    """

    documentos = cargar_documentos()

    if not documentos:
        return (
            "No hay antecedentes guardados "
            "en el RAG local."
        )

    textos = [
        " ".join([
            documento.get(
                "asunto",
                "",
            ),
            documento.get(
                "cuerpo",
                "",
            ),
        ]).strip()
        for documento in documentos
    ]

    try:
        vectorizador = TfidfVectorizer(
            lowercase=True,
            ngram_range=(
                1,
                2,
            ),
        )

        matriz = vectorizador.fit_transform(
            textos
            + [
                termino_busqueda
            ]
        )

    except ValueError:
        return (
            "No se pudo procesar "
            "el vocabulario del RAG."
        )

    similitudes = cosine_similarity(
        matriz[-1],
        matriz[:-1],
    )[0]

    indices = similitudes.argsort()[
        ::-1
    ]

    resultados = []

    for indice in indices:
        similitud = float(
            similitudes[
                int(
                    indice
                )
            ]
        )

        if (
            similitud
            < RAG_MIN_SIMILARITY
        ):
            continue

        documento = documentos[
            int(
                indice
            )
        ]

        numero = len(
            resultados
        ) + 1

        bloque = (
            f"[Correo histórico {numero}]\n"
            f"Fecha: {documento.get('fecha', '')}\n"
            f"Asunto: {documento.get('asunto', '')}\n"
            f"Destinatario: "
            f"{documento.get('destinatario', '')}\n"
            f"Contenido: "
            f"{documento.get('cuerpo', '')[:1200]}\n"
            f"Similitud: {similitud:.3f}\n"
            f"----------------------------------------"
        )

        resultados.append(
            bloque
        )

        if len(
            resultados
        ) >= max(
            1,
            int(
                limite
            ),
        ):
            break

    if not resultados:
        return (
            "No se encontraron correos "
            "anteriores relevantes "
            "para esta consulta."
        )

    return "\n\n".join(
        resultados
    )
