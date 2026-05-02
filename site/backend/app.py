from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pydantic import BaseModel, ConfigDict, ValidationError, create_model


BASE_DIR = Path(__file__).resolve().parent
CONTRACT = {'service_name': 'Forge Reservas', 'service_slug': 'nail-studio-pocitos-reservas', 'service_summary': 'API minima para capturar reservas, validar disponibilidad basica y reenviar solicitudes.', 'backend_mode': 'booking_intake', 'project_type': 'portfolio', 'project_slug': 'nail-studio-pocitos', 'project_id': '4ad64788-53b9-4711-9e85-2ee52fd562bd', 'task_id': 'eb5de6d6-6389-4c4e-815d-69705b2b6a8a', 'primary_resource': 'reservas', 'entity': {'name': 'reserva', 'label': 'Reservas', 'fields': [{'name': 'nombre', 'type': 'string', 'required': True, 'description': 'Nombre del cliente'}, {'name': 'email', 'type': 'email', 'required': True, 'description': 'Email del cliente'}, {'name': 'fecha', 'type': 'string', 'required': True, 'description': 'Fecha solicitada'}, {'name': 'hora', 'type': 'string', 'required': True, 'description': 'Hora solicitada'}, {'name': 'servicio', 'type': 'string', 'required': True, 'description': 'Servicio o tipo de reserva'}, {'name': 'notas', 'type': 'string', 'required': False, 'description': 'Notas opcionales'}]}, 'routes': [{'name': 'health', 'method': 'GET', 'path': '/health', 'kind': 'health', 'resource': 'reservas', 'description': 'Salud del servicio backend', 'required_fields': [], 'optional_fields': [], 'forward_env': ''}, {'name': 'meta', 'method': 'GET', 'path': '/api/meta', 'kind': 'meta', 'resource': 'reservas', 'description': 'Resumen del contrato operativo y readiness de entorno', 'required_fields': [], 'optional_fields': [], 'forward_env': ''}, {'name': 'submit', 'method': 'POST', 'path': '/api/reservas', 'kind': 'submit', 'resource': 'reservas', 'description': 'Valida y acepta el payload principal del MVP', 'required_fields': ['nombre', 'email', 'fecha', 'hora', 'servicio'], 'optional_fields': ['notas'], 'forward_env': 'FORWARD_WEBHOOK_URL'}, {'name': 'recent', 'method': 'GET', 'path': '/api/reservas/recent', 'kind': 'recent', 'resource': 'reservas', 'description': 'Ultimos envios aceptados para QA y trazabilidad', 'required_fields': [], 'optional_fields': [], 'forward_env': ''}, {'name': 'schema', 'method': 'GET', 'path': '/api/reservas/schema', 'kind': 'schema', 'resource': 'reservas', 'description': 'Esquema esperado del payload principal', 'required_fields': [], 'optional_fields': [], 'forward_env': ''}], 'integrations': ['whatsapp', 'render'], 'env_vars': [{'name': 'PORT', 'required': False, 'purpose': 'Puerto HTTP local o de Render', 'example': '10000'}, {'name': 'APP_ENV', 'required': False, 'purpose': 'Entorno operativo', 'example': 'production'}, {'name': 'FORWARD_WEBHOOK_URL', 'required': False, 'purpose': 'Webhook de integracion externa', 'example': 'https://n8n.example/webhook/forge'}], 'storage': {'enabled': True, 'mode': 'jsonl', 'path': 'storage/reservas.jsonl'}, 'notes': ['Persistencia local para dev y QA; en Render no sustituye una base durable.', 'Forward webhook opcional para n8n, Formspree o integracion propia.', 'Piccolo debe validar el endpoint principal antes del deploy.'], 'sample_payload': {'nombre': 'Cliente Demo', 'email': 'demo@example.com', 'fecha': '2026-05-01', 'hora': '10:00', 'servicio': 'valor-demo', 'notas': 'valor-demo'}}

load_dotenv(BASE_DIR / ".env", override=False)
APP = Flask(__name__)
CORS(APP)
APP.config["JSON_SORT_KEYS"] = False

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PayloadBase(BaseModel):
    model_config = ConfigDict(extra="allow")


