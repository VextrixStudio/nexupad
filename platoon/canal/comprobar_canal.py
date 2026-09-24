#!/usr/bin/env python3
"""Comprueba el canal y los permisos contra una copia temporal.

No toca el pelotón real, no imprime secretos y no declara QA de producto.
El objeto de estas comprobaciones es solo el mecanismo de secciones y de
sincronización. Salida: una línea PASS o FAIL por caso.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REAL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL / "lib"))

import buzon  # noqa: E402
import politica  # noqa: E402
from politica import ProtocolError  # noqa: E402


FAILURES = 0


def check(name: str, fn) -> None:
    global FAILURES
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — el informe debe decir qué caso falló.
        FAILURES += 1
        print(f"FAIL  {name}: {exc}")
        return
    print(f"PASS  {name}")


def expect_deny(fn) -> None:
    try:
        result = fn()
    except ProtocolError:
        return
    if isinstance(result, dict) and result.get("permitido") is False:
        return
    raise AssertionError("se esperaba un rechazo y la operación fue aceptada")


def token(root: Path, agent_id: str) -> str:
    return (root / "permisos" / "secretos" / f"{agent_id}.token").read_text(encoding="utf-8").strip()


def assignment(task_id: str, manager: str, objective: str, **extra) -> dict:
    body = {
        "task_id": task_id,
        "objective": objective,
        "manager": manager,
        "priority": "high",
        "dependencies": [],
        "constraints": ["mobile-first"],
        "deliverables": ["informe de la sección"],
        "review_required": True,
    }
    body.update(extra)
    return body


def handoff(task_id: str, next_agent: str) -> dict:
    return {
        "TASK": task_id,
        "STATUS": "entregado",
        "WHAT WAS INVESTIGATED": "Se inspeccionó solo el paquete de esta tarea de prueba del canal.",
        "WHAT WAS CHANGED": "Nada en el producto. La prueba solo mueve un mensaje.",
        "DECISIONS": "Ninguna decisión de producto en esta prueba.",
        "EVIDENCE": ["El mensaje cumple los once campos de la sección 41 y no cita fuentes no abiertas."],
        "FILES AFFECTED": [],
        "DEPENDENCIES": [],
        "RISKS": "Ninguno sobre el producto: el fixture es temporal.",
        "OPEN QUESTIONS": [],
        "NEXT AGENT": next_agent,
    }


def evidence(prefix: str) -> list[str]:
    return [
        f"{prefix}: se comprobó el primer criterio con un resultado observado.",
        f"{prefix}: se comprobó el segundo criterio y no se usó un sello vacío.",
        f"{prefix}: se comprobó el tercer criterio sobre el fixture, no sobre el producto.",
    ]


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="platoon-check-"))
    root = tmp / "platoon"
    shutil.copytree(REAL, root, ignore=shutil.ignore_patterns("__pycache__"))
    super_id = "SUPER_MANAGER_MZ0"
    mz1 = "MANAGER_MZ1_RESEARCH"
    mz2 = "MANAGER_MZ2_DESIGN"
    mz3 = "MANAGER_MZ3_FRONTEND"
    mz4 = "MANAGER_MZ4_BACKEND"
    mz5 = "MANAGER_MZ5_QA"
    buscador = "BUSCADOR_MZ1"
    analyst = "ANALYST_MZ2"
    apple = "APPLE_REVIEWER_MZ"
    google = "GOOGLE_REVIEWER_MZ"
    functional = "FUNCTIONAL_QA_MZ"
    visual = "VISUAL_QA_MZ"

    def t(agent_id: str) -> str:
        return token(root, agent_id)

    check("credencial propia aceptada", lambda: politica.authenticate(root, buscador, t(buscador)))
    check(
        "credencial ajena rechazada",
        lambda: expect_deny(lambda: politica.authenticate(root, buscador, t(analyst))),
    )
    check(
        "agente desconocido rechazado",
        lambda: expect_deny(lambda: politica.authenticate(root, "AGENTE_INVENTADO", t(buscador))),
    )

    def write_own():
        politica.write_file(root, buscador, t(buscador), "agentes/BUSCADOR_MZ1/entregables/ficha.json", "{}\n")

    check("especialista escribe en su sección", write_own)
    check(
        "especialista no reescribe sus tareas asignadas",
        lambda: expect_deny(
            lambda: politica.write_file(root, buscador, t(buscador), "agentes/BUSCADOR_MZ1/TAREAS.md", "alterado\n")
        ),
    )
    check(
        "especialista no escribe en otra sección",
        lambda: expect_deny(
            lambda: politica.write_file(
                root, buscador, t(buscador), "agentes/ANALYST_MZ2/entregables/intrusion.md", "no\n"
            )
        ),
    )
    check(
        "especialista no lee la carpeta de otro especialista",
        lambda: expect_deny(lambda: politica.read_file(root, apple, t(apple), "agentes/GOOGLE_REVIEWER_MZ/TAREAS.md")),
    )
    check(
        "gerente lee a su equipo y no al equipo ajeno",
        lambda: (
            politica.read_file(root, mz2, t(mz2), "agentes/APPLE_REVIEWER_MZ/TAREAS.md"),
            expect_deny(lambda: politica.read_file(root, mz2, t(mz2), "agentes/BUSCADOR_MZ1/TAREAS.md")),
        ),
    )
    check(
        "gerente no reescribe el entregable de su equipo",
        lambda: expect_deny(
            lambda: politica.write_file(root, mz1, t(mz1), "agentes/BUSCADOR_MZ1/entregables/ficha.json", "pisado\n")
        ),
    )
    check(
        "investigación escribe solo su memoria",
        lambda: (
            politica.write_file(root, mz1, t(mz1), "memoria/RESEARCH.md", "# informe\n"),
            expect_deny(lambda: politica.write_file(root, mz1, t(mz1), "memoria/DESIGN_SYSTEM.md", "no\n")),
        ),
    )
    check(
        "comando no lee secretos ni escribe el control",
        lambda: (
            expect_deny(lambda: politica.read_file(root, super_id, t(super_id), f"permisos/secretos/{buscador}.token")),
            expect_deny(lambda: politica.write_file(root, super_id, t(super_id), "lib/politica.py", "alterado\n")),
        ),
    )
    check(
        "ruta fuera del pelotón rechazada",
        lambda: (
            expect_deny(lambda: politica.check_access(root, super_id, t(super_id), "../README.md", "escribir")),
            expect_deny(
                lambda: politica.check_access(
                    root,
                    buscador,
                    t(buscador),
                    "agentes/BUSCADOR_MZ1/entregables/../../../README.md",
                    "escribir",
                )
            ),
        ),
    )
    check(
        "el contenido con un secreto se rechaza",
        lambda: expect_deny(
            lambda: politica.write_file(
                root,
                buscador,
                t(buscador),
                "agentes/BUSCADOR_MZ1/entregables/fuga.md",
                "token=" + t(buscador),
            )
        ),
    )

    def flow():
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz1,
                "task_id": "NXP-0101",
                "body": assignment("NXP-0101", mz1, "Probar el enrutado de investigación sin tocar el producto."),
            },
        )
        expect_deny(
            lambda: buzon.publish(
                root,
                super_id,
                t(super_id),
                {
                    "type": "asignacion",
                    "to": buscador,
                    "task_id": "NXP-0109",
                    "body": assignment("NXP-0109", buscador, "Asignación directa que la sección 3 no permite."),
                },
            )
        )
        buzon.publish(
            root,
            mz1,
            t(mz1),
            {
                "type": "asignacion",
                "to": buscador,
                "task_id": "NXP-0101",
                "body": assignment(
                    "NXP-0101",
                    mz1,
                    "Delegar la recolección de esta prueba de canal.",
                    assignee=buscador,
                ),
            },
        )
        expect_deny(
            lambda: buzon.publish(
                root,
                mz1,
                t(mz1),
                {
                    "type": "asignacion",
                    "to": apple,
                    "task_id": "NXP-0101",
                    "body": assignment("NXP-0101", mz1, "Un gerente no asigna fuera de su equipo.", assignee=apple),
                },
            )
        )
        buzon.publish(
            root,
            buscador,
            t(buscador),
            {"type": "handoff", "to": analyst, "task_id": "NXP-0101", "body": handoff("NXP-0101", analyst)},
        )
        expect_deny(
            lambda: buzon.publish(
                root,
                buscador,
                t(buscador),
                {"type": "handoff", "to": mz2, "task_id": "NXP-0101", "body": handoff("NXP-0101", mz2)},
            )
        )
        incomplete = handoff("NXP-0101", analyst)
        incomplete["EVIDENCE"] = ["Looks good."]
        expect_deny(
            lambda: buzon.publish(
                root,
                buscador,
                t(buscador),
                {"type": "handoff", "to": analyst, "task_id": "NXP-0101", "body": incomplete},
            )
        )

    check("cadena de mando, handoff interno y sello vacío", flow)

    def design_and_ui():
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz2,
                "task_id": "NXP-0102",
                "body": assignment("NXP-0102", mz2, "Tarea de diseño de prueba, sin producto real.", ui_change="none"),
            },
        )
        expect_deny(
            lambda: buzon.publish(
                root,
                super_id,
                t(super_id),
                {
                    "type": "asignacion",
                    "to": mz3,
                    "task_id": "NXP-0103",
                    "body": assignment(
                        "NXP-0103",
                        mz3,
                        "UI mayor sin compuerta de diseño, debe bloquearse.",
                        ui_change="major",
                        design_task_id="NXP-0102",
                    ),
                },
            )
        )
        buzon.set_gate(root, mz2, t(mz2), "NXP-0102", "DESIGN_APPROVED", True, evidence("diseño"))
        expect_deny(lambda: buzon.set_gate(root, super_id, t(super_id), "NXP-0102", "DESIGN_APPROVED", True, evidence("comando")))
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz3,
                "task_id": "NXP-0103",
                "body": assignment(
                    "NXP-0103",
                    mz3,
                    "UI mayor ya con diseño aprobado en la tarea de prueba.",
                    ui_change="major",
                    design_task_id="NXP-0102",
                ),
            },
        )
        allowed = buzon.implementation_allowed(root, mz3, t(mz3), "NXP-0103")
        if not allowed["permitido"]:
            raise AssertionError(allowed["mensaje"])
        buzon.set_gate(
            root,
            super_id,
            t(super_id),
            "NXP-0102",
            "DESIGN_APPROVED",
            False,
            ["Comando revoca la compuerta de diseño de esta prueba con un motivo explícito."],
        )
        revoked = buzon.implementation_allowed(root, mz3, t(mz3), "NXP-0103")
        if revoked["permitido"]:
            raise AssertionError("la revocación no bloqueó la UI mayor")
        expect_deny(
            lambda: buzon.publish(
                root,
                super_id,
                t(super_id),
                {
                    "type": "asignacion",
                    "to": mz3,
                    "task_id": "NXP-0104",
                    "body": assignment(
                        "NXP-0104",
                        mz3,
                        "Excepción con sello vacío, debe rechazarse.",
                        ui_change="major",
                        excepcion_diseno={"motivo": "ajuste visual minimo", "evidence": ["Looks good."]},
                    ),
                },
            )
        )

    check("compuerta de diseño, UI mayor y revocación", design_and_ui)

    def reviews():
        buzon.publish(
            root,
            mz2,
            t(mz2),
            {
                "type": "asignacion",
                "to": apple,
                "task_id": "NXP-0102",
                "body": assignment("NXP-0102", mz2, "Encargar la crítica independiente de esta prueba.", assignee=apple),
            },
        )
        buzon.publish(
            root,
            apple,
            t(apple),
            {
                "type": "revision",
                "to": mz2,
                "task_id": "NXP-0102",
                "body": {
                    "summary": "La prueba no contiene una propuesta de interfaz que copiar.",
                    "findings": ["No hay pantalla propietaria en el fixture."],
                    "evidence": ["Se revisó el encargo de prueba, no una interfaz de otra compañía."],
                    "verdict": "observaciones",
                    "copied_interface": False,
                },
            },
        )
        expect_deny(
            lambda: buzon.publish(
                root,
                apple,
                t(apple),
                {
                    "type": "revision",
                    "to": google,
                    "task_id": "NXP-0102",
                    "body": {
                        "summary": "Un revisor no alinea su informe con otro revisor.",
                        "evidence": ["Este envío debe ser rechazado por la cadena de mando."],
                    },
                },
            )
        )

    check("revisores independientes", reviews)

    def coordination():
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz4,
                "task_id": "NXP-0106",
                "body": assignment("NXP-0106", mz4, "Tarea backend de prueba para la coordinación de la sección 30."),
            },
        )
        buzon.publish(
            root,
            mz4,
            t(mz4),
            {
                "type": "coordinacion",
                "to": mz3,
                "task_id": "NXP-0106",
                "body": {
                    "change": "Ningún contrato real cambia en esta prueba del canal.",
                    "frontend_impact": "No hay frontend que alterar; el mensaje solo comprueba la copia a comando.",
                },
            },
        )
        copies = [
            item
            for item in buzon.inbox(root, super_id, t(super_id))["mensajes"]
            if item.get("copia_comando") and item.get("task_id") == "NXP-0106"
        ]
        if len(copies) != 1:
            raise AssertionError(f"se esperaba una copia a comando, hubo {len(copies)}")
        expect_deny(
            lambda: buzon.publish(
                root,
                mz4,
                t(mz4),
                {"type": "handoff", "to": mz3, "task_id": "NXP-0106", "body": handoff("NXP-0106", mz3)},
            )
        )

    check("coordinación backend-frontend con copia a comando", coordination)

    def qa_and_close():
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz5,
                "task_id": "NXP-0105",
                "body": assignment("NXP-0105", mz5, "Verificar solo el mecanismo, no el producto."),
            },
        )
        expect_deny(lambda: buzon.close_task(root, super_id, t(super_id), "NXP-0105", evidence("cierre prematuro")))
        owners = {
            "FUNCTIONAL_QA": "FUNCTIONAL_QA_MZ",
            "VISUAL_QA": "VISUAL_QA_MZ",
            "ACCESSIBILITY_QA": "ACCESSIBILITY_QA_MZ",
            "PERFORMANCE_QA": "PERFORMANCE_QA_MZ",
            "REGRESSION_QA": "REGRESSION_QA_MZ",
        }
        for gate, owner in owners.items():
            buzon.publish(
                root,
                mz5,
                t(mz5),
                {
                    "type": "asignacion",
                    "to": owner,
                    "task_id": "NXP-0105",
                    "body": assignment("NXP-0105", mz5, f"Delegar la compuerta {gate} de esta prueba.", assignee=owner),
                },
            )
            buzon.set_gate(root, owner, t(owner), "NXP-0105", gate, "PASS", evidence(gate))
        expect_deny(
            lambda: buzon.set_gate(root, functional, t(functional), "NXP-0105", "VISUAL_QA", "PASS", evidence("ajena"))
        )
        expect_deny(
            lambda: buzon.set_gate(root, super_id, t(super_id), "NXP-0105", "FUNCTIONAL_QA", "PASS", evidence("comando"))
        )
        expect_deny(
            lambda: buzon.set_gate(root, visual, t(visual), "NXP-0105", "VISUAL_QA", "PASS", ["Looks good.", "ok", "aprobado"])
        )
        closed = buzon.close_task(root, super_id, t(super_id), "NXP-0105", evidence("cierre de canal"))
        if not closed["closed"]:
            raise AssertionError("el cierre no quedó registrado")
        expect_deny(lambda: buzon.close_task(root, mz5, t(mz5), "NXP-0105", evidence("qa no cierra")))

    check("QA por dueño, sello vacío y cierre solo de comando", qa_and_close)

    def invalidate():
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz5,
                "task_id": "NXP-0107",
                "body": assignment("NXP-0107", mz5, "Segunda tarea para comprobar que el retrabajo invalida QA."),
            },
        )
        buzon.publish(
            root,
            mz5,
            t(mz5),
            {
                "type": "asignacion",
                "to": functional,
                "task_id": "NXP-0107",
                "body": assignment("NXP-0107", mz5, "Delegar funcional de la segunda prueba.", assignee=functional),
            },
        )
        buzon.set_gate(root, functional, t(functional), "NXP-0107", "FUNCTIONAL_QA", "PASS", evidence("antes del retrabajo"))
        buzon.publish(
            root,
            super_id,
            t(super_id),
            {
                "type": "asignacion",
                "to": mz3,
                "task_id": "NXP-0107",
                "body": assignment("NXP-0107", mz3, "Sacar la tarea de QA para forzar un retest."),
            },
        )
        gates = buzon.consult_gates(root, mz5, t(mz5), "NXP-0107")["compuertas"]["gates"]["FUNCTIONAL_QA"]
        if gates.get("value") is not None:
            raise AssertionError("la compuerta de QA sobrevivió al retrabajo")

    check("retrabajo invalida las compuertas de QA", invalidate)

    def sync():
        buzon.update_state(root, buscador, t(buscador), "en_progreso", "Sincronizando el estado de esta prueba de canal.", "NXP-0101")
        expect_deny(
            lambda: buzon.update_state(
                root,
                analyst,
                t(analyst),
                "en_progreso",
                "No puedo colgarme de una tarea que no me asignaron.",
                "NXP-0106",
            )
        )
        board = buzon.board(root, google, t(google))
        blob = json.dumps(board)
        if "EVIDENCE" in blob or t(buscador) in blob:
            raise AssertionError("el tablero filtró un entregable o un secreto")
        if not any(item["agent_id"] == buscador and item["status"] == "en_progreso" for item in board["estados"]):
            raise AssertionError("el estado no es visible para otro agente autenticado")
        foreign = buzon.inbox(root, analyst, t(analyst))
        if any(item["from"] == apple for item in foreign["mensajes"]):
            raise AssertionError("la bandeja mezcló una revisión de otro módulo")

    check("tablero público sin cuerpos ni secretos", sync)

    def example_and_cli():
        envelope = json.loads((root / "canal" / "ejemplos" / "handoff.ejemplo.json").read_text(encoding="utf-8"))
        expect_deny(lambda: buzon.publish(root, buscador, t(buscador), envelope, simulate=False))
        env = os.environ.copy()
        env["PLATOON_ROOT"] = str(root)
        proc = subprocess.run(
            [
                sys.executable,
                str(REAL / "permisos" / "verificar.py"),
                "--json",
                "comprobar",
                "--agente",
                buscador,
                "--usar-secreto-local",
                "--ruta",
                "agentes/BUSCADOR_MZ1/entregables/ficha.json",
                "--operacion",
                "leer",
            ],
            cwd=REAL.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        if not payload["permitido"]:
            raise AssertionError(payload)
        if t(buscador) in proc.stdout:
            raise AssertionError("la CLI imprimió un secreto")

    check("ejemplo no publicable y CLI de permisos", example_and_cli)

    shutil.rmtree(tmp)
    print(f"comprobaciones fallidas: {FAILURES}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
