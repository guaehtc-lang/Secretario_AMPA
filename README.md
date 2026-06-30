# Secretario AMPA V0.3

Versión simplificada y controlada por Python.
El LLM ya no elige herramientas ni controla el bucle.

## Estructura principal

```text
main.py
  ├── src/prompt.py      → carga varios prompts
  ├── src/tools.py       → catálogo de tools internas
  ├── src/funciones.py   → funciones Python registradas
  └── src/agente.py      → flujo controlado por Python
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
| Informativo | No leído |
| Necesita respuesta | Leído si se crea el borrador |
| Reunión | Leído si se crea el borrador o se registra confirmación/rechazo |
| Urgencia | Leído si se registra la alerta de WhatsApp |
| No clasificado | No leído |

SQLite impide reprocesar los mensajes informativos o no clasificados que permanecen no leídos.

## Primera ejecución

1. Completa las claves en `.env`:

```text
LLM_API_KEY=
COMPOSIO_API_KEY=
```

2. Instala dependencias:

```bash
pip install -r requirements.txt
```

3. Autoriza Google:

```bash
python autorizar_google.py
```

4. Crea el RAG separado:

```bash
python actualizar_rag.py
```

5. Ejecuta el agente:

```bash
python main.py
```

## RAG separado

`actualizar_rag.py` construye el histórico usando correos enviados.
El agente solo ejecuta `consultar_rag()` cuando necesita redactar una respuesta.

## Calendar

V0.3 consulta disponibilidad y crea un borrador con propuestas.
No crea eventos ni envía invitaciones automáticas.

## WhatsApp

V0.3 utiliza `WHATSAPP_MODE=simulado`.
La alerta se muestra en consola y se guarda localmente, pero no se envía a teléfonos reales.

## Seguridad

- No existe función para enviar correos.
- Los borradores requieren revisión humana.
- Calendar no crea eventos.
- El LLM no recibe herramientas.
- Python controla todas las acciones externas.
