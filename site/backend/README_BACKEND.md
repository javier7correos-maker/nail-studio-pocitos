# Backend generado por Vegeta

## Resumen

API minima para capturar reservas, validar disponibilidad basica y reenviar solicitudes.

## Recurso principal

- Servicio: `Forge Reservas`
- Slug: `nail-studio-pocitos-reservas`
- Modo backend: `booking_intake`
- Recurso principal: `reservas`

## Endpoints

- `GET /health`: Salud del servicio backend
- `GET /api/meta`: Resumen del contrato operativo y readiness de entorno
- `POST /api/reservas`: Valida y acepta el payload principal del MVP
- `GET /api/reservas/recent`: Ultimos envios aceptados para QA y trazabilidad
- `GET /api/reservas/schema`: Esquema esperado del payload principal

## Campos del payload principal

- `nombre` (`string`, requerido): Nombre del cliente
- `email` (`email`, requerido): Email del cliente
- `fecha` (`string`, requerido): Fecha solicitada
- `hora` (`string`, requerido): Hora solicitada
- `servicio` (`string`, requerido): Servicio o tipo de reserva
- `notas` (`string`, opcional): Notas opcionales

## Variables de entorno

- `PORT` (opcional): Puerto HTTP local o de Render
- `APP_ENV` (opcional): Entorno operativo
- `FORWARD_WEBHOOK_URL` (opcional): Webhook de integracion externa

## Ejecucion local

```powershell
cd C:\forge\projects\nail-studio-pocitos\src\backend
pip install -r requirements.txt
python app.py
```

## Notas

- Persistencia local para dev y QA; en Render no sustituye una base durable.
- Forward webhook opcional para n8n, Formspree o integracion propia.
- Piccolo debe validar el endpoint principal antes del deploy.
