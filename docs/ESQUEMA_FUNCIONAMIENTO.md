# Esquema de funcionamiento V0.3

```text
main.py
  ↓
carga prompts + tools + funciones
  ↓
Gmail obtiene no leídos por fecha ascendente
  ↓
LLM clasifica
  ↓
Python selecciona el flujo
  ├── informativo → registrar → conservar no leído
  ├── respuesta → RAG → redactar → borrador → leído
  ├── reunión → extraer → Calendar → borrador → leído
  ├── urgencia → resumen → WhatsApp simulado → leído
  └── no clasificado → registrar → conservar no leído
```

El LLM nunca decide qué función se ejecuta.
