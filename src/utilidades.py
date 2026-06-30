"""Funciones auxiliares compartidas."""

import json
import re
from email.utils import parsedate_to_datetime


def convertir_resultado(resultado):
    """Convierte una respuesta externa en diccionario."""

    if hasattr(
        resultado,
        "model_dump",
    ):
        resultado = resultado.model_dump()

    if isinstance(
        resultado,
        dict,
    ):
        return resultado

    if isinstance(
        resultado,
        str,
    ):
        try:
            return json.loads(
                resultado
            )

        except json.JSONDecodeError:
            return {
                "texto": resultado
            }

    return {
        "texto": str(resultado)
    }


def buscar_ids(objeto):
    """Busca identificadores de mensajes de Gmail."""

    ids = []

    if isinstance(
        objeto,
        dict,
    ):
        for clave, valor in objeto.items():

            if (
                clave
                in [
                    "messageId",
                    "message_id",
                ]
                and isinstance(
                    valor,
                    str,
                )
            ):
                ids.append(
                    valor
                )

            elif (
                clave == "id"
                and isinstance(
                    valor,
                    str,
                )
                and not valor.startswith(
                    "log_"
                )
            ):
                ids.append(
                    valor
                )

            elif isinstance(
                valor,
                (dict, list),
            ):
                ids += buscar_ids(
                    valor
                )

    elif isinstance(
        objeto,
        list,
    ):
        for elemento in objeto:
            ids += buscar_ids(
                elemento
            )

    return list(
        dict.fromkeys(ids)
    )


def buscar_mensajes(objeto):
    """Busca la lista messages dentro de una respuesta."""

    if isinstance(
        objeto,
        dict,
    ):
        mensajes = objeto.get(
            "messages"
        )

        if isinstance(
            mensajes,
            list,
        ):
            return mensajes

        for valor in objeto.values():
            encontrados = buscar_mensajes(
                valor
            )

            if encontrados:
                return encontrados

    elif isinstance(
        objeto,
        list,
    ):
        for elemento in objeto:
            encontrados = buscar_mensajes(
                elemento
            )

            if encontrados:
                return encontrados

    return []


def buscar_valor(objeto, claves):
    """Busca recursivamente el primer valor solicitado."""

    if isinstance(
        objeto,
        dict,
    ):
        for clave in claves:
            valor = objeto.get(
                clave
            )

            if valor not in [
                None,
                "",
                [],
                {},
            ]:
                return valor

        for valor in objeto.values():
            encontrado = buscar_valor(
                valor,
                claves,
            )

            if encontrado not in [
                None,
                "",
                [],
                {},
            ]:
                return encontrado

    elif isinstance(
        objeto,
        list,
    ):
        for elemento in objeto:
            encontrado = buscar_valor(
                elemento,
                claves,
            )

            if encontrado not in [
                None,
                "",
                [],
                {},
            ]:
                return encontrado

    return None


def obtener_cabecera(headers, nombre):
    """Obtiene una cabecera de Gmail."""

    for header in headers:
        if (
            header.get(
                "name",
                "",
            ).lower()
            == nombre.lower()
        ):
            return header.get(
                "value",
                "",
            )

    return ""


def extraer_email(texto):
    """Extrae una dirección de correo."""

    coincidencia = re.search(
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}",
        texto or "",
    )

    if coincidencia:
        return coincidencia.group(
            0
        )

    return ""


def timestamp_fecha(texto):
    """Convierte una fecha de correo en timestamp."""

    try:
        return parsedate_to_datetime(
            texto
        ).timestamp()

    except (
        TypeError,
        ValueError,
    ):
        return 0
