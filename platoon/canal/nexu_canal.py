#!/usr/bin/env python3
"""Canal de sincronización entre agentes del pelotón NexuPad.

Autentica la credencial del emisor y solo entonces acepta asignaciones,
handoffs, revisiones, conflictos, coordinación o cambios de estado.
No imprime secretos ni cuerpos de bandejas ajenas.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from buzon import (  # noqa: E402
    board,
    close_task,
    consult_gates,
    consult_task,
    implementation_allowed,
    inbox,
    publish,
    set_gate,
    update_state,
)
from politica import ProtocolError, platoon_root, resolve_token  # noqa: E402


def _emit(payload: dict, as_json: bool, ok: bool = True) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("mensaje", ""))
        extra = {key: value for key, value in payload.items() if key != "mensaje"}
        if extra and not ok:
            print(json.dumps(extra, ensure_ascii=False, indent=2))
        elif extra and as_json:
            print(json.dumps(extra, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def _print_human(payload: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("mensaje", ""))
        for key in ("message_id", "task_id", "gate", "value", "total", "permitido"):
            if key in payload and key not in ("mensaje",):
                print(f"{key}: {payload[key]}")
        if "estados" in payload:
            for item in payload["estados"]:
                print(
                    f"- {item.get('agent_id')}: {item.get('status')} · "
                    f"{item.get('activity')} · tarea={item.get('task_id') or '—'}"
                )
        if "mensajes" in payload:
            for item in payload["mensajes"]:
                copia = " · copia a comando" if item.get("copia_comando") else ""
                print(
                    f"- {item.get('message_id')} {item.get('type')} de {item.get('from')} "
                    f"tarea={item.get('task_id')}{copia}"
                )
        if "mensaje_completo" in payload:
            print(json.dumps(payload["mensaje_completo"], ensure_ascii=False, indent=2))
        if "compuertas" in payload:
            print(json.dumps(payload["compuertas"], ensure_ascii=False, indent=2))
        if "tarea" in payload:
            print(json.dumps(payload["tarea"], ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canal de estados y entregas del pelotón NexuPad.")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="comando", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--agente", required=True)
    common.add_argument("--token", default=None)
    common.add_argument("--usar-secreto-local", action="store_true")

    send = sub.add_parser("publicar", parents=[common])
    send.add_argument("--archivo", required=True)
    send.add_argument("--simular", action="store_true")

    state = sub.add_parser("estado", parents=[common])
    state.add_argument("--status", required=True)
    state.add_argument("--actividad", required=True)
    state.add_argument("--task", default=None)

    sub.add_parser("sincronizar", parents=[common])

    box = sub.add_parser("bandeja", parents=[common])
    box.add_argument("--id", default=None)

    gate = sub.add_parser("compuerta")
    gate_sub = gate.add_subparsers(dest="accion_compuerta", required=True)
    fix = gate_sub.add_parser("fijar", parents=[common])
    fix.add_argument("--task", required=True)
    fix.add_argument("--compuerta", required=True)
    fix.add_argument("--resultado", required=True)
    fix.add_argument("--evidencia", action="append", required=True)
    show = gate_sub.add_parser("consultar", parents=[common])
    show.add_argument("--task", required=True)
    allow = gate_sub.add_parser("puede-implementar", parents=[common])
    allow.add_argument("--task", required=True)

    close = sub.add_parser("cerrar", parents=[common])
    close.add_argument("--task", required=True)
    close.add_argument("--evidencia", action="append", required=True)

    task = sub.add_parser("tarea", parents=[common])
    task.add_argument("--task", required=True)

    args = parser.parse_args(argv)
    try:
        root = platoon_root()
        token = resolve_token(root, args.agente, args.token, args.usar_secreto_local)
        if args.comando == "publicar":
            envelope = json.loads(Path(args.archivo).read_text(encoding="utf-8"))
            payload = publish(root, args.agente, token, envelope, simulate=args.simular)
            return _print_human(payload, args.json)
        if args.comando == "estado":
            payload = update_state(root, args.agente, token, args.status, args.actividad, args.task)
            return _print_human(payload, args.json)
        if args.comando == "sincronizar":
            payload = board(root, args.agente, token)
            return _print_human(payload, args.json)
        if args.comando == "bandeja":
            payload = inbox(root, args.agente, token, args.id)
            return _print_human(payload, args.json)
        if args.comando == "compuerta" and args.accion_compuerta == "fijar":
            raw = args.resultado
            if raw in ("true", "false"):
                value = raw == "true"
            else:
                value = raw
            payload = set_gate(root, args.agente, token, args.task, args.compuerta, value, args.evidencia)
            return _print_human(payload, args.json)
        if args.comando == "compuerta" and args.accion_compuerta == "consultar":
            payload = consult_gates(root, args.agente, token, args.task)
            return _print_human(payload, args.json)
        if args.comando == "compuerta" and args.accion_compuerta == "puede-implementar":
            payload = implementation_allowed(root, args.agente, token, args.task)
            return _print_human(payload, args.json)
        if args.comando == "cerrar":
            payload = close_task(root, args.agente, token, args.task, args.evidencia)
            return _print_human(payload, args.json)
        if args.comando == "tarea":
            payload = consult_task(root, args.agente, token, args.task)
            return _print_human(payload, args.json)
        parser.error("comando no reconocido")
        return 1
    except ProtocolError as exc:
        return _emit({"mensaje": str(exc), "codigo": exc.code}, args.json, False)
    except json.JSONDecodeError as exc:
        return _emit({"mensaje": f"JSON inválido: {exc}", "codigo": "uso"}, args.json, False)


if __name__ == "__main__":
    sys.exit(main())
