"""RAG local basado en correos enviados del histórico."""

import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.composio_cliente import obtener_sesion_google
from src.gmail import preparar_correo
from src.parametros import (
    RAG_ANIOS_HISTORIAL,
    RAG_MAX_CORREOS,
    RAG_RESULTADOS,
    RAG_SIMILITUD_MINIMA,
    RAG_SOLO_ENVIADOS,
    RUTA_RAG,
)
from src.utilidades import (
    buscar_ids,
    buscar_valor,
    convertir_resultado,
    extraer_email,
)


CONTEXTO_RAG = {}

CLASIFICACIONES_CON_RAG = {
    "requiere_respuesta",
    "solicitud_reunion",
    "rechazo_reunion",
}


def cargar_documentos():
    """Lee los correos históricos guardados."""

    if not RUTA_RAG.exists():
        return []

    documentos = []

    with RUTA_RAG.open(
        encoding="utf-8"
    ) as archivo:
        for linea in archivo:
            linea = linea.strip()

            if linea:
                documentos.append(
                    json.loads(
                        linea
                    )
                )

    return documentos


def obtener_contexto_rag(message_id):
    """Devuelve el contexto recuperado durante el ciclo actual."""

    return CONTEXTO_RAG.get(
        message_id
    )


def guardar_contexto(
    message_id,
    consulta,
    resultados,
    estado,
):
    """Guarda temporalmente el resultado para crear el borrador."""

    CONTEXTO_RAG[message_id] = {
        "consulta": consulta,
        "resultados": resultados,
        "estado": estado,
    }


def buscar_contexto_rag(
    message_id,
    consulta,
    clasificacion,
    limite=RAG_RESULTADOS,
):
    """Recupera respuestas históricas enviadas y relevantes."""

    clasificacion = (
        clasificacion
        or ""
    ).strip().lower()

    if (
        clasificacion
        not in CLASIFICACIONES_CON_RAG
    ):
        return {
            "ok": False,
            "estado": (
                "rag_bloqueado_"
                "por_clasificacion"
            ),
            "clasificacion": clasificacion,
            "resultados": [],
        }

    from src.gmail import obtener_correo_por_id

    correo_actual = obtener_correo_por_id(
        message_id
    )

    consulta_real = " ".join([
        correo_actual.get(
            "asunto",
            "",
        ),
        correo_actual.get(
            "cuerpo",
            "",
        ),
        consulta or "",
    ]).strip()

    documentos = cargar_documentos()

    documentos_validos = []

    for documento in documentos:
        if (
            documento.get(
                "message_id"
            )
            == message_id
        ):
            continue

        if RAG_SOLO_ENVIADOS:
            if (
                documento.get(
                    "tipo"
                )
                != "enviado"
            ):
                continue

            if (
                documento.get(
                    "fuente_validada"
                )
                is not True
            ):
                continue

        texto = " ".join([
            documento.get(
                "asunto",
                "",
            ),
            documento.get(
                "cuerpo",
                "",
            ),
        ]).strip()

        if texto:
            documentos_validos.append(
                documento
            )

    if not documentos_validos:
        estado = (
            "sin_respuestas_historicas_"
            "validas"
        )

        guardar_contexto(
            message_id,
            consulta_real,
            [],
            estado,
        )

        return {
            "ok": True,
            "estado": estado,
            "resultados": [],
        }

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
        ])
        for documento in documentos_validos
    ]

    try:
        vectorizador = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
        )

        matriz = vectorizador.fit_transform(
            textos
            + [consulta_real]
        )

    except ValueError:
        estado = "rag_sin_vocabulario"

        guardar_contexto(
            message_id,
            consulta_real,
            [],
            estado,
        )

        return {
            "ok": True,
            "estado": estado,
            "resultados": [],
        }

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
                indice
            ]
        )

        if (
            similitud
            < RAG_SIMILITUD_MINIMA
        ):
            continue

        documento = documentos_validos[
            int(indice)
        ]

        resultados.append({
            "message_id": documento.get(
                "message_id",
                "",
            ),
            "fecha": documento.get(
                "fecha",
                "",
            ),
            "asunto": documento.get(
                "asunto",
                "",
            ),
            "remitente": documento.get(
                "remitente",
                "",
            ),
            "cuerpo": documento.get(
                "cuerpo",
                "",
            )[:1600],
            "tipo": documento.get(
                "tipo",
                "",
            ),
            "fuente_validada": (
                documento.get(
                    "fuente_validada"
                )
                is True
            ),
            "similitud": round(
                similitud,
                3,
            ),
        })

        if (
            len(resultados)
            >= max(
                1,
                int(limite),
            )
        ):
            break

    estado = (
        "contexto_recuperado"
        if resultados
        else "sin_antecedentes_relevantes"
    )

    guardar_contexto(
        message_id,
        consulta_real,
        resultados,
        estado,
    )

    return {
        "ok": True,
        "estado": estado,
        "umbral": RAG_SIMILITUD_MINIMA,
        "resultados": resultados,
    }


def actualizar_rag():
    """Descarga únicamente correos enviados, nunca borradores."""

    sesion = obtener_sesion_google()

    perfil = convertir_resultado(
        sesion.execute(
            "GMAIL_GET_PROFILE",
            arguments={
                "user_id": "me",
            },
        )
    )

    correo_cuenta = buscar_valor(
        perfil,
        [
            "emailAddress",
            "email_address",
            "email",
        ],
    ) or ""

    dias = (
        365
        * RAG_ANIOS_HISTORIAL
    )

    query = (
        f"in:sent newer_than:{dias}d"
    )

    ids = []
    page_token = ""

    while (
        len(ids)
        < RAG_MAX_CORREOS
    ):
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
                        RAG_MAX_CORREOS
                        - len(ids),
                    ),
                    "page_token": page_token,
                    "query": query,
                    "user_id": "me",
                    "verbose": False,
                },
            )
        )

        nuevos_ids = buscar_ids(
            resultado
        )

        for message_id in nuevos_ids:
            if (
                message_id
                not in ids
            ):
                ids.append(
                    message_id
                )

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

    documentos = []

    for message_id in ids[
        :RAG_MAX_CORREOS
    ]:
        resultado = sesion.execute(
            "GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID",
            arguments={
                "format": "full",
                "message_id": message_id,
                "user_id": "me",
            },
        )

        correo = preparar_correo(
            resultado
        )

        labels = set(
            correo.get(
                "labels",
                [],
            )
        )

        if "DRAFT" in labels:
            continue

        if "SENT" not in labels:
            continue

        documentos.append({
            "message_id": (
                correo[
                    "message_id"
                ]
                or message_id
            ),
            "thread_id": correo[
                "thread_id"
            ],
            "fecha": correo[
                "fecha"
            ],
            "remitente": correo[
                "remitente"
            ],
            "destinatario": correo[
                "destinatario"
            ],
            "asunto": correo[
                "asunto"
            ],
            "cuerpo": correo[
                "cuerpo"
            ],
            "labels": sorted(
                labels
            ),
            "tipo": "enviado",
            "fuente_validada": True,
        })

    RUTA_RAG.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RUTA_RAG.open(
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

    return {
        "ok": True,
        "correos_guardados": len(
            documentos
        ),
        "correos_enviados": len(
            documentos
        ),
        "cuenta": correo_cuenta,
        "archivo": str(
            RUTA_RAG
        ),
    }
