"""Reconstruye el RAG usando correos enviados."""

from src.rag import actualizar_rag


if __name__ == "__main__":
    resultado = actualizar_rag()

    print(
        "Correos enviados guardados en el RAG:",
        resultado["correos_guardados"],
    )
    print("Archivo:", resultado["archivo"])
