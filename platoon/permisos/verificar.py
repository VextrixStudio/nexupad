#!/usr/bin/env python3
"""Comprueba credenciales y el alcance de cada agente.

No imprime secretos. El aislamiento es lógico: esta herramienta es la
autoridad que la orquestación debe consultar antes de leer o escribir
fuera de la carpeta del agente.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from politica import ProtocolError, check_access, platoon_root, public_identity, read_file, resolve_token, rotate_secret, write_file  # noqa: E402


def _token(args) -> str:
    return resolve_token(platoon_root(), args.agente, args.token, args.usar_secreto_local)


def _emit(payload: dict, as_json: bool, ok: bool) -> int:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload.get("mensaje") or payload.get("motivo") or json.dumps(payload, ensure_ascii=False))
        if not ok and payload.get("motivo") and payload.get("mensaje") != payload.get("motivo"):
            print(payload["motivo"])
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Permisos por sección del pelotón NexuPad.")
    parser.add_argument("--json", action="store_true", help="Salida JSON.")
    sub = parser.add_subparsers(dest="comando", required=True)

    ident = sub.add_parser("identidad", help="Muestra el identificador público, nunca el secreto.")
    ident.add_argument("--agente", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--agente", required=True)
    common.add_argument("--token", default=None)
    common.add_argument("--usar-secreto-local", action="store_true")

    check = sub.add_parser("comprobar", parents=[common], help="Dice si la ruta cae en la sección del agente.")
    check.add_argument("--ruta", required=True)
    check.add_argument("--operacion", required=True, choices=("leer", "escribir"))

    read = sub.add_parser("leer", parents=[common], help="Lee un archivo si el alcance lo permite.")
    read.add_argument("--ruta", required=True)

    save = sub.add_parser("guardar", parents=[common], help="Escribe un archivo si el alcance lo permite.")
    save.add_argument("--ruta", required=True)
    source = save.add_mutually_exclusive_group(required=True)
    source.add_argument("--contenido")
    source.add_argument("--contenido-archivo")

    sub.add_parser("rotar", parents=[common], help="Rota el secreto propio. No lo imprime.")

    args = parser.parse_args(argv)
    try:
        if args.comando == "identidad":
            payload = public_identity(platoon_root(), args.agente)
            payload["mensaje"] = (
                f"{args.agente}: {payload['credential_id']} · {payload['modulo']}/{payload['seccion']}. "
                "Secreto no mostrado."
            )
            return _emit(payload, args.json, True)
        token = _token(args)
        root = platoon_root()
        if args.comando == "comprobar":
            payload = check_access(root, args.agente, token, args.ruta, args.operacion)
            payload["mensaje"] = "PERMISO CONCEDIDO" if payload["permitido"] else "PERMISO DENEGADO"
            if payload["motivo"]:
                payload["mensaje"] += f"\n{payload['motivo']}"
            return _emit(payload, args.json, payload["permitido"])
        if args.comando == "leer":
            payload = read_file(root, args.agente, token, args.ruta)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(payload["contenido"], end="" if payload["contenido"].endswith("\n") else "\n")
            return 0
        if args.comando == "guardar":
            content = args.contenido
            if args.contenido_archivo:
                content = Path(args.contenido_archivo).read_text(encoding="utf-8")
            payload = write_file(root, args.agente, token, args.ruta, content)
            return _emit(payload, args.json, True)
        if args.comando == "rotar":
            payload = rotate_secret(root, args.agente, token)
            return _emit(payload, args.json, True)
        parser.error("comando no reconocido")
        return 1
    except ProtocolError as exc:
        payload = {"mensaje": str(exc), "codigo": exc.code, "permitido": False}
        return _emit(payload, args.json, False)


if __name__ == "__main__":
    sys.exit(main())
