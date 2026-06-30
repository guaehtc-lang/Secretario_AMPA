# Plan de pruebas V0.3

Se recomienda probar paso a paso y anotar todos los fallos.
Solo se generará V0.4 después de completar el bloque de pruebas, salvo que un error impida continuar.

## 0. Configuración

```bash
python -m compileall -q main.py src
python autorizar_google.py
python actualizar_rag.py
```

## 1. Buzón sin correos pendientes

```bash
python main.py
```

Esperado: `sin_correos_nuevos`.

## 2. Informativo

Esperado:
- clasificación `informativo`;
- sin borrador;
- permanece no leído;
- queda registrado en SQLite.

## 3. Necesita respuesta

Esperado:
- consulta RAG;
- crea borrador;
- marca leído;
- nunca envía el correo.

## 4. Reunión

Esperado:
- extrae fechas y horas;
- consulta Calendar;
- crea borrador con opciones;
- marca leído;
- no crea evento.

## 5. Urgencia de seguridad

Esperado:
- crea resumen de máximo cinco líneas;
- muestra WhatsApp simulado;
- registra la alerta;
- marca leído.

## 6. No clasificado

Esperado:
- no crea borrador;
- no ejecuta Calendar ni WhatsApp;
- permanece no leído;
- requiere revisión.

## Estrategia de versiones

- V0.3: ejecutar el bloque completo y anotar fallos.
- V0.4: corregir todos los fallos encontrados conjuntamente.
- Parche inmediato únicamente si una avería bloquea las pruebas restantes.
