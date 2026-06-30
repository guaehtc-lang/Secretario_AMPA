"""Reinicia únicamente la memoria local de pruebas.

Archivo temporal: eliminar al cerrar la fase de pruebas.
"""

from src.memoria import inicializar_memoria
from src.parametros import DATABASE_PATH


if DATABASE_PATH.exists():
    DATABASE_PATH.unlink()
    print("Eliminado:", DATABASE_PATH)

inicializar_memoria()
print("Base de datos de pruebas reiniciada.")
