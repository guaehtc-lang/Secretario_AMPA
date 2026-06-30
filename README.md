# Secretario AMPA V3.9

Versión local en revisión del agente **Secretario AMPA**.

El proyecto supervisa el correo del AMPA, clasifica los mensajes, prepara borradores, consulta Google Calendar, gestiona alertas urgentes mediante Telegram y conserva el estado del procesamiento en SQLite.

La V3.9 se revisa y valida todavía en local. El despliegue permanente mediante `systemd` se realizará posteriormente en la V4.0.

---

## 1. Funcionamiento general

Python controla el flujo completo del agente. El LLM se utiliza únicamente para:

- clasificar correos;
- redactar borradores;
- extraer datos de reuniones;
- resumir posibles urgencias de seguridad.

Las acciones externas se ejecutan mediante funciones controladas por Python y permisos definidos en `.env`.

### Ciclo de Gmail

El agente busca correos no leídos y los clasifica como:

- `informativo`;
- `necesita_respuesta`;
- `reunion`;
- `urgente_seguridad`;
- `no_clasificado`.

### Ciclo de Telegram

Telegram se consulta con una frecuencia independiente de Gmail. En una urgencia:

1. Se crea un borrador en Gmail.
2. Se envía una alerta al chat autorizado.
3. El usuario puede revisar el borrador desde Telegram.
4. El correo solo se envía si el usuario pulsa la autorización final y `ALLOW_EMAIL_SEND=true`.
5. Si se rechaza el envío, el borrador permanece en Gmail para revisión manual.

Los correos administrativos ordinarios no se envían automáticamente.

---

## 2. Acciones según la clasificación

| Clasificación | Acción principal | Estado final habitual |
|---|---|---|
| `informativo` | Registrar sin crear borrador | No leído |
| `necesita_respuesta` | Consultar RAG y crear borrador | Leído si el borrador se crea |
| `reunion` | Extraer datos, consultar Calendar y crear borrador; si es una confirmación, puede crear el evento | Leído si termina correctamente |
| `urgente_seguridad` | Crear borrador, avisar por Telegram y solicitar revisión | Leído si se crea el borrador y se envía la alerta |
| `no_clasificado` | Dejar para revisión humana | No leído |

SQLite evita reprocesar correos ya registrados aunque permanezcan sin leer.

---

## 3. Reuniones y Google Calendar

El agente diferencia entre:

- solicitud de reunión;
- cambio de fecha;
- confirmación;
- rechazo;
- información insuficiente.

Para una solicitud o cambio:

1. Extrae las fechas y horas propuestas.
2. Consulta la disponibilidad en Google Calendar.
3. Crea un borrador de respuesta.

Para una confirmación puede crear el evento si:

```text
ALLOW_CREATE_EVENTS=true
```

Con el permiso en `false`, la creación del evento queda bloqueada.

---

## 4. RAG local

El RAG utiliza correos enviados anteriormente para aportar ejemplos de estilo y antecedentes al redactar respuestas.

El archivo real se genera en:

```text
data/rag/correos_historicos.jsonl
```

Se crea manualmente mediante:

```bash
python crear_rag.py
```

`crear_rag.py`:

- consulta los correos enviados de Gmail;
- elimina el contenido citado de conversaciones anteriores;
- descarta borradores y duplicados;
- guarda los correos válidos en formato JSONL.

El RAG real contiene información privada y está excluido de Git mediante `.gitignore`.

Si el archivo no existe, el agente continúa funcionando, pero las respuestas ordinarias sin antecedentes utilizan una respuesta neutral.

---

## 5. Memoria SQLite

La memoria se guarda en:

```text
data/secretario_ampa.db
```

La base de datos se crea automáticamente al iniciar el agente y conserva, entre otros datos:

- correos procesados;
- clasificación y acción realizada;
- identificadores de borradores;
- errores y revisiones pendientes;
- estado de las alertas urgentes;
- offset de Telegram.

La base de datos es local, persistente y está excluida de Git.

