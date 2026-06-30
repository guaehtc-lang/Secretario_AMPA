"""Carga en el RAG el histórico configurado de Gmail."""

from src.rag import actualizar_rag


if __name__ == "__main__":
    resultado = actualizar_rag()

    print(
        "Correos guardados en el RAG:",
        resultado["correos_guardados"],
    )
    print(
        "Archivo:",
        resultado["archivo"],
    )
