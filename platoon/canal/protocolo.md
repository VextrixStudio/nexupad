# Protocolo del canal

El cuerpo de una asignación conserva los campos de la sección 40. El cuerpo de un handoff conserva los de la sección 41. El sobre (`type`, `to`, `task_id`) es transporte: sin él el canal no sabe a quién entregar ni puede impedir que un especialista se cuele en la tarea de otro.

## Asignación (§40)

La crea `SUPER_MANAGER_MZ0` y solo hacia un gerente. El gerente la delega solo hacia su equipo, con `assignee`.

```json
{
  "type": "asignacion",
  "to": "MANAGER_MZ2_DESIGN",
  "task_id": "NXP-0001",
  "body": {
    "task_id": "NXP-0001",
    "objective": "Qué hay que lograr, en una frase que se pueda comprobar.",
    "manager": "MANAGER_MZ2_DESIGN",
    "priority": "high",
    "dependencies": [],
    "constraints": ["mobile-first", "limited liquid glass"],
    "deliverables": ["design specification"],
    "review_required": true
  }
}
```

`priority` acepta el valor corto del ejemplo de la especificación (`high`). No se inventó un enum.

Campos de enrutado, añadidos para poder aplicar las secciones 30 y 42 sin sustituir las de la 40:

| Campo | Uso |
| --- | --- |
| `assignee` | Obligatorio cuando un gerente delega. Comando no lo usa para saltarse al gerente. |
| `ui_change` | `none`, `tiny` o `major`. Si es `major` y el destino es frontend, hace falta diseño aprobado. |
| `design_task_id` | Tarea donde vive `DESIGN_APPROVED`, si no es la misma. |
| `excepcion_diseno` | Solo comando. Motivo de la sección 42 más evidencia. Un sello vacío no vale. |

Motivos de excepción admitidos, sin otros: `correccion de emergencia`, `ajuste visual minimo`, `correccion de accesibilidad`, `regresion evidente`, `autorizado explicitamente por SUPER_MANAGER`.

Volver a asignar una tarea existente a otro gerente es reasignación. Si sale de QA, las cinco compuertas de QA quedan invalidadas: la sección 43 pide probar otra vez.

## Handoff (§41)

Todos estos campos son obligatorios. `TASK` debe contener el `task_id`. `EVIDENCE` es una lista. No se acepta vacía ni «Looks good.».

```text
TASK
STATUS
WHAT WAS INVESTIGATED
WHAT WAS CHANGED
DECISIONS
EVIDENCE
FILES AFFECTED
DEPENDENCIES
RISKS
OPEN QUESTIONS
NEXT AGENT
```

`NEXT AGENT` puede nombrar al siguiente recomendado, incluso de otro módulo. El destinatario real del mensaje cruzado es comando, salvo las entregas internas que la especificación sí ordena:

- `BUSCADOR_MZ1` puede entregar a `ANALYST_MZ2`, `TREND_MZ3` y `SOURCE_VALIDATOR_MZ4`.
- `ANALYST_MZ2` puede entregar a `TREND_MZ3` y `SOURCE_VALIDATOR_MZ4`.
- `SOURCE_VALIDATOR_MZ4` devuelve la validación a `BUSCADOR_MZ1` y a `ANALYST_MZ2`.
- El resto de especialistas entrega a su gerente.

Nadie entrega una tarea en la que no está delegado.

## Revisión

Los cinco revisores de diseño responden solo a `MANAGER_MZ2_DESIGN`. No se escriben entre ellos. El veredicto, si se usa, es `observaciones`, `rechazo` o `sin_objecion`. No es un voto. `copied_interface: true` se rechaza.

QA no fija su compuerta con un mensaje. La fija con:

```bash
python3 platoon/canal/nexu_canal.py compuerta fijar \
  --agente FUNCTIONAL_QA_MZ --usar-secreto-local \
  --task NXP-0001 --compuerta FUNCTIONAL_QA --resultado PASS \
  --evidencia "Se abrió el flujo y se anotó el resultado observado." \
  --evidencia "Se probó el flujo vecino que la tarea nombra." \
  --evidencia "No había error de consola en esa ejecución."
```

Hacen falta tres evidencias para un PASS. Cada una describe una comprobación. El canal no comprueba que la comprobación haya ocurrido fuera del texto: no afirma un test que el agente no haya hecho. Sí impide el sello vacío y que otro agente firme la compuerta.

## Coordinación y conflicto

`coordinacion` solo entre `MANAGER_MZ3_FRONTEND` y `MANAGER_MZ4_BACKEND`, con copia a comando. Un handoff directo entre esos dos se rechaza.

`conflicto` sube: especialista a su gerente, gerente a comando. La respuesta de comando es `decision`, con decisión, motivo y alternativas.

## Cierre

Solo comando. Exige las cinco compuertas de QA en PASS, cada una fijada por su dueño. Si la tarea es UI mayor, también `DESIGN_APPROVED`, salvo excepción ya registrada. El mensaje de cierre dice que las compuertas están registradas. No dice que el producto haya sido probado si la evidencia no lo dice.