---

## 6. Estructura del proyecto

```text
Secretario_AMPA/
├── main.py
├── servicio.py
├── autorizar_google.py
├── crear_rag.py
├── reset_pruebas.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
├── prompts/
│   ├── reglas_comunes.txt
│   ├── prompt_clasificacion.txt
│   ├── prompt_redaccion.txt
│   ├── prompt_reunion.txt
│   └── prompt_telegram.txt
├── src/
│   ├── agente.py
│   ├── calendar.py
│   ├── funciones.py
│   ├── gmail.py
│   ├── llm.py
│   ├── memoria.py
│   ├── parametros.py
│   ├── prompts.py
│   ├── rag.py
│   ├── telegram.py
│   └── tools.py
├── data/
│   ├── secretario_ampa.db
│   └── rag/
│       └── correos_historicos.jsonl
├── notebooks/
└── docs/
```

`reset_pruebas.py`, el notebook y la documentación antigua se mantienen temporalmente mientras se completa la revisión de la V3.9. Al cerrar la versión se decidirá qué elementos deben eliminarse o actualizarse.

---

## 7. Instalación local

### 7.1. Crear y activar un entorno virtual

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 7.2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 7.3. Crear `.env`

Copia `.env.example` como `.env` y completa las claves privadas:

```text
LLM_API_KEY=
COMPOSIO_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

No debe subirse `.env` a GitHub.

### 7.4. Autorizar Gmail y Google Calendar

```bash
python autorizar_google.py
```

El script solicita la autorización de:

- Gmail;
- Google Calendar.

### 7.5. Crear el RAG

Este paso es opcional para las pruebas, pero necesario para aprovechar antecedentes reales:

```bash
python crear_rag.py
```

---

## 8. Ejecución

### Un único ciclo

```bash
python main.py
```

Procesa las autorizaciones pendientes de Telegram y los correos no leídos encontrados en ese momento.

### Servicio local continuo

```bash
python servicio.py
```

`servicio.py` mantiene dos frecuencias independientes:

```text
TELEGRAM_CHECK_SECONDS=15
GMAIL_CHECK_SECONDS=30
```

Los valores reales se leen desde `.env` y podrán modificarse cuando se utilice la cuenta definitiva del AMPA.

---

## 9. Permisos de seguridad

Las acciones sensibles se controlan desde `.env`:

```text
ALLOW_CREATE_DRAFTS=true
ALLOW_MARK_AS_READ=true
ALLOW_EMAIL_SEND=false
ALLOW_CREATE_EVENTS=false
```

Recomendación durante la revisión local:

- mantener `ALLOW_EMAIL_SEND=false` hasta probar el flujo completo;
- mantener `ALLOW_CREATE_EVENTS=false` en instalaciones nuevas;
- habilitar cada acción únicamente de forma consciente y con una cuenta de prueba.

El archivo `.env.example` deja desactivados por defecto el envío de correos y la creación de eventos.

---

## 10. Datos privados y GitHub

No deben publicarse:

```text
.env
data/secretario_ampa.db
data/rag/correos_historicos.jsonl
```

`.gitignore` evita nuevas incorporaciones, pero si SQLite o el RAG ya estaban registrados en Git deben retirarse del seguimiento sin borrarlos del ordenador:

```bash
git rm --cached data/secretario_ampa.db
git rm --cached data/rag/correos_historicos.jsonl
```

Después:

```bash
git add .gitignore .env.example requirements.txt README.md
git commit -m "Prepara raiz del proyecto para V3.9"
```

---

## 11. Estado de la V3.9

La versión permanece en revisión local. Los siguientes bloques se revisarán paso a paso antes de crear la copia final y subirla a GitHub:

- scripts de entrada;
- módulos de `src/`;
- prompts;
- memoria y RAG;
- herramientas de prueba;
- documentación final;
- limpieza del proyecto.

La V4.0 incorporará el despliegue permanente en una máquina virtual y la ejecución mediante `systemd`.
