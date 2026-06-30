# Estado y pendientes
## Secretario AMPA V3.5

## Revisado

### Configuración

- Compilación del proyecto.
- Conexión con Gmail.
- Conexión con Google Calendar.

### Gestión básica de correo

- Lectura de correos no leídos.
- Orden cronológico.
- Clasificación.
- Creación de borradores.
- Marcado como leído tras crear el borrador.
- Informativos y no clasificados permanecen no leídos.
- Registro en SQLite.
- Prevención de reprocesado.

### Clasificaciones comprobadas

- `informativo`
- `necesita_respuesta`
- `no_clasificado`

## Pendiente de revisar

### RAG

- Incorporar el archivo histórico definitivo.
- Validar búsquedas TF-IDF.
- Revisar los antecedentes recuperados.
- Comprobar la redacción con y sin contexto.

### Calendar

- Extraer fechas y horas.
- Consultar disponibilidad real.
- Detectar horarios ocupados.
- Crear el borrador de propuesta.
- Marcar el correo como leído.

### WhatsApp

- Clasificar urgencias reales.
- Generar el resumen.
- Comprobar el modo simulado.
- Evitar duplicados.
- Marcar el correo como leído.

### Memoria y errores

- Revisar persistencia.
- Probar reintentos.
- Probar errores de Gmail, Calendar y LLM.
- Revisar `servicio.py`.

## Archivos temporales

`reset_pruebas.py` debe eliminarse al finalizar las pruebas.
