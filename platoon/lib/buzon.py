#!/usr/bin/env python3
"""Canal de comunicación y sincronización del pelotón.

Los cuerpos de handoff y de asignación conservan los campos de la
especificación (§40 y §41). El sobre (type, to, task_id) es el transporte
necesario para enrutar sin abrir las carpetas de otro agente.

El tablero público solo expone estado y una línea de actividad. El cuerpo
de un entregable vive en la bandeja del destinatario autorizado.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from politica import (
    ProtocolError,
    authenticate,
    load_json,
    reject_if_contains_secret,
)


TASK_ID_RE = re.compile(r"^NXP-[0-9]{4,}$")
STATUSES = {
    "inactivo",
    "listo",
    "asignado",
    "en_progreso",
    "bloqueado",
    "en_revision",
    "entregado",
    "retrabajo",
}
MESSAGE_TYPES = {"asignacion", "handoff", "revision", "conflicto", "coordinacion", "decision"}
QA_GATES = (
    "FUNCTIONAL_QA",
    "VISUAL_QA",
    "ACCESSIBILITY_QA",
    "PERFORMANCE_QA",
    "REGRESSION_QA",
)
GATE_OWNER = {
    "FUNCTIONAL_QA": "FUNCTIONAL_QA_MZ",
    "VISUAL_QA": "VISUAL_QA_MZ",
    "ACCESSIBILITY_QA": "ACCESSIBILITY_QA_MZ",
    "PERFORMANCE_QA": "PERFORMANCE_QA_MZ",
    "REGRESSION_QA": "REGRESSION_QA_MZ",
    "DESIGN_APPROVED": "MANAGER_MZ2_DESIGN",
}
RUBBER_STAMPS = {
    "looks good",
    "looks good.",
    "lgtm",
    "ok",
    "okay",
    "se ve bien",
    "se ve bien.",
    "esta bien",
    "está bien",
    "aprobado",
    "todo bien",
    "sin problemas",
    "pass",
    "passed",
    "fail",
    "failed",
}
DESIGN_EXCEPTIONS = {
    "correccion de emergencia",
    "ajuste visual minimo",
    "correccion de accesibilidad",
    "regresion evidente",
    "autorizado explicitamente por SUPER_MANAGER",
}
HANDOFF_FIELDS = (
    "TASK",
    "STATUS",
    "WHAT WAS INVESTIGATED",
    "WHAT WAS CHANGED",
    "DECISIONS",
    "EVIDENCE",
    "FILES AFFECTED",
    "DEPENDENCIES",
    "RISKS",
    "OPEN QUESTIONS",
    "NEXT AGENT",
)
ASSIGNMENT_FIELDS = (
    "task_id",
    "objective",
    "manager",
    "priority",
    "dependencies",
    "constraints",
    "deliverables",
    "review_required",
)
LIST_FIELDS = {
    "dependencies",
    "constraints",
    "deliverables",
    "EVIDENCE",
    "FILES AFFECTED",
    "DEPENDENCIES",
    "OPEN QUESTIONS",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_log(root: Path, entry: dict) -> None:
    path = root / "canal" / "registro" / "actividad.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _task_path(root: Path, task_id: str) -> Path:
    if not TASK_ID_RE.match(task_id):
        raise ProtocolError("task_id inválido. El formato de la especificación es NXP-0001.", "uso")
    return root / "canal" / "tareas" / f"{task_id}.json"


def _gate_path(root: Path, task_id: str) -> Path:
    if not TASK_ID_RE.match(task_id):
        raise ProtocolError("task_id inválido. El formato de la especificación es NXP-0001.", "uso")
    return root / "canal" / "compuertas" / f"{task_id}.json"


def load_task(root: Path, task_id: str) -> dict:
    path = _task_path(root, task_id)
    if not path.is_file():
        raise ProtocolError(f"La tarea {task_id} no existe. Solo SUPER_MANAGER_MZ0 puede crearla.", "denegado")
    return load_json(path)


def load_gates(root: Path, task_id: str) -> dict:
    path = _gate_path(root, task_id)
    if not path.is_file():
        return {"task_id": task_id, "gates": {}}
    return load_json(path)


def _known_agents(root: Path) -> set[str]:
    return set(load_json(root / "permisos" / "matriz.json")["agentes"])


def _nonempty_text(value, field: str) -> str:
    if not isinstance(value, str) or len(value.strip()) < 12:
        raise ProtocolError(
            f"«{field}» debe ser texto explícito de al menos 12 caracteres. No se aceptan campos vacíos.",
            "esquema",
        )
    return value.strip()


def _evidence_list(value, *, minimum: int, field: str = "EVIDENCE") -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise ProtocolError(
            f"«{field}» debe ser una lista con al menos {minimum} elemento(s) concreto(s). "
            "Un sello vacío del tipo «Looks good.» no es una revisión (§44).",
            "esquema",
        )
    cleaned = []
    for item in value:
        if not isinstance(item, str):
            raise ProtocolError(f"Cada elemento de «{field}» debe ser texto.", "esquema")
        text = item.strip()
        if len(text) < 12:
            raise ProtocolError(
                f"Un elemento de «{field}» es demasiado vago. Describe la comprobación realizada.",
                "esquema",
            )
        if text.lower().rstrip(".") in {stamp.rstrip(".") for stamp in RUBBER_STAMPS} or text.lower() in RUBBER_STAMPS:
            raise ProtocolError(
                f"«{text}» no es evidencia. §44 prohíbe aprobar con un sello vacío.",
                "denegado",
            )
        cleaned.append(text)
    return cleaned


def _scan(root: Path, payload) -> None:
    reject_if_contains_secret(root, json.dumps(payload, ensure_ascii=False))


def _deliver(root: Path, message: dict) -> None:
    inbox = root / "canal" / "bandeja" / message["to"]
    inbox.mkdir(parents=True, exist_ok=True)
    _write_json(inbox / f"{message['message_id']}.json", message)


def _active_assignees(task: dict) -> set[str]:
    return {
        item["assignee"]
        for item in task.get("delegaciones", [])
        if item.get("active") and item.get("assignee")
    }


def _sender_on_task(agent_id: str, task: dict) -> bool:
    return agent_id == task.get("manager") or agent_id in _active_assignees(task)


def update_state(root: Path, agent_id: str, token: str, status: str, activity: str, task_id: str | None) -> dict:
    authenticate(root, agent_id, token)
    if status not in STATUSES:
        raise ProtocolError(
            "Estado no reconocido. Usa: " + ", ".join(sorted(STATUSES)) + ".",
            "uso",
        )
    activity = _nonempty_text(activity, "actividad")
    if len(activity) > 240:
        raise ProtocolError(
            "La línea de actividad admite como máximo 240 caracteres. El entregable va en el handoff, no en el tablero.",
            "uso",
        )
    if task_id:
        load_task(root, task_id)
        if not _sender_on_task(agent_id, load_task(root, task_id)) and agent_id != "SUPER_MANAGER_MZ0":
            raise ProtocolError(
                "No puedes asociar tu estado a una tarea que no te fue asignada.",
                "denegado",
            )
    reject_if_contains_secret(root, activity)
    payload = {
        "agent_id": agent_id,
        "status": status,
        "activity": activity,
        "task_id": task_id,
        "updated_at": now(),
        "updated_by": agent_id,
    }
    path = root / "canal" / "estados" / f"{agent_id}.json"
    if not path.is_file():
        raise ProtocolError("No hay estado inicial para este agente.", "configuracion")
    _write_json(path, payload)
    _append_log(
        root,
        {
            "ts": payload["updated_at"],
            "agente": agent_id,
            "accion": "estado",
            "tarea": task_id,
            "destino": None,
            "resumen": status,
        },
    )
    return {"mensaje": f"Estado de {agent_id} actualizado a «{status}».", "estado": payload}


def board(root: Path, agent_id: str, token: str) -> dict:
    authenticate(root, agent_id, token)
    states = []
    state_dir = root / "canal" / "estados"
    for path in sorted(state_dir.glob("*.json")):
        item = load_json(path)
        states.append(
            {
                "agent_id": item.get("agent_id"),
                "status": item.get("status"),
                "activity": item.get("activity"),
                "task_id": item.get("task_id"),
                "updated_at": item.get("updated_at"),
            }
        )
    return {
        "mensaje": "Tablero de estados. No incluye cuerpos de entregables ni credenciales.",
        "consultado_por": agent_id,
        "estados": states,
    }


def inbox(root: Path, agent_id: str, token: str, message_id: str | None = None) -> dict:
    authenticate(root, agent_id, token)
    folder = root / "canal" / "bandeja" / agent_id
    if message_id:
        if not re.match(r"^msg_[a-f0-9]{16}$", message_id):
            raise ProtocolError("Identificador de mensaje inválido.", "uso")
        path = folder / f"{message_id}.json"
        if not path.is_file():
            raise ProtocolError("Ese mensaje no está en tu bandeja.", "denegado")
        return {"mensaje": "Mensaje de tu bandeja.", "mensaje_completo": load_json(path)}
    items = []
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            item = load_json(path)
            items.append(
                {
                    "message_id": item.get("message_id"),
                    "type": item.get("type"),
                    "from": item.get("from"),
                    "task_id": item.get("task_id"),
                    "timestamp": item.get("timestamp"),
                    "copia_comando": bool(item.get("copia_comando")),
                }
            )
    return {
        "mensaje": f"Bandeja de {agent_id}. Solo sus mensajes.",
        "total": len(items),
        "mensajes": items,
    }


def _validate_assignment(root: Path, sender: str, recipient: str, body: dict, record: dict) -> dict:
    missing = [field for field in ASSIGNMENT_FIELDS if field not in body]
    if missing:
        raise ProtocolError(
            "La asignación no cumple §40. Faltan: " + ", ".join(missing) + ".",
            "esquema",
        )
    task_id = body["task_id"]
    if not isinstance(task_id, str) or not TASK_ID_RE.match(task_id):
        raise ProtocolError("task_id inválido. Usa el formato NXP-0001.", "esquema")
    _nonempty_text(body["objective"], "objective")
    if not isinstance(body["priority"], str) or len(body["priority"].strip()) < 3:
        raise ProtocolError(
            "priority debe ser texto. El ejemplo de §40 usa valores como high; no se exige una frase.",
            "esquema",
        )
    if not isinstance(body["review_required"], bool):
        raise ProtocolError("review_required debe ser booleano, como en §40.", "esquema")
    for field in ("dependencies", "constraints", "deliverables"):
        if not isinstance(body[field], list) or any(not isinstance(item, str) for item in body[field]):
            raise ProtocolError(f"«{field}» debe ser una lista de textos.", "esquema")
    if recipient not in record.get("puede_asignar_a", []):
        raise ProtocolError(
            f"{sender} no puede asignar trabajo a {recipient}. La asignación sigue la cadena de mando.",
            "denegado",
        )
    if sender == "SUPER_MANAGER_MZ0":
        if body["manager"] != recipient:
            raise ProtocolError(
                "En una asignación de SUPER_MANAGER el campo manager debe ser el gerente destinatario.",
                "esquema",
            )
        if body.get("assignee") not in (None, recipient):
            raise ProtocolError(
                "SUPER_MANAGER asigna a gerentes, no directamente a especialistas (§3).",
                "denegado",
            )
    else:
        if body["manager"] != sender:
            raise ProtocolError("Un gerente solo asigna trabajo dentro de su propio equipo.", "denegado")
        if body.get("assignee") != recipient:
            raise ProtocolError("La delegación debe nombrar en assignee al especialista destinatario.", "esquema")
    ui_change = body.get("ui_change", "none")
    if ui_change not in ("none", "tiny", "major"):
        raise ProtocolError("ui_change solo puede ser none, tiny o major.", "esquema")
    return body


def _assignment_preview(root: Path, sender: str, recipient: str, body: dict) -> dict:
    """Vista previa para aplicar §42 también en --simular, sin escribir."""
    path = _task_path(root, body["task_id"])
    if sender != "SUPER_MANAGER_MZ0":
        task = load_task(root, body["task_id"])
        return task
    if path.is_file():
        task = dict(load_json(path))
    else:
        task = {"task_id": body["task_id"], "ui_change": "none", "excepcion_diseno": None}
    task["manager"] = recipient
    task["ui_change"] = body.get("ui_change", task.get("ui_change", "none"))
    if body.get("design_task_id"):
        task["design_task_id"] = body["design_task_id"]
    if body.get("excepcion_diseno"):
        task["excepcion_diseno"] = _validate_exception(body["excepcion_diseno"])
    return task


def _apply_assignment(root: Path, sender: str, recipient: str, body: dict) -> dict:
    task_id = body["task_id"]
    path = _task_path(root, task_id)
    timestamp = now()
    if sender == "SUPER_MANAGER_MZ0":
        if path.is_file():
            task = load_json(path)
            if task.get("closed"):
                raise ProtocolError("La tarea ya está cerrada.", "denegado")
            previous = task.get("manager")
            task.setdefault("historial", []).append(
                {"manager": previous, "until": timestamp, "event": "reasignacion"}
            )
            task["manager"] = recipient
            task["objective"] = body["objective"]
            task["priority"] = body["priority"]
            task["dependencies"] = body["dependencies"]
            task["constraints"] = body["constraints"]
            task["deliverables"] = body["deliverables"]
            task["review_required"] = body["review_required"]
            task["ui_change"] = body.get("ui_change", task.get("ui_change", "none"))
            if body.get("design_task_id"):
                task["design_task_id"] = body["design_task_id"]
            for item in task.get("delegaciones", []):
                item["active"] = False
            task["updated_at"] = timestamp
            action = "reasignacion"
        else:
            task = {
                "task_id": task_id,
                "objective": body["objective"],
                "manager": recipient,
                "priority": body["priority"],
                "dependencies": body["dependencies"],
                "constraints": body["constraints"],
                "deliverables": body["deliverables"],
                "review_required": body["review_required"],
                "ui_change": body.get("ui_change", "none"),
                "design_task_id": body.get("design_task_id"),
                "excepcion_diseno": None,
                "delegaciones": [],
                "historial": [{"manager": recipient, "from": timestamp, "event": "creacion"}],
                "created_at": timestamp,
                "created_by": sender,
                "updated_at": timestamp,
                "closed": False,
            }
            action = "creacion"
        if body.get("excepcion_diseno"):
            task["excepcion_diseno"] = _validate_exception(body["excepcion_diseno"])
            task["excepcion_diseno"]["by"] = sender
            task["excepcion_diseno"]["at"] = timestamp
        _enforce_design_gate_for_frontend(root, recipient, task)
        if _leaving_qa(task, action, recipient):
            _invalidate_qa(root, task_id, "Reasignación fuera de QA. §43 exige volver a probar después del retrabajo.")
        _write_json(path, task)
        return task
    task = load_task(root, task_id)
    if task.get("closed"):
        raise ProtocolError("La tarea ya está cerrada.", "denegado")
    if task.get("manager") != sender:
        raise ProtocolError("Solo el gerente actual de la tarea puede delegarla en su equipo.", "denegado")
    _enforce_design_gate_for_frontend(root, recipient, task, inherited=True)
    task.setdefault("delegaciones", []).append(
        {
            "assignee": recipient,
            "objective": body["objective"],
            "at": timestamp,
            "by": sender,
            "active": True,
        }
    )
    task["updated_at"] = timestamp
    _write_json(path, task)
    return task


def _leaving_qa(task: dict, action: str, recipient: str) -> bool:
    if action != "reasignacion":
        return False
    history = task.get("historial") or []
    if len(history) < 1:
        return False
    previous = history[-1].get("manager")
    return previous == "MANAGER_MZ5_QA" and recipient != "MANAGER_MZ5_QA"


def _invalidate_qa(root: Path, task_id: str, reason: str) -> None:
    gates = load_gates(root, task_id)
    current = gates.get("gates") or {}
    if not current:
        return
    timestamp = now()
    for name in QA_GATES:
        prior = current.get(name)
        if not prior:
            continue
        current[name] = {
            "value": None,
            "invalidated_at": timestamp,
            "invalidated_reason": reason,
            "previous": prior,
        }
    gates["gates"] = current
    gates["task_id"] = task_id
    _write_json(_gate_path(root, task_id), gates)


def _validate_exception(raw) -> dict:
    if not isinstance(raw, dict):
        raise ProtocolError("excepcion_diseno debe ser un objeto con motivo y evidence.", "esquema")
    motivo = raw.get("motivo")
    if motivo not in DESIGN_EXCEPTIONS:
        raise ProtocolError(
            "Motivo de excepción no reconocido. §42 solo admite corrección de emergencia, "
            "ajuste visual mínimo, corrección de accesibilidad, regresión evidente "
            "o autorización explícita del SUPER_MANAGER con evidencia.",
            "denegado",
        )
    evidence = _evidence_list(raw.get("evidence"), minimum=1, field="evidence")
    return {"motivo": motivo, "evidence": evidence}


def _design_task_id(task: dict) -> str | None:
    return task.get("design_task_id") or task.get("task_id")


def _design_approved(root: Path, design_task_id: str | None) -> bool:
    if not design_task_id:
        return False
    gates = load_gates(root, design_task_id).get("gates", {})
    entry = gates.get("DESIGN_APPROVED") or {}
    return entry.get("value") is True


def _enforce_design_gate_for_frontend(root: Path, recipient: str, task: dict, inherited: bool = False) -> None:
    del inherited
    frontend_agents = set(
        load_json(root / "permisos" / "matriz.json")["agentes"]["MANAGER_MZ3_FRONTEND"].get("puede_asignar_a", [])
    )
    frontend_agents.add("MANAGER_MZ3_FRONTEND")
    if recipient not in frontend_agents:
        return
    if task.get("ui_change", "none") != "major":
        return
    if task.get("excepcion_diseno"):
        return
    if not _design_approved(root, _design_task_id(task)):
        raise ProtocolError(
            "Implementación de UI mayor bloqueada: DESIGN_APPROVED no es TRUE (§42). "
            "Hace falta la compuerta del gerente de diseño o una excepción explícita de §42 con evidencia.",
            "denegado",
        )


def _validate_handoff(root: Path, body: dict, task_id: str) -> None:
    missing = [field for field in HANDOFF_FIELDS if field not in body]
    if missing:
        raise ProtocolError(
            "El handoff no cumple §41. Faltan: " + ", ".join(missing) + ".",
            "esquema",
        )
    task_text = body.get("TASK")
    if not isinstance(task_text, str) or task_id not in task_text.strip():
        raise ProtocolError("TASK debe contener el task_id del sobre. El identificador NXP-0001 basta.", "esquema")
    status = body.get("STATUS")
    if not isinstance(status, str) or len(status.strip()) < 4:
        raise ProtocolError("STATUS no puede ir vacío.", "esquema")
    next_agent = body.get("NEXT AGENT")
    if not isinstance(next_agent, str):
        raise ProtocolError("NEXT AGENT es obligatorio.", "esquema")
    if next_agent != "NINGUNO" and next_agent not in _known_agents(root):
        raise ProtocolError("NEXT AGENT no es un agente del pelotón ni NINGUNO.", "esquema")
    for field in ("WHAT WAS INVESTIGATED", "WHAT WAS CHANGED", "RISKS"):
        _nonempty_text(body.get(field, ""), field)
    if not isinstance(body["DECISIONS"], (str, list)):
        raise ProtocolError("DECISIONS debe ser texto o lista.", "esquema")
    if isinstance(body["DECISIONS"], str):
        _nonempty_text(body["DECISIONS"], "DECISIONS")
    elif not body["DECISIONS"]:
        raise ProtocolError("DECISIONS no puede ir vacío.", "esquema")
    _evidence_list(body["EVIDENCE"], minimum=1)
    for field in ("FILES AFFECTED", "DEPENDENCIES", "OPEN QUESTIONS"):
        if not isinstance(body[field], list):
            raise ProtocolError(f"«{field}» debe ser una lista.", "esquema")
    for path in body["FILES AFFECTED"]:
        if not isinstance(path, str) or "secretos/" in path.replace("\\", "/") or path.endswith(".token"):
            raise ProtocolError("FILES AFFECTED no puede incluir secretos.", "denegado")


def _validate_revision(body: dict, sender: str) -> None:
    summary = body.get("summary")
    findings = body.get("findings")
    has_summary = isinstance(summary, str) and len(summary.strip()) >= 12
    has_findings = isinstance(findings, list) and any(isinstance(item, str) and len(item.strip()) >= 12 for item in findings)
    if not has_summary and not has_findings:
        raise ProtocolError(
            "Una revisión debe incluir summary o findings concretos. No se acepta un informe vacío (§44).",
            "esquema",
        )
    if "evidence" not in body and "EVIDENCE" not in body:
        raise ProtocolError("Una revisión sin evidencia queda rechazada (§44).", "esquema")
    evidence = body.get("evidence", body.get("EVIDENCE"))
    _evidence_list(evidence, minimum=1, field="evidence")
    if "verdict" in body and body["verdict"] not in ("observaciones", "rechazo", "sin_objecion"):
        raise ProtocolError(
            "verdict de diseño solo puede ser observaciones, rechazo o sin_objecion. No es un voto.",
            "esquema",
        )
    if body.get("copied_interface") is True:
        raise ProtocolError(
            "La revisión declara copia de una interfaz propietaria. §51 lo prohíbe.",
            "denegado",
        )
    del sender


def _validate_decision(body: dict) -> None:
    _nonempty_text(body.get("decision", ""), "decision")
    _nonempty_text(body.get("reason", ""), "reason")
    if not isinstance(body.get("alternatives"), list):
        raise ProtocolError("Una decisión debe listar alternatives consideradas (§57).", "esquema")


def _validate_conflict(body: dict) -> None:
    _nonempty_text(body.get("issue", ""), "issue")
    _nonempty_text(body.get("position", ""), "position")


def _validate_coordination(body: dict) -> None:
    _nonempty_text(body.get("change", ""), "change")
    _nonempty_text(body.get("frontend_impact", ""), "frontend_impact")


def publish(root: Path, agent_id: str, token: str, envelope: dict, simulate: bool = False) -> dict:
    record = authenticate(root, agent_id, token)
    if not isinstance(envelope, dict):
        raise ProtocolError("El mensaje debe ser un objeto JSON.", "esquema")
    if envelope.get("_ejemplo") is True and not simulate:
        raise ProtocolError(
            "Este archivo es un ejemplo. No se publica como trabajo real. Usa --simular para validarlo.",
            "denegado",
        )
    message_type = envelope.get("type")
    recipient = envelope.get("to")
    task_id = envelope.get("task_id")
    body = envelope.get("body")
    if message_type not in MESSAGE_TYPES:
        raise ProtocolError("Tipo de mensaje no reconocido.", "esquema")
    if message_type not in record.get("tipos_mensaje", []):
        raise ProtocolError(
            f"{agent_id} no puede emitir mensajes de tipo «{message_type}».",
            "denegado",
        )
    if not isinstance(recipient, str) or recipient not in _known_agents(root):
        raise ProtocolError("Destinatario desconocido.", "esquema")
    if recipient == agent_id:
        raise ProtocolError("Un agente no se envía trabajo a sí mismo por el canal.", "denegado")
    if not isinstance(body, dict):
        raise ProtocolError("El cuerpo del mensaje es obligatorio.", "esquema")
    if not isinstance(task_id, str) or not TASK_ID_RE.match(task_id):
        raise ProtocolError("El sobre debe incluir task_id con formato NXP-0001.", "esquema")
    _scan(root, envelope)

    if message_type == "asignacion":
        _validate_assignment(root, agent_id, recipient, body, record)
        if body["task_id"] != task_id:
            raise ProtocolError("El task_id del sobre y el del cuerpo no coinciden.", "esquema")
        _enforce_design_gate_for_frontend(root, recipient, _assignment_preview(root, sender=agent_id, recipient=recipient, body=body))
    elif message_type == "handoff":
        _validate_handoff(root, body, task_id)
        task = load_task(root, task_id)
        if task.get("closed"):
            raise ProtocolError("La tarea ya está cerrada.", "denegado")
        if not _sender_on_task(agent_id, task):
            raise ProtocolError("No puedes entregar una tarea que no está asignada a tu sección.", "denegado")
        if recipient not in record.get("puede_entregar_a", []):
            raise ProtocolError(
                f"{agent_id} no puede entregar a {recipient}. El cruce de módulos pasa por SUPER_MANAGER_MZ0.",
                "denegado",
            )
    elif message_type == "revision":
        _validate_revision(body, agent_id)
        task = load_task(root, task_id)
        if not _sender_on_task(agent_id, task):
            raise ProtocolError("No puedes revisar una tarea que no está en tu sección.", "denegado")
        if recipient not in record.get("puede_revisar_a", []):
            raise ProtocolError(
                f"{agent_id} solo remite revisiones a su cadena de mando, no a otro especialista.",
                "denegado",
            )
    elif message_type == "conflicto":
        _validate_conflict(body)
        load_task(root, task_id)
        if recipient not in record.get("puede_escalar_a", []):
            raise ProtocolError(
                "El conflicto escala de especialista a gerente y de gerente a SUPER_MANAGER (§45).",
                "denegado",
            )
    elif message_type == "decision":
        _validate_decision(body)
        load_task(root, task_id)
        if recipient not in record.get("puede_decidir_a", []):
            raise ProtocolError("No puedes emitir esa decisión a ese destinatario.", "denegado")
    elif message_type == "coordinacion":
        _validate_coordination(body)
        pair = {"MANAGER_MZ3_FRONTEND", "MANAGER_MZ4_BACKEND"}
        if agent_id not in pair or recipient not in pair or recipient == agent_id:
            raise ProtocolError(
                "La coordinación directa solo existe entre MANAGER_MZ3_FRONTEND y MANAGER_MZ4_BACKEND (§30).",
                "denegado",
            )
        task = load_task(root, task_id)
        if agent_id != task.get("manager") and not _coordination_reply(root, task_id, agent_id):
            raise ProtocolError(
                "Solo el gerente actual de la tarea abre la coordinación; el otro gerente puede responder.",
                "denegado",
            )

    message = {
        "message_id": new_id("msg"),
        "type": message_type,
        "from": agent_id,
        "to": recipient,
        "task_id": task_id,
        "timestamp": now(),
        "body": body,
        "copia_comando": False,
    }
    if simulate:
        return {
            "mensaje": "Simulación válida. No se escribió bandeja, estado ni compuerta.",
            "simulado": True,
            "type": message_type,
            "from": agent_id,
            "to": recipient,
            "task_id": task_id,
        }
    if message_type == "asignacion":
        _apply_assignment(root, agent_id, recipient, body)
    _deliver(root, message)
    if message_type == "coordinacion":
        copy = dict(message)
        copy["message_id"] = new_id("msg")
        copy["to"] = "SUPER_MANAGER_MZ0"
        copy["copia_comando"] = True
        copy["timestamp"] = now()
        _deliver(root, copy)
    _append_log(
        root,
        {
            "ts": message["timestamp"],
            "agente": agent_id,
            "accion": message_type,
            "tarea": task_id,
            "destino": recipient,
            "resumen": "Mensaje aceptado por el canal",
        },
    )
    return {
        "mensaje": f"Mensaje {message['message_id']} entregado a {recipient}.",
        "message_id": message["message_id"],
        "type": message_type,
        "task_id": task_id,
    }


def _coordination_reply(root: Path, task_id: str, agent_id: str) -> bool:
    inbox_dir = root / "canal" / "bandeja" / agent_id
    if not inbox_dir.is_dir():
        return False
    for path in inbox_dir.glob("*.json"):
        item = load_json(path)
        if item.get("type") == "coordinacion" and item.get("task_id") == task_id and not item.get("copia_comando"):
            return True
    return False


def set_gate(
    root: Path,
    agent_id: str,
    token: str,
    task_id: str,
    gate: str,
    value,
    evidence: list[str],
) -> dict:
    record = authenticate(root, agent_id, token)
    task = load_task(root, task_id)
    if task.get("closed"):
        raise ProtocolError("La tarea ya está cerrada.", "denegado")
    evidence = _evidence_list(evidence, minimum=3 if value in ("PASS", True) else 1, field="evidence")
    _scan(root, {"evidence": evidence, "gate": gate, "value": value})
    timestamp = now()
    if gate == "DESIGN_APPROVED":
        if value not in (True, False):
            raise ProtocolError("DESIGN_APPROVED solo admite true o false.", "uso")
        if value is True:
            if agent_id != "MANAGER_MZ2_DESIGN" or task.get("manager") != "MANAGER_MZ2_DESIGN":
                raise ProtocolError(
                    "Solo MANAGER_MZ2_DESIGN puede establecer DESIGN_APPROVED = TRUE, "
                    "y solo mientras la tarea está asignada a diseño (§42).",
                    "denegado",
                )
        elif agent_id not in ("MANAGER_MZ2_DESIGN", "SUPER_MANAGER_MZ0"):
            raise ProtocolError(
                "Solo diseño o SUPER_MANAGER pueden revocar DESIGN_APPROVED.",
                "denegado",
            )
        elif agent_id == "MANAGER_MZ2_DESIGN" and task.get("manager") != "MANAGER_MZ2_DESIGN":
            raise ProtocolError(
                "Diseño ya no es el gerente actual de esta tarea. Solo SUPER_MANAGER puede revocar la compuerta.",
                "denegado",
            )
    elif gate in QA_GATES:
        owner = GATE_OWNER[gate]
        if agent_id != owner:
            raise ProtocolError(
                f"Solo {owner} puede fijar {gate}. Otro agente no puede sellar esa compuerta (§44).",
                "denegado",
            )
        if value not in ("PASS", "FAIL"):
            raise ProtocolError("Las compuertas de QA solo admiten PASS o FAIL.", "uso")
        if task.get("manager") != "MANAGER_MZ5_QA" or agent_id not in _active_assignees(task):
            raise ProtocolError(
                "La compuerta de QA solo se fija cuando SUPER_MANAGER asignó la tarea a QA "
                "y el gerente de QA te delegó esa sección.",
                "denegado",
            )
        if value == "PASS" and len(evidence) < 3:
            raise ProtocolError("Un PASS exige al menos tres comprobaciones concretas (§44).", "esquema")
    else:
        raise ProtocolError("Compuerta desconocida.", "uso")

    gates = load_gates(root, task_id)
    gates["task_id"] = task_id
    gates.setdefault("gates", {})[gate] = {
        "value": value,
        "by": agent_id,
        "at": timestamp,
        "evidence": evidence,
    }
    _write_json(_gate_path(root, task_id), gates)
    recipients = []
    if gate == "DESIGN_APPROVED":
        recipients.append("SUPER_MANAGER_MZ0")
    else:
        recipients.append("MANAGER_MZ5_QA")
    for recipient in recipients:
        notice = {
            "message_id": new_id("msg"),
            "type": "revision",
            "from": agent_id,
            "to": recipient,
            "task_id": task_id,
            "timestamp": timestamp,
            "copia_comando": False,
            "body": {
                "gate": gate,
                "result": value,
                "evidence": evidence,
                "summary": f"{gate} fijada por {agent_id}",
            },
        }
        _deliver(root, notice)
    _append_log(
        root,
        {
            "ts": timestamp,
            "agente": agent_id,
            "accion": "compuerta",
            "tarea": task_id,
            "destino": recipients[0],
            "resumen": f"{gate}={value}",
        },
    )
    return {
        "mensaje": f"{gate} registrada por {agent_id}. Esto no afirma por sí solo que el producto haya sido probado fuera de la evidencia aportada.",
        "task_id": task_id,
        "gate": gate,
        "value": value,
        "by": agent_id,
    }


def consult_gates(root: Path, agent_id: str, token: str, task_id: str) -> dict:
    authenticate(root, agent_id, token)
    load_task(root, task_id)
    gates = load_gates(root, task_id)
    return {
        "mensaje": f"Compuertas de {task_id}. Visibles para sincronizar el estado; no sustituyen la evidencia.",
        "consultado_por": agent_id,
        "compuertas": gates,
    }


def implementation_allowed(root: Path, agent_id: str, token: str, task_id: str) -> dict:
    authenticate(root, agent_id, token)
    task = load_task(root, task_id)
    ui_change = task.get("ui_change", "none")
    if ui_change != "major":
        return {
            "permitido": True,
            "mensaje": "La tarea no está marcada como UI mayor. §42 no exige DESIGN_APPROVED para este caso.",
            "task_id": task_id,
            "ui_change": ui_change,
        }
    if task.get("excepcion_diseno"):
        return {
            "permitido": True,
            "mensaje": "Hay una excepción de §42 registrada con evidencia. No es una aprobación de diseño.",
            "task_id": task_id,
            "excepcion": task["excepcion_diseno"]["motivo"],
        }
    approved = _design_approved(root, task.get("design_task_id") or task_id)
    return {
        "permitido": approved,
        "mensaje": (
            "DESIGN_APPROVED = TRUE. La implementación de UI mayor puede comenzar."
            if approved
            else "DESIGN_APPROVED no es TRUE. La implementación de UI mayor no debe comenzar (§42)."
        ),
        "task_id": task_id,
        "design_task_id": task.get("design_task_id") or task_id,
    }


def close_task(root: Path, agent_id: str, token: str, task_id: str, evidence: list[str]) -> dict:
    authenticate(root, agent_id, token)
    if agent_id != "SUPER_MANAGER_MZ0":
        raise ProtocolError("Solo SUPER_MANAGER_MZ0 declara el cierre de una tarea (§3, §43).", "denegado")
    task = load_task(root, task_id)
    if task.get("closed"):
        raise ProtocolError("La tarea ya estaba cerrada.", "uso")
    evidence = _evidence_list(evidence, minimum=3, field="evidence")
    gates = load_gates(root, task_id).get("gates", {})
    missing = []
    for name in QA_GATES:
        entry = gates.get(name) or {}
        if entry.get("value") != "PASS" or entry.get("by") != GATE_OWNER[name]:
            missing.append(name)
    if missing:
        raise ProtocolError(
            "Cierre rechazado. §43 exige PASS de las cinco compuertas de QA, fijadas por su agente responsable. Faltan o no están en PASS: "
            + ", ".join(missing)
            + ".",
            "denegado",
        )
    if task.get("ui_change") == "major" and not task.get("excepcion_diseno"):
        design_task_id = _design_task_id(task)
        if not _design_approved(root, design_task_id):
            raise ProtocolError(
                "Cierre rechazado: la tarea es UI mayor y DESIGN_APPROVED no es TRUE.",
                "denegado",
            )
    timestamp = now()
    task["closed"] = True
    task["closed_at"] = timestamp
    task["closed_by"] = agent_id
    task["close_evidence"] = evidence
    task["updated_at"] = timestamp
    _write_json(_task_path(root, task_id), task)
    _append_log(
        root,
        {
            "ts": timestamp,
            "agente": agent_id,
            "accion": "cierre",
            "tarea": task_id,
            "destino": None,
            "resumen": "Compuertas de canal completas",
        },
    )
    return {
        "mensaje": (
            f"Tarea {task_id} cerrada en el canal. Este cierre solo comprueba que las compuertas "
            "exigidas fueron registradas por sus agentes, con evidencia. No afirma que un test "
            "de producto se haya ejecutado si esa evidencia no lo dice."
        ),
        "task_id": task_id,
        "closed": True,
    }


def consult_task(root: Path, agent_id: str, token: str, task_id: str) -> dict:
    authenticate(root, agent_id, token)
    task = load_task(root, task_id)
    allowed = agent_id == "SUPER_MANAGER_MZ0" or _sender_on_task(agent_id, task)
    # El gerente que ya no es el actual puede necesitar el historial si participó.
    history_managers = {item.get("manager") for item in task.get("historial", [])}
    past_assignees = {item.get("assignee") for item in task.get("delegaciones", [])}
    if agent_id in history_managers or agent_id in past_assignees:
        allowed = True
    if not allowed:
        raise ProtocolError(
            "Esta tarea no está en tu sección. Recibirás el paquete si tu gerente o SUPER_MANAGER te lo asigna.",
            "denegado",
        )
    return {"mensaje": f"Tarea {task_id}.", "tarea": task}
