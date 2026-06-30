# Esquema de funcionamiento

```text
                     ┌──────────────────────┐
                     │       main.py        │
                     └──────────┬───────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
   prompt.py              parametros.py             tools.py
          │                     │                     │
          ▼                     ▼                     ▼
 prompt_agente.txt          .env                  lista tools
          │                                           │
          └─────────────────┬─────────────────────────┘
                            ▼
                 ┌──────────────────────┐
                 │ ejecutar_agente(...) │
                 │      agente.py       │
                 └──────────┬───────────┘
                            │
                            ▼
                     funciones.py
                            │
          ┌─────────────────┼──────────────────┐
          ▼                 ▼                  ▼
       gmail.py         calendar.py          rag.py
          │                 │                  │
          ▼                 ▼                  ▼
        Gmail        Google Calendar     histórico JSONL
                            │
                            ▼
                       memoria.py
                          SQLite
```

## Flujo de un correo

```text
leer correo
   ↓
recuperar hilo
   ↓
LLM clasifica
   ├── informativo → registrar
   ├── respuesta → consultar RAG → crear borrador → registrar
   ├── reunión → consultar Calendar → crear invitación → registrar
   ├── contrapropuesta → volver a consultar Calendar
   └── revisión manual → registrar sin acción externa
```
