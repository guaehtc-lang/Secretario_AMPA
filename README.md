# Secretario AMPA

Proyecto reorganizado con la estructura de function calling vista
en clase.

## Idea principal

`main.py` solo reúne las piezas:

```python
mensajes = crear_mensajes()

print(
    ejecutar_agente(
        mensajes,
        tools,
        funciones,
    )
)
```

Cada parte se modifica en un archivo independiente:

| Necesidad | Archivo |
|---|---|
| Cambiar comportamiento del agente | `prompts/prompt_agente.txt` |
| Cambiar modelo, temperatura o límites | `src/parametros.py` |
| Añadir o modificar tools | `src/tools.py` |
| Registrar funciones disponibles | `src/funciones.py` |
| Cambiar el bucle del agente | `src/agente.py` |
| Cambiar Gmail | `src/gmail.py` |
| Cambiar Calendar | `src/calendar.py` |
| Cambiar el RAG | `src/rag.py` |
| Cambiar la memoria | `src/memoria.py` |

## Estructura

```text
main.py
   ├── prompt.py ── prompts/prompt_agente.txt
   ├── parametros.py ── .env
   ├── tools.py
   ├── funciones.py
   │     ├── gmail.py
   │     ├── calendar.py
   │     ├── rag.py
   │     └── memoria.py
   └── agente.py
```

## Primera configuración

1. Copia `.env.example` como `.env`.
2. Añade `LLM_API_KEY` y `COMPOSIO_API_KEY`.
3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Autoriza Google:

```bash
python autorizar_google.py
```

5. Carga el histórico del último año:

```bash
python actualizar_rag.py
```

6. Ejecuta un ciclo:

```bash
python main.py
```

7. Servicio horario:

```bash
python servicio.py
```

## Cómo ampliar el agente

Para añadir una herramienta:

1. Crea su función en el archivo del área correspondiente.
2. Añade su descripción en `src/tools.py`.
3. Registra la función en `src/funciones.py`.
4. Añade al prompt una regla únicamente si el agente necesita saber
   cuándo utilizarla.

No hay que modificar `main.py` ni el bucle general del agente.

## RAG

El histórico se guarda localmente en:

```text
data/rag/correos_historicos.jsonl
```

El número de años se cambia en `.env` o `src/parametros.py`:

```text
RAG_ANIOS_HISTORIAL=1
```

Para pasar a cinco años:

```text
RAG_ANIOS_HISTORIAL=5
```

Después se vuelve a ejecutar `actualizar_rag.py`.

## Seguridad actual

- No existe ninguna tool para enviar correos.
- Gmail solo puede leer y crear borradores.
- Calendar puede consultar disponibilidad y enviar invitaciones
  con Sí, No y Quizás.
- Los eventos se vuelven a comprobar antes de crearse.
- SQLite evita reprocesar correos y duplicar eventos.
