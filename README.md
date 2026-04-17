# higgsfield-microservice

Microservicio en Python/FastAPI para integrar Higgsfield como proveedor de generación de video dentro del proyecto general **Edicion de Fotos y Video con IA**.

## Estado actual

El servicio ya incluye:

- `/health`
- `POST /video/generate-video`
- `GET /video/tasks/{id}`
- protección con `HIGGSFIELD_EXECUTION_ENABLED=false`
- upload real con `upload_file(...)`
- submit real con `submit(...)`
- polling con `status(request_id=...)`
- obtención de resultado con `result(request_id=...)`
- construcción de argumentos separada por perfil de modelo

## Modelos candidatos documentados

Higgsfield muestra públicamente en su plataforma varios modelos relevantes para video, incluyendo:

- Wan 2.5
- Wan 2.6
- Sora 2
- Kling 3.0

## Configuración de modelo

Ejemplo:

```env
HIGGSFIELD_MODEL_ID=wan-2.5
HIGGSFIELD_MODEL_LABEL=WAN 2.5
HIGGSFIELD_EXECUTION_ENABLED=false