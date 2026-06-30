"""Borra únicamente los datos locales de pruebas."""

from src.parametros import (
    DATABASE_PATH,
    WHATSAPP_LOG_PATH,
)


for ruta in [DATABASE_PATH, WHATSAPP_LOG_PATH]:
    if ruta.exists():
        ruta.unlink()
        print("Eliminado:", ruta)

print("Datos locales de prueba reiniciados.")
