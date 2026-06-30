# Secretario AMPA V3.5

Versión simplificada del agente Secretario AMPA.

Python controla el flujo completo. El LLM solo:

- clasifica correos;
- redacta borradores;
- extrae datos de reuniones;
- resume urgencias.

## Estructura

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
├── src/
├── notebooks/
├── docs/
└── data/
```

## Clasificaciones

- `informativo`
- `necesita_respuesta`
- `reunion`
- `urgente_seguridad`
- `no_clasificado`

## Estado leído/no leído

| Clasificación | Estado final |
|---|---|
| `informativo` | No leído |
| `necesita_respuesta` | Leído si se crea el borrador |
| `reunion` | Leído si se procesa correctamente |
| `urgente_seguridad` | Leído si se registra la alerta |
| `no_clasificado` | No leído |

SQLite evita reprocesar correos informativos o no clasificados que
permanecen sin leer.

## RAG

El RAG ya debe existir en:

```text
data/rag/correos_historicos.jsonl
```

El proyecto no incluye un programa para construirlo o actualizarlo.

`src/rag.py` únicamente:

- carga el archivo;
- busca correos similares con TF-IDF;
- devuelve el contexto al agente.

## Instalación

```bash
pip install -r requirements.txt
```

Completa en `.env`:

```text
LLM_API_KEY=
COMPOSIO_API_KEY=
```

Autoriza Google:

```bash
python autorizar_google.py
```

Ejecuta el agente:

```bash
python main.py
```

## Servicio horario

```bash
python servicio.py
```

## Pruebas

El notebook único es:

```text
notebooks/pruebas_secretario_ampa.ipynb
```

Durante las pruebas puede utilizarse:

```bash
python reset_pruebas.py
```

`reset_pruebas.py` debe eliminarse al cerrar la fase de pruebas.

## Restricciones

- No existe función para enviar correos.
- Solo se crean borradores.
- Calendar no crea eventos en V3.5.
- WhatsApp funciona en modo simulado.
- El agente no modifica ni actualiza el RAG.
