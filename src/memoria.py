"""Memoria mínima para evitar procesar dos veces el mismo correo."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from src import config


def conectar():
    """Crea la carpeta y abre la base de datos SQLite."""

    ruta = Path(config.DATABASE_PATH)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    conexion = sqlite3.connect(ruta)

    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS correos_procesados (
            message_id TEXT PRIMARY KEY,
            fecha_proceso TEXT NOT NULL,
            clasificacion TEXT,
            resumen TEXT,
            resultado_json TEXT,
            draft_id TEXT
        )
        """
    )

    conexion.commit()

    return conexion


def esta_procesado(message_id):
    """Comprueba si el correo ya existe en la memoria."""

    with conectar() as conexion:
        fila = conexion.execute(
            """
            SELECT message_id
            FROM correos_procesados
            WHERE message_id = ?
            """,
            (message_id,),
        ).fetchone()

    return fila is not None


def guardar_resultado(message_id, resultado, draft_id=None):
    """Guarda el resultado del procesamiento."""

    with conectar() as conexion:
        conexion.execute(
            """
            INSERT OR REPLACE INTO correos_procesados (
                message_id,
                fecha_proceso,
                clasificacion,
                resumen,
                resultado_json,
                draft_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                datetime.now().isoformat(timespec="seconds"),
                resultado.get("clasificacion", ""),
                resultado.get("resumen", ""),
                json.dumps(
                    resultado,
                    ensure_ascii=False,
                ),
                draft_id,
            ),
        )

        conexion.commit()
