# higgsfield-microservice

Microservicio en Python/FastAPI para integrar **Higgsfield** como proveedor de generación de video dentro del proyecto general **Edicion de Fotos y Video con IA**.

## Objetivo

Mantener el mismo contrato consumido por n8n para:

- solicitar generación de video
- consultar el estado de tareas
- normalizar estados del proveedor

## Estado actual

Este repositorio ya incluye:

- bootstrap del microservicio en FastAPI
- configuración por variables de entorno
- endpoint `/health`
- endpoint `POST /video/generate-video`
- endpoint `GET /video/tasks/{id}`
- bandera de seguridad `HIGGSFIELD_EXECUTION_ENABLED=false`
- estructura preparada para integrar el SDK oficial de Higgsfield sin activar ejecución real todavía

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