def get_storage_path() -> Path:
    relative_path = str(CONTRACT.get("storage", {}).get("path") or "storage/submissions.jsonl")
    target = (BASE_DIR / relative_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def get_entity_fields() -> list[dict[str, Any]]:
    return list(CONTRACT.get("entity", {}).get("fields", []))


def get_env_readiness() -> list[dict[str, Any]]:
    readiness = []
    for item in CONTRACT.get("env_vars", []):
        name = str(item.get("name") or "").strip()
        readiness.append(
            {
                "name": name,
                "required": bool(item.get("required", False)),
                "configured": bool(os.getenv(name)),
            }
        )
    return readiness


def build_dynamic_model() -> type[BaseModel]:
    type_map = {
        "string": str,
        "email": str,
        "boolean": bool,
        "integer": int,
        "number": float,
        "object": dict,
        "list": list,
    }
    definitions: dict[str, tuple[Any, Any]] = {}
    for field in get_entity_fields():
        python_type = type_map.get(str(field.get("type") or "string").strip().lower(), str)
        if field.get("required"):
            definitions[field["name"]] = (python_type, ...)
        else:
            definitions[field["name"]] = (python_type | None, None)
    return create_model("DynamicPayload", __base__=PayloadBase, **definitions)


def validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    model = build_dynamic_model()
    validated = model.model_validate(payload).model_dump()
    for field in get_entity_fields():
        if str(field.get("type") or "").lower() != "email":
            continue
        value = validated.get(field["name"])
        if value and not EMAIL_PATTERN.match(str(value).strip()):
            raise ValidationError.from_exception_data(
                title="DynamicPayload",
                line_errors=[
                    {
                        "type": "value_error",
                        "loc": (field["name"],),
                        "msg": "Formato de email invalido.",
                        "input": value,
                        "ctx": {"error": "Formato de email invalido."},
                    }
                ],
            )
    return validated


def append_record(record: dict[str, Any]) -> None:
    storage_path = get_storage_path()
    with storage_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_recent(limit: int = 10) -> list[dict[str, Any]]:
    storage_path = get_storage_path()
    if not storage_path.exists():
        return []
    with storage_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    recent = []
    for raw_line in lines[-limit:]:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            recent.append(json.loads(raw_line))
        except json.JSONDecodeError:
            continue
    return recent


def route_forward_target() -> str:
    for route in CONTRACT.get("routes", []):
        if route.get("kind") == "submit" and route.get("forward_env"):
            return str(route["forward_env"]).strip()
    return "FORWARD_WEBHOOK_URL"


def forward_payload_if_configured(record: dict[str, Any]) -> dict[str, Any]:
    env_name = route_forward_target()
    target_url = os.getenv(env_name, "").strip()
    if not target_url:
        return {"configured": False, "ok": False, "target_env": env_name, "target_url": None, "error": None}

    try:
        response = requests.post(target_url, json=record, timeout=12)
        return {
            "configured": True,
            "ok": response.status_code < 400,
            "target_env": env_name,
            "target_url": target_url,
            "status_code": response.status_code,
            "error": None if response.status_code < 400 else response.text[:300],
        }
    except requests.RequestException as exc:
        return {
            "configured": True,
            "ok": False,
            "target_env": env_name,
            "target_url": target_url,
            "error": str(exc),
        }


@APP.get("/health")
def health() -> Any:
    return jsonify(
        {
            "status": "ok",
            "service": CONTRACT.get("service_slug"),
            "resource": CONTRACT.get("primary_resource"),
            "storage_ready": get_storage_path().parent.exists(),
            "timestamp": int(time.time()),
        }
    )


@APP.get("/api/meta")
def meta() -> Any:
    return jsonify(
        {
            "service_name": CONTRACT.get("service_name"),
            "service_slug": CONTRACT.get("service_slug"),
            "summary": CONTRACT.get("service_summary"),
            "backend_mode": CONTRACT.get("backend_mode"),
            "primary_resource": CONTRACT.get("primary_resource"),
            "routes": CONTRACT.get("routes", []),
            "fields": get_entity_fields(),
            "env_readiness": get_env_readiness(),
            "storage_path": str(get_storage_path()),
        }
    )


@APP.get("/api/<resource>/schema")
def schema(resource: str) -> Any:
    if resource != CONTRACT.get("primary_resource"):
        return jsonify({"ok": False, "error": "Recurso no soportado."}), 404
    return jsonify(
        {
            "resource": resource,
            "fields": get_entity_fields(),
            "sample_payload": CONTRACT.get("sample_payload", {}),
        }
    )


@APP.get("/api/<resource>/recent")
def recent(resource: str) -> Any:
    if resource != CONTRACT.get("primary_resource"):
        return jsonify({"ok": False, "error": "Recurso no soportado."}), 404
    return jsonify(
        {
            "resource": resource,
            "count": len(read_recent()),
            "items": read_recent(),
        }
    )


@APP.post("/api/<resource>")
def submit(resource: str) -> Any:
    if resource != CONTRACT.get("primary_resource"):
        return jsonify({"ok": False, "error": "Recurso no soportado."}), 404

    incoming = request.get_json(silent=True)
    if not isinstance(incoming, dict):
        return jsonify({"ok": False, "error": "Payload JSON invalido."}), 400

    try:
        validated = validate_payload(incoming)
    except ValidationError as exc:
        return jsonify({"ok": False, "error": "Payload invalido.", "details": exc.errors()}), 422

    record = {
        "id": str(uuid.uuid4()),
        "resource": resource,
        "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "payload": validated,
        "headers": {
            "user_agent": request.headers.get("User-Agent"),
            "origin": request.headers.get("Origin"),
        },
    }
    append_record(record)
    forward_result = forward_payload_if_configured(record)

    return jsonify(
        {
            "ok": True,
            "message": "Payload aceptado.",
            "record_id": record["id"],
            "resource": resource,
            "forward": forward_result,
        }
    ), 201


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    APP.run(host="0.0.0.0", port=port, debug=False)
