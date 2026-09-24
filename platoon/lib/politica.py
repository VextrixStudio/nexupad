#!/usr/bin/env python3
"""Control de acceso lógico del pelotón NexuPad.

Un solo usuario de sistema opera este entorno. El aislamiento entre agentes
no es una cuenta del sistema operativo: es una política que estas funciones
aplican cuando la orquestación usa las herramientas del pelotón.

Las credenciales se comparan con el archivo secreto local (gitignored) y con
la huella SHA-256 publicada. Un desajuste de huella se trata como alteración.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from pathlib import Path


AGENT_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,64}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{32,128}$")

FROZEN_BASENAMES = {
    "TAREAS.md",
    "perfil.json",
    "INDICE.md",
    "agentes.md",
    "README.md",
}

# Rutas que ningún agente puede escribir mediante la herramienta, aunque
# una concesión futura las incluya por error. El canal lo escribe buzon.py
# después de autenticar; no se edita con `guardar`.
WRITE_HARD_DENY_PREFIXES = (
    "permisos/secretos/",
    "canal/",
    "lib/",
    "hooks/",
    "agentes.md",
)


class ProtocolError(Exception):
    def __init__(self, message: str, code: str = "denegado"):
        super().__init__(message)
        self.code = code


def platoon_root() -> Path:
    override = os.environ.get("PLATOON_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[1]


def repo_root(root: Path | None = None) -> Path:
    return (root or platoon_root()).parent


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError(f"No existe {path.name}.", "configuracion") from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"JSON inválido en {path.name}: {exc}", "configuracion") from exc


def matriz(root: Path | None = None) -> dict:
    root = root or platoon_root()
    data = load_json(root / "permisos" / "matriz.json")
    if "agentes" not in data:
        raise ProtocolError("matriz.json sin agentes.", "configuracion")
    return data


def huellas(root: Path | None = None) -> dict:
    root = root or platoon_root()
    return load_json(root / "permisos" / "huellas.json")


def require_agent_id(agent_id: str) -> str:
    if not agent_id or not AGENT_ID_RE.match(agent_id):
        raise ProtocolError("Identificador de agente inválido.", "uso")
    return agent_id


def secret_path(root: Path, agent_id: str) -> Path:
    require_agent_id(agent_id)
    return root / "permisos" / "secretos" / f"{agent_id}.token"


def resolve_token(root: Path, agent_id: str, token: str | None, use_local_secret: bool) -> str:
    require_agent_id(agent_id)
    if token:
        supplied = token.strip()
    elif os.environ.get(f"NEXUPAD_TOKEN_{agent_id}"):
        supplied = os.environ[f"NEXUPAD_TOKEN_{agent_id}"].strip()
    elif use_local_secret:
        path = secret_path(root, agent_id)
        if not path.is_file():
            raise ProtocolError(
                "No hay secreto local para este agente. No se emite ni se muestra una credencial ajena.",
                "autenticacion",
            )
        supplied = path.read_text(encoding="utf-8").strip()
    else:
        raise ProtocolError(
            "Falta la credencial. Pasa --token, exporta la variable de entorno del agente "
            "o usa --usar-secreto-local para leer solo su propio archivo.",
            "uso",
        )
    if not TOKEN_RE.match(supplied):
        raise ProtocolError("Credencial rechazada.", "autenticacion")
    return supplied


def authenticate(root: Path, agent_id: str, token: str) -> dict:
    require_agent_id(agent_id)
    data = matriz(root)
    record = data["agentes"].get(agent_id)
    if record is None:
        raise ProtocolError("Agente desconocido.", "autenticacion")
    path = secret_path(root, agent_id)
    if not path.is_file():
        raise ProtocolError("Credencial rechazada.", "autenticacion")
    expected = path.read_text(encoding="utf-8").strip()
    if not hmac.compare_digest(expected, token):
        raise ProtocolError("Credencial rechazada.", "autenticacion")
    fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
    published = huellas(root).get("agentes", {}).get(agent_id, {}).get("sha256")
    if not published or not hmac.compare_digest(published, fingerprint):
        raise ProtocolError(
            "Credencial rechazada: la huella publicada no coincide con el secreto local.",
            "autenticacion",
        )
    return record


def to_rel(root: Path, user_path: str) -> str:
    """Normaliza una ruta de usuario a una ruta relativa al pelotón, sin salir de él."""
    if user_path is None or user_path.strip() == "":
        raise ProtocolError("Ruta vacía.", "uso")
    raw = user_path.strip()
    if "\x00" in raw or raw.startswith("~"):
        raise ProtocolError("Ruta rechazada.", "denegado")
    root = root.resolve()
    repo = root.parent
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        posix = raw.replace("\\", "/")
        if posix.startswith("./"):
            posix = posix[2:]
        if posix == "platoon" or posix.startswith("platoon/"):
            resolved = (repo / posix).resolve()
        else:
            resolved = (root / posix).resolve()
    if resolved != root and root not in resolved.parents:
        raise ProtocolError(
            "Permiso denegado: la ruta está fuera del pelotón y de la sección asignada.",
            "denegado",
        )
    if resolved == root:
        return "."
    return resolved.relative_to(root).as_posix()


def _matches(rel: str, pattern: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith("/"):
        prefix = pattern[:-1]
        return rel == prefix or rel.startswith(prefix + "/")
    return rel == pattern


def _denied(rel: str, patterns: list[str]) -> bool:
    return any(_matches(rel, pattern) for pattern in patterns)


def can_read(record: dict, rel: str) -> bool:
    denied = list(record.get("lectura_denegada") or [])
    # Nadie lee secretos por la herramienta de lectura, ni el propio token.
    denied.append("permisos/secretos/")
    if rel == "permisos/secretos" or _denied(rel, denied):
        return False
    patterns = list(record.get("lectura") or [])
    if "*" in patterns:
        return True
    return any(_matches(rel, pattern) for pattern in patterns)


def can_write(record: dict, rel: str) -> bool:
    if rel in ("", "."):
        return False
    basename = Path(rel).name
    if basename in FROZEN_BASENAMES:
        return False
    if rel.startswith(WRITE_HARD_DENY_PREFIXES) or rel in WRITE_HARD_DENY_PREFIXES:
        return False
    for prefix in WRITE_HARD_DENY_PREFIXES:
        if prefix.endswith("/") and rel.startswith(prefix):
            return False
        if rel == prefix.rstrip("/"):
            return False
    patterns = list(record.get("escritura") or [])
    return any(_matches(rel, pattern) for pattern in patterns)


def explain_scope(record: dict) -> str:
    modulo = record.get("modulo", "sin módulo")
    seccion = record.get("seccion", "sin sección")
    return f"módulo «{modulo}», sección «{seccion}»"


def check_access(root: Path, agent_id: str, token: str, user_path: str, operation: str) -> dict:
    record = authenticate(root, agent_id, token)
    op = operation.strip().lower()
    if op not in ("leer", "escribir"):
        raise ProtocolError("Operación no reconocida. Usa leer o escribir.", "uso")
    rel = to_rel(root, user_path)
    allowed = can_read(record, rel) if op == "leer" else can_write(record, rel)
    return {
        "permitido": allowed,
        "agente": agent_id,
        "operacion": op,
        "ruta": rel,
        "alcance": explain_scope(record),
        "motivo": None
        if allowed
        else (
            f"La credencial de {agent_id} solo cubre {explain_scope(record)}. "
            f"No puede {op} «{rel}»."
        ),
    }


def read_file(root: Path, agent_id: str, token: str, user_path: str) -> dict:
    decision = check_access(root, agent_id, token, user_path, "leer")
    if not decision["permitido"]:
        raise ProtocolError(decision["motivo"], "denegado")
    path = root / decision["ruta"]
    if not path.is_file():
        raise ProtocolError("No hay un archivo legible en esa ruta.", "uso")
    return {
        "agente": agent_id,
        "ruta": decision["ruta"],
        "contenido": path.read_text(encoding="utf-8"),
    }


def write_file(root: Path, agent_id: str, token: str, user_path: str, content: str) -> dict:
    if not isinstance(content, str):
        raise ProtocolError("El contenido debe ser texto.", "uso")
    if len(content.encode("utf-8")) > 2_000_000:
        raise ProtocolError("El contenido supera el límite de 2 MB de la herramienta.", "uso")
    reject_if_contains_secret(root, content)
    decision = check_access(root, agent_id, token, user_path, "escribir")
    if not decision["permitido"]:
        raise ProtocolError(decision["motivo"], "denegado")
    path = root / decision["ruta"]
    if path.exists() and not path.is_file():
        raise ProtocolError("El destino no es un archivo.", "uso")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {
        "agente": agent_id,
        "ruta": decision["ruta"],
        "bytes": len(content.encode("utf-8")),
        "mensaje": f"Escritura permitida en la sección de {agent_id}: {decision['ruta']}",
    }


def reject_if_contains_secret(root: Path, text: str) -> None:
    secret_dir = root / "permisos" / "secretos"
    if not secret_dir.is_dir():
        return
    for path in secret_dir.glob("*.token"):
        secret = path.read_text(encoding="utf-8").strip()
        if secret and secret in text:
            raise ProtocolError(
                "Rechazado: el contenido incluye una credencial. §58 prohíbe exponer secretos.",
                "denegado",
            )


def public_identity(root: Path, agent_id: str) -> dict:
    require_agent_id(agent_id)
    record = matriz(root)["agentes"].get(agent_id)
    if record is None:
        raise ProtocolError("Agente desconocido.", "autenticacion")
    directory = load_json(root / "permisos" / "credenciales.json")
    published = directory.get("agentes", {}).get(agent_id, {})
    return {
        "agente": agent_id,
        "credential_id": published.get("credential_id"),
        "modulo": record.get("modulo"),
        "seccion": record.get("seccion"),
        "rango": record.get("rango"),
        "reporta_a": record.get("reporta_a"),
        "variable_entorno": published.get("variable_entorno"),
        "archivo_secreto": published.get("archivo_secreto"),
        "aviso": "El secreto no se muestra. Está solo en el archivo local gitignored o en la variable de entorno.",
    }


def rotate_secret(root: Path, agent_id: str, token: str) -> dict:
    authenticate(root, agent_id, token)
    import secrets

    new_token = secrets.token_urlsafe(32)
    path = secret_path(root, agent_id)
    path.write_text(new_token + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    fingerprint = hashlib.sha256(new_token.encode("utf-8")).hexdigest()
    stamp_path = root / "permisos" / "huellas.json"
    data = load_json(stamp_path)
    data.setdefault("agentes", {}).setdefault(agent_id, {})["sha256"] = fingerprint
    stamp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "agente": agent_id,
        "mensaje": (
            f"Credencial rotada para {agent_id}. El nuevo secreto quedó en "
            f"{path.relative_to(root).as_posix()} con modo 600. No se imprime."
        ),
        "huella_sha256": fingerprint,
    }
