# Secretario AMPA

Versión simplificada para probar directamente el agente con una cuenta Gmail real de pruebas.

## Cuenta prevista

`agentesectretarioampa@gmail.com`

La aplicación no utiliza la contraseña. La autorización se realiza mediante OAuth desde el navegador.

## Estructura

```text
Secretario_AMPA/
├── notebooks/
│   ├── 01_configuracion_y_primera_llamada.ipynb
│   ├── 02_prompts_y_clasificacion.ipynb
│   └── 03_conexion_gmail_y_prueba_agente.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── google_oauth.py
│   ├── gmail_client.py
│   ├── agente.py
│   └── memoria.py
├── prompts/
│   └── system_prompt_secretario.md
├── main.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── Diseno_Tecnico_Agente_Secretario_AMPA.md
```

## Primera prueba

1. Completar `LLM_API_KEY` en `.env`.
2. Crear un proyecto en Google Cloud.
3. Activar Gmail API.
4. Crear credenciales OAuth para una aplicación de escritorio.
5. Descargar el archivo y guardarlo como `credentials.json`.
6. Ejecutar:

```bash
pip install -r requirements.txt
python main.py --probar-conexion
python main.py --revisar --limite 3
```

## Seguridad inicial

```env
GMAIL_ACCESS_MODE=lectura
ALLOW_EMAIL_SEND=false
ALLOW_CREATE_DRAFTS=false
ALLOW_MODIFY_LABELS=false
```

La primera prueba solo lee y analiza. No crea borradores, no cambia etiquetas y no envía correos.

## Cambio de modelo o de organización

El núcleo está separado del prompt y de la configuración. Para adaptarlo a otra organización se modifican principalmente:

- `prompts/system_prompt_secretario.md`
- `.env`
- reglas de clasificación y actuación
- modelo y proveedor LLM

El envío automático de correo permanece prohibido.
