# Guía técnica y de funcionamiento
## Secretario AMPA V3.5

## 1. Objetivo

Secretario AMPA gestiona de forma asistida el correo del AMPA.

El agente:

- lee correos no leídos;
- los procesa por orden cronológico;
- los clasifica;
- crea borradores cuando necesitan respuesta;
- consulta un RAG local ya construido;
- consulta disponibilidad en Calendar;
- simula alertas de WhatsApp;
- registra las acciones en SQLite.

Python controla el flujo. El LLM no elige herramientas.

## 2. Clasificaciones

- `informativo`
- `necesita_respuesta`
- `reunion`
- `urgente_seguridad`
- `no_clasificado`

## 3. Flujos

### Informativo

```text
leer → clasificar → registrar → mantener no leído
```

### Necesita respuesta

```text
leer → clasificar → consultar RAG → redactar →
crear borrador → marcar leído → registrar
```

### Reunión

```text
leer → clasificar → extraer datos → consultar Calendar →
redactar propuesta → crear borrador → marcar leído → registrar
```

Calendar no crea eventos en V3.5.

### Urgencia

```text
leer → clasificar → resumir → registrar WhatsApp simulado →
marcar leído → registrar
```

### No clasificado

```text
leer → clasificar → registrar para revisión →
mantener no leído
```

## 4. RAG

El archivo del RAG es:

```text
data/rag/correos_historicos.jsonl
```

El proyecto no construye ni actualiza el RAG.

`src/rag.py` solo contiene:

- `cargar_documentos()`
- `consultar_antecedentes_gmail()`

La búsqueda utiliza TF-IDF y similitud coseno.

## 5. Estructura

```text
Secretario_AMPA/
├── main.py
├── autorizar_google.py
├── servicio.py
├── reset_pruebas.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
├── prompts/
│   ├── reglas_comunes.txt
│   ├── prompt_clasificacion.txt
│   ├── prompt_redaccion.txt
│   ├── prompt_reunion.txt
│   └── prompt_whatsapp.txt
├── src/
│   ├── agente.py
│   ├── parametros.py
│   ├── prompts.py
│   ├── funciones.py
│   ├── tools.py
│   ├── llm.py
│   ├── gmail.py
│   ├── calendar.py
│   ├── whatsapp.py
│   ├── rag.py
│   └── memoria.py
├── notebooks/
│   └── pruebas_secretario_ampa.ipynb
├── docs/
│   ├── GUIA_TECNICA_Y_FUNCIONAMIENTO.md
│   └── ESTADO_Y_PENDIENTES_V3.5.md
└── data/
    ├── secretario_ampa.db
    └── rag/
        └── correos_historicos.jsonl
```

## 6. Restricciones

- Nunca envía correos.
- Solo crea borradores.
- No crea eventos.
- WhatsApp es simulado.
- No modifica el RAG.
- `reset_pruebas.py` es temporal.
