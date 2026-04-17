# higgsfield-microservice

Microservicio en Python/FastAPI para integrar **Higgsfield** como proveedor de generación de video dentro del proyecto general **Edicion de Fotos y Video con IA**.

## Objetivo

Mantener el mismo contrato consumido por n8n para:

- solicitar generación de video
- consultar el estado de tareas
- normalizar estados del proveedor

## Estado actual

El servicio ya soporta:

- `/health`
- `POST /video/generate-video`
- `GET /video/tasks/{id}`
- validación segura con `HIGGSFIELD_EXECUTION_ENABLED=false`
- flujo real preparado con:
  - `upload_file(...)`
  - `submit(...)`
  - `status(request_id=...)`
  - `result(request_id=...)`

## Importante

La documentación oficial del SDK Python de Higgsfield indica que:
- `upload_file(...)` sube un archivo y devuelve una URL,
- `submit(...)` crea una solicitud asíncrona,
- `status(request_id=...)` permite consultar el estado,
- `result(request_id=...)` obtiene el resultado final. :contentReference[oaicite:1]{index=1}

Aun así, el schema exacto de `arguments` depende del `model_id` concreto que se vaya a usar. Por eso, el código actual deja este bloque preparado pero puede requerir ajuste fino cuando el cliente confirme el modelo exacto. :contentReference[oaicite:2]{index=2}

## Variables de entorno

```env
PORT=3010
APP_ENV=development

ACTIVE_VIDEO_PROVIDER=higgsfield

HIGGSFIELD_API_KEY=TU_API_KEY
HIGGSFIELD_API_SECRET=TU_API_SECRET
HIGGSFIELD_MODEL_ID=
HIGGSFIELD_EXECUTION_ENABLED=false

LOG_LEVEL=INFO

## Stack

- Python 3.13
- FastAPI
- Uvicorn
- python-dotenv
- pydantic
- higgsfield-client

## Estructura

```text
app/
  main.py
  config.py
  models.py
  routes/
    video.py
  services/
    task_store.py
    higgsfield_service.py
.env.example
requirements.txt
Dockerfile
README.md