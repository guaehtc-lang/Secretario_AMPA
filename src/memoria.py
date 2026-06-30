"""Memoria estructurada SQLite."""

import json
import sqlite3
from datetime import datetime

from src.parametros import RUTA_BD


def convertir_booleano(valor):
    """Convierte booleanos, números y textos a True o False."""

    if isinstance(
        valor,
        bool,
    ):
        return valor

    if isinstance(
        valor,
        str,
    ):
        return valor.strip().lower() in {
            "true",
            "1",
            "sí",
            "si",
            "yes",
        }

    return bool(
        valor
    )


def limpiar_resumen(
    resumen,
    clasificacion,
):
    """Evita guardar acciones como si fueran el resumen."""

    resumen = (
        resumen
        or ""
    ).strip()

    texto = resumen.lower()

    if (
        clasificacion
        == "rechazo_reunion"
        and (
            "correo fue rechazado"
            in texto
            or "correo rechazado"
            in texto
        )
    ):
        return (
            "Reunión rechazada por el invitado"
        )

    if (
        clasificacion
        == "confirmacion_reunion"
        and (
            "correo fue confirmado"
            in texto
            or "correo confirmado"
            in texto
        )
    ):
        return (
            "Reunión confirmada por el invitado"
        )

    frases_incorrectas = [
        "se respondió",
        "se respondio",
        "correo respondido",
        "respuesta enviada",
    ]

    if any(
        frase in texto
        for frase in frases_incorrectas
    ):
        if (
            clasificacion
            == "requiere_respuesta"
        ):
            return (
                "Correo que requiere respuesta"
            )

        return "Correo procesado"

    return resumen


def conectar():
    """Abre la base de datos."""

    RUTA_BD.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sqlite3.connect(
        RUTA_BD
    )


def inicializar_memoria():
    """Crea las tablas y columnas necesarias."""

    conexion = conectar()

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS correos (
            message_id TEXT PRIMARY KEY,
            fecha TEXT NOT NULL,
            clasificacion TEXT,
            resumen TEXT,
            acciones_realizadas TEXT,
            estado_reunion TEXT,
            requiere_revision INTEGER,
            resultado TEXT
        )
        """
    )

    columnas = [
        fila[1]
        for fila in conexion.execute(
            "PRAGMA table_info(correos)"
        ).fetchall()
    ]

    if (
        "acciones_realizadas"
        not in columnas
    ):
        conexion.execute(
            """
            ALTER TABLE correos
            ADD COLUMN acciones_realizadas TEXT
            """
        )

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS acciones (
            message_id TEXT NOT NULL,
            tipo TEXT NOT NULL,
            detalle TEXT,
            fecha TEXT NOT NULL,
            PRIMARY KEY (message_id, tipo)
        )
        """
    )

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS eventos (
            message_id TEXT PRIMARY KEY,
            event_id TEXT,
            inicio TEXT,
            invitado TEXT,
            estado TEXT,
            fecha_registro TEXT
        )
        """
    )

    conexion.commit()
    conexion.close()


def obtener_ids_procesados():
    """Devuelve los correos ya procesados."""

    inicializar_memoria()
    conexion = conectar()

    filas = conexion.execute(
        """
        SELECT message_id
        FROM correos
        """
    ).fetchall()

    conexion.close()

    return [
        fila[0]
        for fila in filas
    ]


def registrar_accion(
    message_id,
    tipo,
    detalle="",
):
    """Registra una acción realmente ejecutada."""

    inicializar_memoria()
    conexion = conectar()

    conexion.execute(
        """
        INSERT OR REPLACE INTO acciones (
            message_id,
            tipo,
            detalle,
            fecha
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            message_id,
            tipo,
            detalle,
            datetime.now().isoformat(
                timespec="seconds"
            ),
        ),
    )

    conexion.commit()
    conexion.close()


def obtener_acciones(message_id):
    """Devuelve las acciones reales de un correo."""

    inicializar_memoria()
    conexion = conectar()

    filas = conexion.execute(
        """
        SELECT tipo, detalle
        FROM acciones
        WHERE message_id = ?
        ORDER BY fecha
        """,
        (message_id,),
    ).fetchall()

    conexion.close()

    return [
        {
            "tipo": fila[0],
            "detalle": fila[1],
        }
        for fila in filas
    ]


def describir_acciones(
    clasificacion,
    acciones,
    contrapropuesta_reunion=False,
):
    """Convierte acciones reales en una descripción segura."""

    tipos = {
        accion["tipo"]
        for accion in acciones
    }

    descripciones = []

    if "borrador_creado" in tipos:
        descripciones.append(
            "Borrador creado para revisión humana"
        )

    if "invitacion_calendar_creada" in tipos:
        if (
            clasificacion
            == "rechazo_reunion"
            and contrapropuesta_reunion
        ):
            descripciones.append(
                "Nueva invitación de Google Calendar "
                "creada para la contrapropuesta"
            )

        else:
            descripciones.append(
                "Invitación de Google Calendar creada "
                "y enviada al solicitante"
            )

    if descripciones:
        return "; ".join(
            descripciones
        )

    if clasificacion == "informativo":
        return (
            "Registrado sin borrador "
            "ni acción externa"
        )

    if clasificacion == "revision_manual":
        return (
            "Bloqueado y registrado para revisión humana "
            "sin acción externa"
        )

    if clasificacion == "urgencia_seguridad":
        return (
            "Urgencia de seguridad registrada "
            "para revisión inmediata"
        )

    if clasificacion == "confirmacion_reunion":
        return (
            "Confirmación de reunión registrada"
        )

    if clasificacion == "rechazo_reunion":
        return (
            "Rechazo de reunión registrado"
        )

    return "Registrado sin acción externa"


