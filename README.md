# higgsfield-microservice

Microservicio en Python/FastAPI para integrar **Higgsfield** como proveedor de generación de video dentro del proyecto general **Edicion de Fotos y Video con IA**.

## Objetivo

Mantener el mismo contrato consumido por n8n para:

- solicitar generación de video
- consultar el estado de tareas
- normalizar estados del proveedor

## Estado actual

El servicio ya incluye:

- bootstrap en FastAPI
- `/health`
- `POST /video/generate-video`
- `GET /video/tasks/{id}`
- `HIGGSFIELD_EXECUTION_ENABLED=false` como protección
- preparación para alternar modelos tentativos por configuración
- estructura lista para integrar ejecución real con el SDK

## Variables de entorno

Copiar `.env.example` a `.env` y completar:

- `PORT`
- `APP_ENV`
- `ACTIVE_VIDEO_PROVIDER`
- `HIGGSFIELD_API_KEY`
- `HIGGSFIELD_API_SECRET`
- `HIGGSFIELD_MODEL_ID`
- `HIGGSFIELD_MODEL_LABEL`
- `HIGGSFIELD_EXECUTION_ENABLED`
- `LOG_LEVEL`

## Ejemplo base

```env
PORT=3010
APP_ENV=development

ACTIVE_VIDEO_PROVIDER=higgsfield

HIGGSFIELD_API_KEY=TU_API_KEY
HIGGSFIELD_API_SECRET=TU_API_SECRET

HIGGSFIELD_MODEL_ID=wan-2.5
HIGGSFIELD_MODEL_LABEL=WAN 2.5

HIGGSFIELD_EXECUTION_ENABLED=false

LOG_LEVEL=INFO