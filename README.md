# higgsfield-microservice

Microservicio en Python/FastAPI para integrar Higgsfield como proveedor de generación de video dentro del proyecto general **Edicion de Fotos y Video con IA**.

## Objetivo

Mantener el contrato actual usado por n8n para:
- solicitar generación de video
- consultar estado de tareas
- normalizar estados del proveedor

Actualmente el microservicio está preparado para:
- levantar localmente
- responder `/health`
- registrar tareas vía `POST /video/generate-video`
- fallar de forma controlada si falta `HIGGSFIELD_MODEL_ID`

## Stack

- Python 3.13
- FastAPI
- Uvicorn
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