def registrar_resultado(
    message_id,
    clasificacion,
    resumen,
    acciones_realizadas="",
    estado_reunion="",
    requiere_revision=False,
):
    """Guarda el resultado usando la clasificación validada."""

    from src.clasificacion import (
        obtener_clasificacion_validada,
    )

    clasificacion_validada = (
        obtener_clasificacion_validada(
            message_id
        )
    )

    if not clasificacion_validada:
        return {
            "ok": False,
            "estado": (
                "clasificacion_no_validada"
            ),
            "mensaje": (
                "Debes ejecutar clasificar_correo "
                "antes de registrar el resultado."
            ),
        }

    if (
        clasificacion
        != clasificacion_validada
    ):
        return {
            "ok": False,
            "estado": (
                "clasificacion_incorrecta"
            ),
            "clasificacion_validada": (
                clasificacion_validada
            ),
            "mensaje": (
                "Continúa usando la "
                "clasificación validada."
            ),
        }

    requiere_revision = convertir_booleano(
        requiere_revision
    )

    resumen = limpiar_resumen(
        resumen,
        clasificacion,
    )

    estados_reunion = {
        "solicitud_reunion": "pendiente",
        "confirmacion_reunion": "confirmada",
        "rechazo_reunion": "rechazada",
    }

    estado_reunion = estados_reunion.get(
        clasificacion,
        "",
    )

    inicializar_memoria()
    conexion = conectar()

    existente = conexion.execute(
        """
        SELECT message_id
        FROM correos
        WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()

    conexion.close()

    if existente:
        return {
            "ok": True,
            "registrado": False,
            "estado": "resultado_ya_registrado",
            "message_id": message_id,
        }

    acciones = obtener_acciones(
        message_id
    )

    contrapropuesta_reunion = False

    if (
        clasificacion
        == "rechazo_reunion"
    ):
        from src.clasificacion import (
            obtener_contrapropuesta_reunion,
        )

        contrapropuesta_reunion = (
            obtener_contrapropuesta_reunion(
                message_id
            )
        )

    tipos = {
        accion["tipo"]
        for accion in acciones
    }

    acciones_reales = describir_acciones(
        clasificacion,
        acciones,
        contrapropuesta_reunion,
    )

    if "borrador_creado" in tipos:
        requiere_revision = True

    if clasificacion == "revision_manual":
        requiere_revision = True
        resumen = (
            "Posible intento de manipulación del agente "
            "o solicitud de información sensible"
        )

    if clasificacion == "urgencia_seguridad":
        requiere_revision = True

    if (
        clasificacion
        == "requiere_respuesta"
        and "borrador_creado"
        not in tipos
    ):
        requiere_revision = True

    if (
        clasificacion
        == "solicitud_reunion"
        and "invitacion_calendar_creada"
        not in tipos
    ):
        requiere_revision = True

    if (
        clasificacion
        == "rechazo_reunion"
    ):
        if (
            contrapropuesta_reunion
            and "invitacion_calendar_creada"
            not in tipos
        ):
            requiere_revision = True

        if not contrapropuesta_reunion:
            requiere_revision = False

        if (
            contrapropuesta_reunion
            and "invitacion_calendar_creada"
            in tipos
        ):
            estado_reunion = "pendiente"
            requiere_revision = False

    if (
        clasificacion
        == "confirmacion_reunion"
    ):
        requiere_revision = False

    resultado = {
        "message_id": message_id,
        "clasificacion": clasificacion,
        "resumen": resumen,
        "acciones_realizadas": acciones_reales,
        "estado_reunion": estado_reunion,
        "contrapropuesta_reunion": (
            contrapropuesta_reunion
        ),
        "requiere_revision": requiere_revision,
    }

    conexion = conectar()

    conexion.execute(
        """
        INSERT INTO correos (
            message_id,
            fecha,
            clasificacion,
            resumen,
            acciones_realizadas,
            estado_reunion,
            requiere_revision,
            resultado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            datetime.now().isoformat(
                timespec="seconds"
            ),
            clasificacion,
            resumen,
            acciones_reales,
            estado_reunion,
            int(
                requiere_revision
            ),
            json.dumps(
                resultado,
                ensure_ascii=False,
            ),
        ),
    )

    conexion.commit()
    conexion.close()

    return {
        "ok": True,
        "registrado": True,
        "estado": "resultado_registrado",
        **resultado,
    }


def evento_existente(message_id):
    """Comprueba si el correo ya generó un evento."""

    inicializar_memoria()
    conexion = conectar()

    fila = conexion.execute(
        """
        SELECT event_id, inicio, invitado, estado
        FROM eventos
        WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()

    conexion.close()

    if not fila:
        return None

    return {
        "event_id": fila[0],
        "inicio": fila[1],
        "invitado": fila[2],
        "estado": fila[3],
    }


def registrar_evento(
    message_id,
    event_id,
    inicio,
    invitado,
    estado,
):
    """Guarda la relación entre correo y evento."""

    inicializar_memoria()
    conexion = conectar()

    conexion.execute(
        """
        INSERT OR REPLACE INTO eventos (
            message_id,
            event_id,
            inicio,
            invitado,
            estado,
            fecha_registro
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            event_id,
            inicio,
            invitado,
            estado,
            datetime.now().isoformat(
                timespec="seconds"
            ),
        ),
    )

    conexion.commit()
    conexion.close()
