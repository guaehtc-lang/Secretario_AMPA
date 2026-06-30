"""Memoria SQLite sencilla para evitar duplicados."""

import json
import sqlite3
from datetime import datetime

from src.parametros import DATABASE_PATH


def conectar():
    """Abre la base de datos local."""

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sqlite3.connect(DATABASE_PATH)


def inicializar_memoria():
    """Crea las tablas necesarias."""

    conexion = conectar()

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS correos (
            message_id TEXT PRIMARY KEY,
            fecha_proceso TEXT NOT NULL,
            clasificacion TEXT NOT NULL,
            resumen TEXT,
            accion TEXT,
            estado_gmail TEXT,
            draft_id TEXT,
            requiere_revision INTEGER,
            error TEXT,
            resultado TEXT
        )
        """
    )

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS alertas (
            message_id TEXT PRIMARY KEY,
            fecha_envio TEXT NOT NULL,
            tipo_riesgo TEXT,
            resumen TEXT,
            modo TEXT,
            resultado TEXT
        )
        """
    )

    conexion.commit()
    conexion.close()


def obtener_ids_procesados():
    """Devuelve los identificadores ya procesados."""

    inicializar_memoria()
    conexion = conectar()

    filas = conexion.execute(
        "SELECT message_id FROM correos"
    ).fetchall()

    conexion.close()

    return [fila[0] for fila in filas]


def registrar_correo(
    message_id,
    clasificacion,
    resumen,
    accion,
    estado_gmail,
    draft_id="",
    requiere_revision=False,
    error="",
    resultado=None,
):
    """Guarda el resultado final de un correo."""

    inicializar_memoria()
    conexion = conectar()

    datos = resultado or {}

    conexion.execute(
        """
        INSERT OR REPLACE INTO correos (
            message_id,
            fecha_proceso,
            clasificacion,
            resumen,
            accion,
            estado_gmail,
            draft_id,
            requiere_revision,
            error,
            resultado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            datetime.now().isoformat(
                timespec="seconds"
            ),
            clasificacion,
            resumen,
            accion,
            estado_gmail,
            draft_id,
            int(bool(requiere_revision)),
            error,
            json.dumps(
                datos,
                ensure_ascii=False,
                default=str,
            ),
        ),
    )

    conexion.commit()
    conexion.close()

    return {
        "ok": True,
        "message_id": message_id,
        "clasificacion": clasificacion,
        "accion": accion,
        "estado_gmail": estado_gmail,
        "requiere_revision": bool(
            requiere_revision
        ),
    }


def alerta_ya_enviada(message_id):
    """Comprueba si una urgencia ya generó alerta."""

    inicializar_memoria()
    conexion = conectar()

    fila = conexion.execute(
        """
        SELECT message_id
        FROM alertas
        WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()

    conexion.close()

    return fila is not None


def registrar_alerta(
    message_id,
    tipo_riesgo,
    resumen,
    modo,
    resultado,
):
    """Registra una alerta de WhatsApp."""

    inicializar_memoria()
    conexion = conectar()

    conexion.execute(
        """
        INSERT OR REPLACE INTO alertas (
            message_id,
            fecha_envio,
            tipo_riesgo,
            resumen,
            modo,
            resultado
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            datetime.now().isoformat(
                timespec="seconds"
            ),
            tipo_riesgo,
            resumen,
            modo,
            json.dumps(
                resultado,
                ensure_ascii=False,
                default=str,
            ),
        ),
    )

    conexion.commit()
    conexion.close()
